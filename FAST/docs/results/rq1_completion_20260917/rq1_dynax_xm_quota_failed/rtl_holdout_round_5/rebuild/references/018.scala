// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  **一个 tile 的完整系统**：动态阈值选择 + 真实稀疏索引 + 带反压的取数
//  引擎 + 计算阵列，全部接在同一个状态机下。
//
//  ## 它补的是评审 P0-4 的后两条
//
//  `AttentionTileTop` 已经把控制搬进硬件（QK -> exp -> AV -> norm 的时序、
//  跨趟累加、完成拍数），但 K/V 仍然由外部直接喂进 `execute_cols`——没有
//  取数引擎，就测不到**存储停顿**；索引也仍然从外部端口给，用的是参照算法
//  挑的列，不是硬件自己挑的。
//
//  这里把缺的两段接上：
//
//      预测 -> 分档选择（BlockTierSelect，三档 {0, n2, n1}）
//           -> 调度器（sched_from_topk=true，用硬件自己挑的索引）
//           -> KeyFeeder（bank 冲突变成 req_ready 拉低，也就是**反压**）
//           -> 执行阵列
//
//  ## 为什么停顿必须由硬件数
//
//  `KeyFeeder` 自带 `busy_cycles` / `conflict_cycles` / `requests_served`
//  ——它自己的注释写着「放在硬件里而不是 testbench 里数：testbench 数的是
//  『它以为发生了什么』」。这里把它们透出来，和 FSM 自己的拍数放在一起，
//  于是「总延迟里有多少是等存储」第一次有了实测答案，而不是代价模型里
//  那个标定出来的 `gather_slowdown` 系数。
//
//  ## 范围
//
//  仍然是**单行**（query 装进阵列第 0 行）。执行阵列是脉动列广播
//  （`rows(i+1).regs_top := rows(i).regs_bottom`），第 r 行看到的列数据
//  延迟 r 拍；多行并发要按行错开发射，那是下一步。这里不假装做到了。

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import execute_unit.KeyFeeder

class AttentionTileSystem(
    val bits: Int,
    val point: Int,
    val tileQ: Int,
    val tileK: Int,
    val headDim: Int,
    val keptPerRow: Int,
    val peCountPerRow: Int,
    val psumBits: Int,
    val dividerStages: Int,
    /** 动态 X:M 的两档保留数。给了才启用分档，否则退化成固定 top-n。 */
    val keptHigh: Int = 0,
    val keptLow: Int = 0,
    /** 取数引擎的 bank 数。冲突 -> 反压 -> 停顿，全部由它决定。 */
    val bankCount: Int = 8,
    val hashBanks: Boolean = false,
) extends Module {
  private val fpType = FixedPoint(bits.W, point.BP)
  private val colBits = log2Ceil(tileK max 2)
  val passes: Int = (keptPerRow + peCountPerRow - 1) / peCountPerRow

  val io = IO(new Bundle {
    val start = Input(Bool())
    val busy = Output(Bool())
    val done = Output(Bool())

    // ---- 工作负载 --------------------------------------------------------
    val q_in = Input(Vec(headDim, fpType))
    /** 近似分数，**逐 key 串行喂入**。
      *
      * 这是 tile 的设计意图，不是绕开：`attention_tile.scala` 自己的注释写着
      * 「分数由外部串行喂入而不是直接接 predict.io.s_out：PrePEA 每拍只产出
      * 一列的分数，要攒够 tileK 列才能挑 top-n……直接接线会把两个阶段的时序
      * 耦死」。
      *
      * 预测阵列自身的排程（相位补偿、组内降序装 Q、逐 key 等 settle 拍）
      * **还没有进这个状态机**——那一段的时序很细（`cycleToggle` 每拍翻转，
      * 装载起点错一拍就「32 个 key 的分数全是 0」），单独做。
      * 现在由驱动方提供分数，`select` 之后的每一段都是硬件自己走的。 */
    val score_in = Input(Vec(tileQ, fpType))
    val score_valid = Input(Bool())
    /** 这一块的概率质量。同样由驱动方给——见 `select_mass` 的说明。 */
    val block_mass = Input(Vec(tileQ, fpType))
    /** 分档阈值。软件里 `sum_m = sum(block) * token_len / m`，缩放放在
      * 软件侧算阈值时做，硬件只比原始块和——省一个乘法器，而阈值本来就是
      * 标定出来的常数。 */
    val threshold_hi = Input(fpType)
    val threshold_lo = Input(fpType)

    // ---- K/V 装载：写进 feeder 的 bank ----------------------------------
    val kv_wr_en = Input(Bool())
    val kv_wr_col = Input(UInt(colBits.W))
    val kv_wr_data = Input(fpType)

    // ---- 结果 ------------------------------------------------------------
    val out = Output(Vec(headDim, fpType))
    val out_valid = Output(Bool())
    /** 硬件**自己**挑出来的列，以及这一块留了几个。和软件比对用。 */
    val chosen_idx = Output(Vec(keptPerRow, UInt(colBits.W)))
    val chosen_valid = Output(Vec(keptPerRow, Bool()))
    val chosen_keep = Output(UInt(log2Ceil(keptPerRow + 1).W))
    val block_skipped = Output(Bool())

    // ---- 性能：全部由硬件数 ----------------------------------------------
    val perf_clear = Input(Bool())
    val total_cycles = Output(UInt(32.W))
    /** 等取数引擎的拍数。**这是代价模型里 `gather_slowdown` 那个标定系数
      * 第一次有实测对照。** */
    val stall_cycles = Output(UInt(32.W))
    val feeder_busy_cycles = Output(UInt(32.W))
    val feeder_conflict_cycles = Output(UInt(32.W))
    val feeder_requests = Output(UInt(32.W))
    /** 当前状态和步进。**挂住的时候要能看见卡在哪** —— 上一版没有它，
      * 一次「20000 拍没完成」只能靠猜。 */
    val dbg_state = Output(UInt(4.W))
    val dbg_step = Output(UInt(8.W))
  })

  val tile = Module(new AttentionTile(
    bits, point, tileQ, tileK, headDim, keptPerRow, peCountPerRow,
    psumBits, dividerStages, keptHigh, keptLow))

  val feeder = Module(new KeyFeeder(
    bits = bits, point = point, regWidth = peCountPerRow,
    bankCount = bankCount, bankDepth = math.max(1, tileK / bankCount),
    hashBanks = hashBanks))


  // ---- 控制编码：抄 repe.scala 的 Enum，和 golden testbench 一致 --------
  private val kAccClear = 0.U(2.W)
  private val kAccIdle = 1.U(2.W)
  private val kAccAccumulate = 2.U(2.W)
  private val kAccMoveOut = 3.U(2.W)
  private val kExpCompute = 1.U(2.W)
  private val kExpIdle = 0.U(2.W)
  private val pIdle = 0.U(2.W)
  private val pCalc = 1.U(2.W)
  private val aIdle = 0.U(2.W)
  private val aClear = 1.U(2.W)
  private val aCalc = 2.U(2.W)

  private val normCycles = headDim + dividerStages + 4
  private val avCycles = headDim + 2

  // 相位。预测和选择是新加的两段——`AttentionTileTop` 里没有，因为那时
  // 索引是外部给的。
  val st = Enum(15)
  val sIdle = st(0); val sSelect = st(1); val sDrain = st(14); val sLoad = st(2)
  val sReq = st(3)
  val sClr0 = st(4); val sClr1 = st(5); val sQk = st(6); val sQkTail = st(7)
  val sExp0 = st(8); val sExp1 = st(9); val sAv = st(10); val sAvTail = st(11)
  val sNorm = st(12); val sDone = st(13)

  val state = RegInit(sIdle)
  val pass = RegInit(0.U(log2Ceil(passes max 2).W))
  val step = RegInit(0.U(log2Ceil((normCycles max tileK) + 2).W))
  val denominator = Reg(fpType)
  val numerators = Reg(Vec(avCycles, fpType))

  // ---- 锁存 TopK 的输出：**select_valid 是脉冲不是电平** ----------------
  //
  // golden testbench 的注释记着这件事：「每个 lane 在自己的 valid 脉冲那一拍
  // 采样。等流完再读会读到已被清零的寄存器——第一版就是这么错的，选出一堆
  // 重复的 31。」我在 sLoad 一拍里读全部 lane，脉冲早过去了，于是 8 个 lane
  // 一个都没捕到。
  //
  // 这同时说明 tile 的 `sched_from_topk` 直连路径在这个语义下**不可用**：
  // 它在 load 那一拍直接读 `selectors(row).io.idx`，而那时索引已经不稳定。
  // 所以这里锁存之后走 `sched_ext_*` 送进调度器——索引仍然是硬件自己挑的，
  // 只是加了任何真实设计都需要的那一级寄存器。
  val capturedIdx = Reg(Vec(keptPerRow, UInt(colBits.W)))
  val capturedValid = RegInit(VecInit(Seq.fill(keptPerRow)(false.B)))
  when(state === sIdle && io.start) {
    capturedValid := VecInit(Seq.fill(keptPerRow)(false.B))
  }
  for (k <- 0 until keptPerRow) {
    when(tile.io.select_valid(0)(k) && !capturedValid(k)) {
      capturedIdx(k) := tile.io.select_idx(0)(k)
      capturedValid(k) := true.B
    }
  }

  io.chosen_idx := capturedIdx
  io.chosen_valid := capturedValid

  // ---- 默认值 -----------------------------------------------------------
  tile.io.predict_q := VecInit(Seq.fill(tileQ)(0.S(4.W)))
  tile.io.predict_k := VecInit(Seq.fill(headDim)(0.S(4.W)))
  tile.io.predict_pes_state := pIdle
  tile.io.predict_array_state := aIdle
  tile.io.select_enable := false.B
  tile.io.select_in := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.select_mass := io.block_mass
  tile.io.select_threshold_hi := io.threshold_hi
  tile.io.select_threshold_lo := io.threshold_lo
  tile.io.sched_load := false.B
  tile.io.sched_load_row := 0.U
  // **用硬件自己挑的索引**，不是外部端口给的参照列。
  // 走 ext 口，但送的是**锁存下来的、硬件自己挑的**索引（见上）。
  tile.io.sched_from_topk := false.B
  tile.io.sched_ext_idx := capturedIdx
  tile.io.sched_ext_valid := capturedValid
  tile.io.sched_pass := pass
  tile.io.execute_clr := false.B
  tile.io.execute_acc_ctrl := kAccIdle
  tile.io.execute_exp_ctrl := kExpIdle
  tile.io.execute_q := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.execute_cols := feeder.io.out_cols
  tile.io.norm_valid := false.B
  tile.io.norm_numerator := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.norm_denominator := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))

  io.chosen_keep := tile.io.select_keep(0)
  io.block_skipped := tile.io.select_skipped(0)

  // ---- 取数引擎 ---------------------------------------------------------
  //
  // 请求这一趟要的列。`req_ready` 拉低就是反压——bank 冲突让引擎还在服务
  // 上一组，状态机必须等。**这正是代价模型里那个 gather_slowdown 系数
  // 描述的东西，现在它是被测出来的。**
  feeder.io.wr_en := io.kv_wr_en
  feeder.io.wr_col := io.kv_wr_col
  feeder.io.wr_data := io.kv_wr_data
  feeder.io.perf_clear := io.perf_clear
  feeder.io.req_valid := state === sReq
  feeder.io.req_cols := VecInit((0 until peCountPerRow).map { pe =>
    tile.io.gather_col(0)(pe)
  })
  feeder.io.req_active := VecInit((0 until peCountPerRow).map { pe =>
    tile.io.gather_active(0)(pe)
  })

  io.busy := state =/= sIdle && state =/= sDone
  io.done := state === sDone

  // ---- 性能计数 ---------------------------------------------------------
  val totalCycles = RegInit(0.U(32.W))
  val stallCycles = RegInit(0.U(32.W))
  when(io.perf_clear) { totalCycles := 0.U; stallCycles := 0.U }
    .elsewhen(io.busy) {
      totalCycles := totalCycles + 1.U
      // 在 sReq 里等 feeder 收下请求的每一拍都算停顿。
      when(state === sReq && !feeder.io.req_ready) {
        stallCycles := stallCycles + 1.U
      }
    }
  io.dbg_state := state
  io.dbg_step := step
  io.total_cycles := totalCycles
  io.stall_cycles := stallCycles
  io.feeder_busy_cycles := feeder.io.busy_cycles
  io.feeder_conflict_cycles := feeder.io.conflict_cycles
  io.feeder_requests := feeder.io.requests_served

  // ---- 状态机 -----------------------------------------------------------
  switch(state) {
    is(sIdle) {
      when(io.start) {
        state := sSelect; pass := 0.U; step := 0.U
        denominator := 0.F(bits.W, point.BP)
        for (i <- 0 until avCycles) { numerators(i) := 0.F(bits.W, point.BP) }
      }
    }
    is(sSelect) {
      // 分数**逐 key 串行**喂给 TopK 级联；分档器同时拿块质量判这一块留几个。
      // 驱动方每给一个有效分数就推进一步——`score_valid` 为假时停在这里，
      // 因为 TopK 的级联是按到达顺序比较的，喂空会把顺序打乱。
      tile.io.select_enable := io.score_valid
      tile.io.select_in := io.score_in
      when(io.score_valid) {
        when(step === (tileK - 1).U) { step := 0.U; state := sDrain }
          .otherwise { step := step + 1.U }
      }
    }
    is(sDrain) {
      // TopK 是 n-1 级级联，最后一个分数喂进去之后还要这么多拍才全部流出。
      // golden testbench 用的是 `kKept + 6`，这里照抄——时序自己发明一套的话，
      // 一次捕不到说不清是级数算错了还是脉冲错过了。
      when(step === (keptPerRow + 6 - 1).U) { step := 0.U; state := sLoad }
        .otherwise { step := step + 1.U }
    }
    is(sLoad) {
      tile.io.sched_load := true.B
      state := sReq
    }
    is(sReq) {
      // 整块被分档判为丢弃时直接跳过——取数、计算都不做。
      when(tile.io.select_skipped(0)) {
        state := sNorm; step := 0.U
      }.elsewhen(feeder.io.req_ready) {
        state := sClr0
      }
      // req_ready 为假就停在这里：这就是反压。
    }
    is(sClr0) { tile.io.execute_clr := true.B; state := sClr1 }
    is(sClr1) { tile.io.execute_acc_ctrl := kAccClear; step := 0.U; state := sQk }
    is(sQk) {
      tile.io.execute_q(0) := io.q_in(step)
      tile.io.execute_acc_ctrl := Mux(step === 0.U, kAccClear, kAccAccumulate)
      when(step === (headDim - 1).U) { step := 0.U; state := sQkTail }
        .otherwise { step := step + 1.U }
    }
    is(sQkTail) { tile.io.execute_acc_ctrl := kAccAccumulate; state := sExp0 }
    is(sExp0) {
      tile.io.execute_acc_ctrl := kAccIdle
      tile.io.execute_exp_ctrl := kExpCompute
      state := sExp1
    }
    is(sExp1) { tile.io.execute_exp_ctrl := kExpIdle; state := sAv; step := 0.U }
    is(sAv) {
      when(step === 0.U) { denominator := denominator + tile.io.execute_row_sum(0) }
      tile.io.execute_acc_ctrl := kAccMoveOut
      when(step === (avCycles - 1).U) { step := 0.U; state := sAvTail }
        .otherwise { step := step + 1.U }
    }
    is(sAvTail) { state := Mux(pass === (passes - 1).U, sNorm, sReq) }
    is(sNorm) {
      val feeding = step < headDim.U
      tile.io.norm_valid := feeding
      val at = step + 2.U
      tile.io.norm_numerator(0) := Mux(
        feeding && at < avCycles.U, numerators(Mux(at < avCycles.U, at, 0.U)),
        0.F(bits.W, point.BP))
      tile.io.norm_denominator(0) := denominator
      when(step === (normCycles - 1).U) { state := sDone }
        .otherwise { step := step + 1.U }
    }
    is(sDone) { when(!io.start) { state := sIdle } }
  }

  // 趟推进：AV 收尾之后如果还有趟就回到 sReq 重新取数。
  when(state === sAvTail && pass =/= (passes - 1).U) { pass := pass + 1.U }

  // 跨趟累加：读的是 move_out 之后那一拍的 row_sum（见
  // `attention_tile_top.scala` 里对同一个错位的说明）。
  private val avActive = RegNext(state === sAv, false.B)
  private val avIndex = RegNext(step, 0.U)
  when(avActive && avIndex < avCycles.U) {
    numerators(avIndex) := numerators(avIndex) + tile.io.execute_row_sum(0)
  }

  val outIndex = RegInit(0.U(log2Ceil(headDim max 2).W))
  val outBuffer = Reg(Vec(headDim, fpType))
  when(state === sIdle && io.start) { outIndex := 0.U }
  when(tile.io.out_valid && outIndex < headDim.U) {
    outBuffer(outIndex) := tile.io.out(0)
    outIndex := outIndex + 1.U
  }
  io.out := outBuffer
  io.out_valid := RegNext(tile.io.out_valid, false.B)
}
