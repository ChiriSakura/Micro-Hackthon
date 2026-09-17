// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  按稀疏索引把 K 列喂给 RePEArray 的取数引擎。
//
//  ## 它补的是一个结构性缺口，不是一个优化
//
//  追一遍带宽就能看到：
//
//    `repe_row.scala:62`   reg_cols := io.regs_top     每拍无条件更新
//    `repe_array.scala:48` rows(0).regs_top := io.regs_top
//
//  所以阵列**每个周期**要 regWidth 个新的 K 标量。DynaX-S 是 8 x 16 = 128 位/拍，
//  DynaX-L 是 16 x 16 = 256 位/拍。
//
//  而 `sram.scala` 的 `SRAM` 是**单地址端口**：一个 `addr` 输入，`Mux1H` 从
//  bankCount 个 bank 里选一个的输出。它每拍只给 bankWidth = 64 位。
//
//  差 2 到 4 倍，而且 `RePEArray` 根本没有反压输入——它没法被告知「这拍没数据」。
//  开源发布里这条路没有接通，所以这个缺口不会以任何仿真失败的形式暴露出来。
//
//  在模型侧，同一个缺口表现为 `fast/agents/codesign.py` 的
//
//      cycles = sparse_macs / (lanes * utilisation)
//
//  ——**一项和访存有关的都没有**，等于假设带宽无限。于是 `sram_bytes`、
//  `double_buffer` 这些维度对周期数的影响是零。
//
//  ## 关键的结构改动：bank 要能独立寻址
//
//  上游把 bank 做成「一个地址、选一个输出」，那只是个分块的单口存储，
//  带宽和不分块完全一样。要一拍拿到 regWidth 个**任意**列，bank 必须各自
//  有地址。这个模块因此不复用 `SRAM`（那份是上游镜像，要保持可对照），
//  而是自己例化 bankCount 个独立的 `SyncReadMem`。
//
//  ## 于是 bank 冲突成为可测量的东西
//
//  一拍要 regWidth 个列，映射 `bank = col % bankCount`。落在同一个 bank 的
//  两个请求必须分两拍。冲突率**取决于索引的分布**：
//
//    * xm 按块保留，索引聚簇
//    * topk 全局取大，索引分散
//
//  同样的保留比例，这两种分布撞 bank 的方式完全不同。**这是模型猜不出来、
//  只能用真实索引流测的量**，也正是协同优化器该看见的 bank 数取舍。
//
//  冲突的代价是实打实的：serve 一组要几拍，就等于阵列停几拍。

package execute_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

class KeyFeeder(
    val bits: Int,
    val point: Int,
    val regWidth: Int,     // 阵列每拍要几个 K 标量
    val bankCount: Int,    // 独立寻址的 bank 数
    val bankDepth: Int,    // 每个 bank 多少个条目
    // bank 选择用低位取模，还是先做一次 XOR 折叠。
    //
    // 取模（false）会和**索引的步长混叠**：实测 xm 在一个 64 宽块里保留的列
    // 是带空洞的簇（如 33,34,35,36,38,39,40），空洞让它不再是完美步长，
    // 而 sink 列 0 又和 36、40 同余 4——三个请求全挤在 bank 0。
    //
    // XOR 折叠（true）把高位掺进 bank 号，专门用来打散这种步长结构。
    val hashBanks: Boolean = false,
) extends Module {
  require(regWidth > 0 && bankCount > 0 && bankDepth > 0)
  require(isPow2(bankCount), s"bankCount=$bankCount 必须是 2 的幂：" +
    "bank 选择要用取模，非 2 的幂会引入一个除法器，" +
    "那个除法器的关键路径会盖过冲突本身的代价")

  val fpType = FixedPoint(bits.W, point.BP)
  private val bankIdxBits = log2Ceil(bankCount max 2)
  private val bankOffBits = log2Ceil(bankDepth max 2)
  val colBits: Int = bankIdxBits + bankOffBits

  val io = IO(new Bundle {
    // ---- 请求：一组 regWidth 个列索引 -----------------------------------
    val req_valid = Input(Bool())
    val req_cols = Input(Vec(regWidth, UInt(colBits.W)))
    // 该槽这一组里是否真的要取。稀疏下最后一组可能不满。
    val req_active = Input(Vec(regWidth, Bool()))
    // 上一组还没服务完就不能收下一组——这就是冲突变成停顿的地方。
    val req_ready = Output(Bool())

    // ---- 写口：装载 K -----------------------------------------------------
    val wr_en = Input(Bool())
    val wr_col = Input(UInt(colBits.W))
    val wr_data = Input(fpType)

    // ---- 输出：一整组齐了才有效 -------------------------------------------
    val out_valid = Output(Bool())
    val out_cols = Output(Vec(regWidth, fpType))

    // ---- 性能计数器 -------------------------------------------------------
    //
    // 放在硬件里而不是 testbench 里数：testbench 数的是「它以为发生了什么」。
    val perf_clear = Input(Bool())
    val groups_served = Output(UInt(32.W))   // 服务了多少组
    val busy_cycles = Output(UInt(32.W))     // 为此花了多少拍
    val conflict_cycles = Output(UInt(32.W)) // 其中多少拍是纯粹的冲突代价
    // 一共服务了多少个**有效**请求。按组平均会把「索引散不散得开」和
    // 「组填不填得满」混在一起：只有 1 个请求的组必然零冲突，而 topk 的
    // 组大多是空的。要比较方法，得按列归一而不是按组。
    val requests_served = Output(UInt(32.W))
  })

  // bankCount 个**各自有地址**的存储。这是和上游 SRAM 的关键差别。
  private val banks = Seq.fill(bankCount)(SyncReadMem(bankDepth, fpType))

  private def bankOf(col: UInt): UInt =
    if (bankCount == 1) 0.U
    else if (!hashBanks) col(bankIdxBits - 1, 0)
    // 低位异或高位：一次异或就能打断固定步长，代价是几个 XOR 门。
    // 注意偏移量仍然用原始的高位——两个不同的列不会映到同一个
    // (bank, offset)，因为 bank 号在同一个 offset 内是单射的。
    else (col(bankIdxBits - 1, 0) ^ col(colBits - 1, bankIdxBits)(bankIdxBits - 1, 0))
  private def offsetOf(col: UInt): UInt =
    if (bankOffBits == 0) 0.U else col(colBits - 1, bankIdxBits)

  // ---- 请求寄存 ------------------------------------------------------------
  private val pending = RegInit(0.U(regWidth.W))   // 还没取到的槽
  private val colsReg = Reg(Vec(regWidth, UInt(colBits.W)))
  private val dataReg = Reg(Vec(regWidth, fpType))
  private val active = RegInit(false.B)

  private val accepting = !active && io.req_valid
  io.req_ready := !active

  // 这一拍每个 bank 挑哪个待取的槽。
  //
  // 「每个 bank 取还没取到的、下标最小的那个槽」——用 PriorityEncoder 而不是
  // 更聪明的仲裁：仲裁策略会改变冲突的**代价**，但改变不了冲突的**存在**，
  // 而这里要测的是后者。换策略要重新标定，所以策略必须简单到能写进注释里。
  private val nextPending = Wire(UInt(regWidth.W))
  private val servedMask = Wire(Vec(regWidth, Bool()))
  for (i <- 0 until regWidth) servedMask(i) := false.B

  for (b <- 0 until bankCount) {
    // 这一拍落在 bank b 上、且还没取到的槽
    val wants = VecInit((0 until regWidth).map { i =>
      pending(i) && bankOf(colsReg(i)) === b.U
    })
    val hasWant = wants.asUInt.orR
    val pick = PriorityEncoder(wants.asUInt)
    val readAddr = offsetOf(colsReg(pick))

    // 写口优先：装载期间不服务请求，两者不会同拍。
    val doWrite = io.wr_en && bankOf(io.wr_col) === b.U
    when(doWrite) {
      banks(b).write(offsetOf(io.wr_col), io.wr_data)
    }
    val readData = banks(b).read(readAddr, active && hasWant && !doWrite)

    // SyncReadMem 是一拍延迟读，所以「这拍选中的槽」要延一拍再写回。
    val pickReg = RegNext(pick)
    val hitReg = RegNext(active && hasWant && !doWrite, false.B)
    when(hitReg) {
      dataReg(pickReg) := readData
      servedMask(pickReg) := true.B
    }
  }

  nextPending := pending & (~servedMask.asUInt).asUInt
  private val done = active && nextPending === 0.U

  when(io.wr_en) {
    // 装载期间不接请求，也不推进状态。
  }.elsewhen(accepting) {
    active := true.B
    colsReg := io.req_cols
    // 不需要取的槽直接算已取到，否则它们会把这组永远挂住。
    pending := io.req_active.asUInt
    for (i <- 0 until regWidth) {
      when(!io.req_active(i)) { dataReg(i) := FixedPoint(0, bits.W, point.BP) }
    }
  }.elsewhen(active) {
    pending := nextPending
    when(nextPending === 0.U) { active := false.B }
  }

  // `done` 和最后一个 dataReg 写入是**同一拍**，而 dataReg 是寄存器——
  // 新值下一拍才看得到。直接把 done 当 out_valid，取到的是上一组的数据。
  //
  // 这不是「差一点」：整组数据晚一拍，第 N 组读到第 N-1 组的值。实测第 1 组
  // 槽 4 要列 45，取到的是列 36 的值——36 正是第 0 组槽 4 的列。而周期数和
  // 解析预测精确一致，所以**只看冲突计数完全看不出这个 bug**。
  //
  // testbench 的判据 1（取回的必须等于写进去的）就是为这种情况存在的。
  private val outValid = RegInit(false.B)
  outValid := done
  io.out_valid := outValid
  io.out_cols := dataReg

  // ---- 计数器 --------------------------------------------------------------
  //
  // `conflict_cycles` 的定义：服务这一组多花的拍数。
  //
  // 没有冲突时，regWidth 个请求分散在 bankCount 个 bank 上，一拍全部发出，
  // 加上 SyncReadMem 的一拍延迟——所以下界是**每组 2 拍**。超过 2 拍的部分
  // 才是冲突代价。用绝对拍数而不是比值来记，因为「无冲突下界」本身随
  // regWidth 和 bankCount 变，记比值会把两个变量搅在一起。
  private val kIdealCycles = 2
  private val groups = RegInit(0.U(32.W))
  private val busy = RegInit(0.U(32.W))
  private val conflict = RegInit(0.U(32.W))
  private val groupCycles = RegInit(0.U(16.W))
  private val requests = RegInit(0.U(32.W))

  when(io.perf_clear) {
    groups := 0.U; busy := 0.U; conflict := 0.U; groupCycles := 0.U; requests := 0.U
  }.otherwise {
    when(accepting) { requests := requests + PopCount(io.req_active) }
    when(active) {
      busy := busy + 1.U
      groupCycles := groupCycles + 1.U
    }
    when(done) {
      groups := groups + 1.U
      val spent = groupCycles + 1.U
      when(spent > kIdealCycles.U) { conflict := conflict + (spent - kIdealCycles.U) }
      groupCycles := 0.U
    }
  }
  io.groups_served := groups
  io.busy_cycles := busy
  io.conflict_cycles := conflict
  io.requests_served := requests
}
