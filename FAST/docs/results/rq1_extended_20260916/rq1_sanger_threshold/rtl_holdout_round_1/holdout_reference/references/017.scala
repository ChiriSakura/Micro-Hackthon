

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

/** 把 `AttentionTile` 的控制收进硬件，并如实数出完成一个 tile 要多少拍。
  *
  * ## 为什么需要它
  *
  * 评审 P0-4：`AttentionTile` 的控制和 K/V gather 都在**外部**。
  * `tb_attention_tile.cpp` 逐 query 复位、把每条 query 都送进阵列第 0 行，
  * 跨趟的分子分母**在 testbench 里相加**——它自己的注释就写着「这正是硬件
  * 缺的那层控制」。
  *
  * 后果是那个测试能证明**单行的数值通路**对不对，但证明不了：
  *
  *   - 完整执行时间（趟与趟之间的开销全在 C++ 里）
  *   - 多行并行吞吐（只驱动了第 0 行）
  *   - 存储停顿（没有取数引擎，K/V 是直接喂进去的）
  *
  * 这个模块解决第一条：**时序由硬件的状态机决定**，`total_cycles` 是它自己
  * 数出来的。第二、三条要接 `KeyFeeder` 和多行驱动，分步做。
  *
  * ## 状态机复现的是 testbench 那套时序
  *
  * 这不是重新设计，是**把已经验证过的时序搬进硬件**。golden 测试仍然是
  * 唯一的正确性锚点：同样的输入，这个模块给出的结果必须和它逐字节一致。
  * 时序自己发明一套的话，一次数值不符说不清是控制错了还是数据通路错了。
  *
  *   LOAD    装索引（每拍一行）
  *   CLR     execute_clr，然后 acc_ctrl=CLEAR
  *   QK      headDim 拍，逐维送 Q 和 K 列；第 0 拍 CLEAR，之后 ACCUM
  *   QK_TAIL 一拍 ACCUM，把最后一维的乘积推进累加器
  *   EXP     一拍 exp_ctrl=COMPUTE，一拍 IDLE，然后读 row_sum 累进分母
  *   AV      headDim+2 拍，move_out 逐拍推出分子；跨趟累加**在这里**
  *   NORM    headDim+dividerStages+4 拍，喂分子分母，收 out_valid
  *
  * 趟与趟之间不复位——跨趟累加器是这个模块存在的理由之一。
  */
class AttentionTileTop(
    val bits: Int,
    val point: Int,
    val tileQ: Int,
    val tileK: Int,
    val headDim: Int,
    val keptPerRow: Int,
    val peCountPerRow: Int,
    val psumBits: Int,
    val dividerStages: Int,
) extends Module {
  private val fpType = FixedPoint(bits.W, point.BP)
  private val colBits = log2Ceil(tileK max 2)
  /** 一趟只能算 peCountPerRow 个保留列，所以要跑这么多趟。 */
  val passes: Int = (keptPerRow + peCountPerRow - 1) / peCountPerRow

  val io = IO(new Bundle {
    // ---- 启动与完成 ------------------------------------------------------
    val start = Input(Bool())
    val busy = Output(Bool())
    val done = Output(Bool())

    // ---- 这一行的输入 ----------------------------------------------------
    //
    // 第一步只驱动一行（和 golden 测试同一个范围），这样"结果必须逐字节
    // 一致"这个锚点是成立的。多行并发是第三步。
    val row = Input(UInt(log2Ceil(tileQ max 2).W))
    val q_in = Input(Vec(headDim, fpType))
    val ext_idx = Input(Vec(keptPerRow, UInt(colBits.W)))
    val ext_valid = Input(Vec(keptPerRow, Bool()))

    // ---- K/V：按 (列, 维) 提供。第一步仍由外部喂，但**时序由硬件决定** --
    //
    // 状态机通过 `k_col_req` / `k_dim_req` 说出它这一拍要哪个元素，外部
    // 组合地把值放上来。接 KeyFeeder 之后这两根线改成接 feeder 的输出，
    // 那时反压才有意义（第二步）。
    val k_col_req = Output(Vec(peCountPerRow, UInt(colBits.W)))
    val k_dim_req = Output(UInt(log2Ceil(headDim max 2).W))
    val k_slot_active = Output(Vec(peCountPerRow, Bool()))
    val k_data = Input(Vec(peCountPerRow, fpType))
    val v_data = Input(Vec(peCountPerRow, fpType))
    val want_v = Output(Bool())

    // ---- 结果 ------------------------------------------------------------
    val out = Output(Vec(headDim, fpType))
    val out_valid = Output(Bool())

    // ---- 性能：**硬件自己数的** ------------------------------------------
    //
    // testbench 数的是「它以为发生了什么」。放在这里是因为跨趟开销、状态
    // 转换的空拍都只有硬件看得见。
    val perf_clear = Input(Bool())
    val total_cycles = Output(UInt(32.W))
    val qk_cycles = Output(UInt(32.W))
    val av_cycles = Output(UInt(32.W))
    val norm_cycles = Output(UInt(32.W))
    val overhead_cycles = Output(UInt(32.W))
  })

  val tile = Module(new AttentionTile(
    bits, point, tileQ, tileK, headDim, keptPerRow, peCountPerRow,
    psumBits, dividerStages))

  // ---- 常量：和 testbench 里的编码一致 ------------------------------------
  // **编码取自 `repe.scala` 的 Enum，和 golden testbench 一致。**
  // 我第一次写反了 Clear 和 Idle（写成 Clear=1/Idle=0），那会让累加器在该
  // 清零的那一拍空转——结果仍然是数字，只是错的。抄验证过的那份，不要凭
  // 印象写。
  private val kAccClear = 0.U(2.W)
  private val kAccIdle = 1.U(2.W)
  private val kAccAccumulate = 2.U(2.W)
  private val kAccMoveOut = 3.U(2.W)
  private val kExpCompute = 1.U(2.W)
  private val kExpIdle = 0.U(2.W)

  private val normCycles = headDim + dividerStages + 4
  private val avCycles = headDim + 2

  // Scala 2 的 `val a :: b :: Nil = ...` 模式必须写在一行里。
  val states = Enum(13)
  val sIdle = states(0); val sLoad = states(1); val sClr0 = states(2)
  val sClr1 = states(3); val sQk = states(4); val sQkTail = states(5)
  val sExp0 = states(6); val sExp1 = states(7); val sAv = states(8)
  val sAvTail = states(9)
  val sNextPass = states(10); val sNorm = states(11); val sDone = states(12)
  val state = RegInit(sIdle)
  val pass = RegInit(0.U(log2Ceil(passes max 2).W))
  val step = RegInit(0.U(log2Ceil((normCycles max headDim) + 2).W))

  // 跨趟累加器——**这是硬件原来缺的那层**，testbench 在 C++ 里做的就是它。
  val denominator = Reg(fpType)
  val numerators = Reg(Vec(avCycles, fpType))

  // ---- 默认值 -------------------------------------------------------------
  tile.io.predict_q := VecInit(Seq.fill(tileQ)(0.S(4.W)))
  tile.io.predict_k := VecInit(Seq.fill(headDim)(0.S(4.W)))
  tile.io.predict_pes_state := 0.U
  tile.io.predict_array_state := 0.U
  tile.io.select_enable := false.B
  // 分档阈值：这一层用外部索引（sched_from_topk=false），分档器不参与，
  // 但输入仍要接——悬空的 Input 在 Chisel 里是编译错，不是警告。
  tile.io.select_mass := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.select_threshold_hi := 0.F(bits.W, point.BP)
  tile.io.select_threshold_lo := 0.F(bits.W, point.BP)
  tile.io.select_in := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.sched_load := false.B
  tile.io.sched_load_row := io.row
  tile.io.sched_from_topk := false.B
  tile.io.sched_ext_idx := io.ext_idx
  tile.io.sched_ext_valid := io.ext_valid
  tile.io.sched_pass := pass
  tile.io.execute_clr := false.B
  tile.io.execute_acc_ctrl := kAccIdle
  tile.io.execute_exp_ctrl := kExpIdle
  tile.io.execute_q := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.execute_cols := VecInit(Seq.fill(peCountPerRow)(0.F(bits.W, point.BP)))
  tile.io.norm_valid := false.B
  tile.io.norm_numerator := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))
  tile.io.norm_denominator := VecInit(Seq.fill(tileQ)(0.F(bits.W, point.BP)))

  // 这一拍要哪些列：第 pass 趟的第 pe 个槽。越界的槽不取。
  for (pe <- 0 until peCountPerRow) {
    val slot = pass * peCountPerRow.U + pe.U
    io.k_col_req(pe) := Mux(slot < keptPerRow.U,
      io.ext_idx(Mux(slot < keptPerRow.U, slot, 0.U)), 0.U)
    io.k_slot_active(pe) := slot < keptPerRow.U && io.ext_valid(
      Mux(slot < keptPerRow.U, slot, 0.U))
  }
  // AV 阶段最后两拍重复最后一维（和 testbench 的 `index` 取法一致）。
  io.k_dim_req := Mux(state === sAv,
    Mux(step < headDim.U, step, (headDim - 1).U), step)
  io.want_v := state === sAv

  io.busy := state =/= sIdle && state =/= sDone
  io.done := state === sDone
  io.out_valid := RegNext(tile.io.out_valid, false.B)

  // ---- 性能计数 -----------------------------------------------------------
  val totalCycles = RegInit(0.U(32.W))
  val qkCycles = RegInit(0.U(32.W))
  val avCyclesCount = RegInit(0.U(32.W))
  val normCyclesCount = RegInit(0.U(32.W))
  when(io.perf_clear) {
    totalCycles := 0.U; qkCycles := 0.U; avCyclesCount := 0.U; normCyclesCount := 0.U
  }.elsewhen(io.busy) {
    totalCycles := totalCycles + 1.U
    when(state === sQk || state === sQkTail) { qkCycles := qkCycles + 1.U }
    when(state === sAv || state === sAvTail) { avCyclesCount := avCyclesCount + 1.U }
    when(state === sNorm) { normCyclesCount := normCyclesCount + 1.U }
  }
  io.total_cycles := totalCycles
  io.qk_cycles := qkCycles
  io.av_cycles := avCyclesCount
  io.norm_cycles := normCyclesCount
  // 开销 = 总拍数减去三个干活的阶段。**这个数原来没人看得见**：它散在
  // testbench 的 C++ 循环里，而真实芯片上它是要付的。
  io.overhead_cycles := totalCycles - qkCycles - avCyclesCount - normCyclesCount

  // ---- 状态机 -------------------------------------------------------------
  switch(state) {
    is(sIdle) {
      when(io.start) {
        state := sLoad; pass := 0.U; step := 0.U
        denominator := 0.F(bits.W, point.BP)
        for (i <- 0 until avCycles) { numerators(i) := 0.F(bits.W, point.BP) }
      }
    }
    is(sLoad) {
      tile.io.sched_load := true.B
      state := sClr0
    }
    is(sClr0) {
      tile.io.execute_clr := true.B
      state := sClr1
    }
    is(sClr1) {
      tile.io.execute_acc_ctrl := kAccClear
      step := 0.U
      state := sQk
    }
    is(sQk) {
      tile.io.execute_q(io.row) := io.q_in(step)
      tile.io.execute_cols := io.k_data
      // 第 0 拍 CLEAR，之后 ACCUM——和 testbench 一致。
      tile.io.execute_acc_ctrl := Mux(step === 0.U, kAccClear, kAccAccumulate)
      when(step === (headDim - 1).U) { step := 0.U; state := sQkTail }
        .otherwise { step := step + 1.U }
    }
    is(sQkTail) {
      tile.io.execute_acc_ctrl := kAccAccumulate
      state := sExp0
    }
    is(sExp0) {
      tile.io.execute_acc_ctrl := kAccIdle
      tile.io.execute_exp_ctrl := kExpCompute
      state := sExp1
    }
    is(sExp1) {
      tile.io.execute_exp_ctrl := kExpIdle
      state := sAv
      step := 0.U
    }
    is(sAv) {
      // 分母在**进入 AV 的这一拍**读：row_sum 此时呈现的还是 exp 的和，
      // 第一次 move_out 的效果要到下一拍才出现。
      when(step === 0.U) { denominator := denominator + tile.io.execute_row_sum(io.row) }
      tile.io.execute_cols := io.v_data
      tile.io.execute_acc_ctrl := kAccMoveOut
      when(step === (avCycles - 1).U) {
        step := 0.U
        state := sAvTail
      }.otherwise { step := step + 1.U }
    }
    is(sAvTail) {
      // 多走一拍，把最后一次 move_out 推出来的值收掉——否则分子少最后一项。
      state := sNextPass
    }
    is(sNextPass) {
      when(pass === (passes - 1).U) { state := sNorm; step := 0.U }
        .otherwise { pass := pass + 1.U; state := sClr0 }
    }
    is(sNorm) {
      val feeding = step < headDim.U
      tile.io.norm_valid := feeding
      // 偏移 2：move_out 推出的是上一拍的 acc，row_sum 自己又是寄存器。
      val at = step + 2.U
      tile.io.norm_numerator(io.row) := Mux(
        feeding && at < avCycles.U, numerators(Mux(at < avCycles.U, at, 0.U)),
        0.F(bits.W, point.BP))
      tile.io.norm_denominator(io.row) := denominator
      when(step === (normCycles - 1).U) { state := sDone }
        .otherwise { step := step + 1.U }
    }
    is(sDone) {
      when(!io.start) { state := sIdle }
    }
  }

  // ---- 跨趟累加：**读的是 move_out 之后那一拍的 row_sum** ---------------
  //
  // golden testbench 里 `denominator` 和 `numerators[0]` 来自**不同的拍**：
  // 前者在 AV 循环之前读，后者在第一次 move_out 的 `tick()` **之后**读。
  // 我原来在 sAv 第 0 拍把同一个 row_sum 同时给了两者，于是整个分子向量
  // 错位一位——输出表现为 硬件[d+1] == 参照[d]，而且有几维完全相等
  // （数值通路没错，只是取错了拍）。
  private val avActive = RegNext(state === sAv, false.B)
  private val avIndex = RegNext(step, 0.U)
  when(avActive && avIndex < avCycles.U) {
    numerators(avIndex) := numerators(avIndex) + tile.io.execute_row_sum(io.row)
  }

  // 收结果：out_valid 拉高的每一拍收一个维度。
  val outIndex = RegInit(0.U(log2Ceil(headDim max 2).W))
  val outBuffer = Reg(Vec(headDim, fpType))
  when(state === sIdle && io.start) { outIndex := 0.U }
  // **在时钟沿之后采样，和 golden testbench 一致。**
  //
  // 它是 `tick()` 然后才读 `out_valid` 和 `out`；组合地在沿之前采样会
  // 早一拍，整条输出向量错位一位。实测就是这个：硬件[d+1] == 参照[d]，
  // 有几维完全相等——数值通路和跨趟累加都对，只有采样时刻差一拍。
  when(tile.io.out_valid && outIndex < headDim.U) {
    outBuffer(outIndex) := tile.io.out(io.row)
    outIndex := outIndex + 1.U
  }
  io.out := outBuffer
}
