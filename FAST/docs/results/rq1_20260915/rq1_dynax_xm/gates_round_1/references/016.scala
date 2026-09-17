// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  一个 attention tile 的完整数据通路。DynaX 开源里没有顶层——PrePEArray、
//  TopK、RePEArray、PSumSoftmax 全是互不相识的叶子模块（实例化次数都是 0）。
//  这个文件把它们连起来，让「模型的一部分注意力真的在这个加速器上跑」
//  成为一件可以验证的事。
//
//  ## 数据通路
//
//      Q(4bit), K(4bit) ─► PrePEArray_1_2 ─► s_out（近似分数）
//                                              │
//                                              ▼
//                                            TopK ─► 每行 top-n 的块内索引
//                                              │
//                                              ▼
//                                       IndexScheduler ─► gather 地址 + sel_cols
//                                              │
//      K(16bit), V(16bit) ──── gather ─────────┤
//                                              ▼
//                                          RePEArray ─► 精确分数 → exp → AV
//                                              │
//                                              ▼
//                                       FixedPointDivPipelined ─► 归一化输出
//
//  两个单元的分工是 DynaX 的核心思想：**PrePEA 用低精度算近似分数只为了
//  挑出哪些位置重要，RePEA 只对挑中的位置算精确值**。所以 PrePEA 的
//  4-bit 误差不进入最终结果，它只影响「挑得准不准」。
//
//  ## 控制交给外部
//
//  各阶段的控制序列（`pes_state`、`array_state`、`acc_ctrl`、`exp_ctrl`、
//  `enable`）由外部驱动，没有内建 FSM。这是刻意的：
//
//  这些序列是我为写 testbench 从数据通路反推出来的，并且逐周期验证过
//  （见 golden/execute_unit.py 的 RePEModel 和 golden/predict_unit.py 的
//  PrePEArrayModel）。把它们固化成 FSM 是下一步，但那会**同时**引入
//  「数据通路对不对」和「FSM 对不对」两个变量。先让外部驱动，把数据通路
//  对着 PyTorch 验证过，再谈 FSM——否则出了错分不清是谁的问题。
//
//  ## 存储侧也在外部
//
//  `gather_col` 发出地址，K/V 的实际取数由外部完成。真实芯片里这是
//  N-index buffer 加 SRAM 的活；这里由 testbench 承担，所以这个顶层
//  验证的是**计算通路**，不含访存。

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import execute_unit.RePEArray
import predict_unit.{BlockTierSelect, FixedPointDivPipelined, IndexScheduler, PrePEArray_1_2, TopK}

class AttentionTile(
    val bits: Int,          // 精确数据通路的定点宽度
    val point: Int,
    val tileQ: Int,         // query 行数
    val tileK: Int,         // 一个块里的 key 数，也是 TopK 的 m
    val headDim: Int,       // PrePEA 的 width；1:2 剪枝后每行 headDim/2 个 PE
    val keptPerRow: Int,    // TopK 的 n
    val peCountPerRow: Int, // RePEA 每行的 PE 数
    val psumBits: Int,      // PrePEA 内部部分和宽度
    val dividerStages: Int, // softmax 除法器的流水级数
    /** 动态 X:M 的高档保留数（软件的 n1）。 */
    val keptHigh: Int = 0,
    /** 动态 X:M 的中档保留数（软件的 n2）。 */
    val keptLow: Int = 0,
) extends Module {
  /** 分档是否启用。两个都不给时退化成固定 top-n，和原来完全一致——既有的
    * golden 测试因此不受影响。 */
  private val tiered = keptHigh > 0 && keptLow > 0
  private val fpType = FixedPoint(bits.W, point.BP)
  private val colBits = log2Ceil(tileK max 2)

  val predict = Module(new PrePEArray_1_2(
    bits = bits, point = point, append = 0,
    internalBits = psumBits, width = headDim, height = tileQ,
  ))
  // 每个 query 行一个 TopK：它们要并行地在各自的分数序列上挑 top-n。
  val selectors = Seq.fill(tileQ)(Module(new TopK(m = tileK, n = keptPerRow,
                                                 bits = bits, point = point)))
  val scheduler = Module(new IndexScheduler(
    numRows = tileQ, keptPerRow = keptPerRow,
    peCountPerRow = peCountPerRow, blockM = tileK,
  ))
  // regWidth 取 peCountPerRow：gather 之后是恒等映射，每个 PE 取自己那一个。
  val execute = Module(new RePEArray(
    peCountPerRow = peCountPerRow, bits = bits, point = point,
    regWidth = peCountPerRow, numRows = tileQ,
    colSelectBits = scheduler.colSelectBits,
  ))
  val normalisers = Seq.fill(tileQ)(
    Module(new FixedPointDivPipelined(bits, point, dividerStages))
  )

  val io = IO(new Bundle {
    // ---- 预测阶段：低精度 Q/K ------------------------------------------
    // ★ 预测通路改为有符号之后，顶层端口跟着改。低位宽有符号量化和
    // DynaX 软件的 calc_max_quant_value(4) = ±7 对齐。
    val predict_q = Input(Vec(tileQ, SInt(4.W)))
    val predict_k = Input(Vec(headDim, SInt(4.W)))
    val predict_pes_state = Input(UInt(2.W))
    val predict_array_state = Input(UInt(2.W))
    val predict_score = Output(Vec(tileQ, fpType))

    // ---- 选择阶段：把分数串行喂给 TopK ---------------------------------
    val select_enable = Input(Bool())
    val select_in = Input(Vec(tileQ, fpType))
    val select_idx = Output(Vec(tileQ, Vec(keptPerRow, UInt(colBits.W))))
    val select_valid = Output(Vec(tileQ, Vec(keptPerRow, Bool())))
    // ---- 动态阈值分档 ---------------------------------------------------
    //
    // 硬件原来只有固定 top-n：`TopK(m, n)` 永远留 n 个。而软件侧的
    // `gen_sparsity_mask_xm` 是三档的（质量 > hi 留 n1、< lo 留 0、
    // 其余留 n2）。两边不一致，而 tile 抓取的参照用的也是固定 top-n
    // ——**两边一致地错**，形状匹配看不出来。
    val select_mass = Input(Vec(tileQ, fpType))
    val select_threshold_hi = Input(fpType)
    val select_threshold_lo = Input(fpType)
    val select_keep = Output(Vec(tileQ, UInt(log2Ceil(keptPerRow + 1).W)))
    val select_skipped = Output(Vec(tileQ, Bool()))

    // ---- 调度：把索引装进 scheduler，并逐趟取出 gather 地址 -------------
    val sched_load = Input(Bool())
    val sched_load_row = Input(UInt(log2Ceil(tileQ max 2).W))
    // 索引来源：1 = TopK（正常通路），0 = 外部端口。
    //
    // 这是可测性设计，不是后门。它让「数据通路算得对不对」和「预测器挑得
    // 准不准」可以分开验证——前者是对错，后者是质量。合在一起时，一次失败
    // 说不清是 RePEA 算错了还是预测器挑了别的列。真实芯片里同样需要这种
    // 旁路来定位问题。
    val sched_from_topk = Input(Bool())
    val sched_ext_idx = Input(Vec(keptPerRow, UInt(colBits.W)))
    val sched_ext_valid = Input(Vec(keptPerRow, Bool()))
    val sched_pass = Input(UInt(log2Ceil(scheduler.passes max 2).W))
    val gather_col = Output(Vec(tileQ, Vec(peCountPerRow, UInt(colBits.W))))
    val gather_active = Output(Vec(tileQ, Vec(peCountPerRow, Bool())))

    // ---- 执行阶段：gather 好的精确 K/V 送进来 ---------------------------
    val execute_q = Input(Vec(tileQ, fpType))
    val execute_cols = Input(Vec(peCountPerRow, fpType))
    val execute_clr = Input(Bool())
    val execute_acc_ctrl = Input(UInt(2.W))
    val execute_exp_ctrl = Input(UInt(2.W))
    val execute_row_sum = Output(Vec(tileQ, fpType))

    // ---- 归一化：分子分母都由外部按阶段给 -------------------------------
    val norm_valid = Input(Bool())
    val norm_numerator = Input(Vec(tileQ, fpType))
    val norm_denominator = Input(Vec(tileQ, fpType))
    val out_valid = Output(Bool())
    val out = Output(Vec(tileQ, fpType))
  })

  // ---- 预测单元 ----------------------------------------------------------
  predict.io.left_in := io.predict_q
  predict.io.top_in := io.predict_k
  predict.io.pes_state := io.predict_pes_state
  predict.io.array_state := io.predict_array_state
  io.predict_score := predict.io.s_out

  // ---- 选择：每行一个 TopK ----------------------------------------------
  //
  // 分数由外部串行喂入而不是直接接 predict.io.s_out：PrePEA 每拍只产出
  // 一列的分数，要攒够 tileK 列才能挑 top-n，中间的攒和重放由外部控制。
  // 直接接线会把两个阶段的时序耦死。
  // 分档器：每行一个。不启用时完全不例化。
  private val tiers =
    if (tiered) Some(Seq.fill(tileQ)(Module(
      new BlockTierSelect(bits, point, keptHigh, keptLow, keptPerRow))))
    else None

  for (row <- 0 until tileQ) {
    selectors(row).io.enable := io.select_enable
    selectors(row).io.inData := io.select_in(row)
    io.select_idx(row) := selectors(row).io.idx

    tiers match {
      case Some(units) =>
        val tier = units(row)
        tier.io.mass := io.select_mass(row)
        tier.io.threshold_hi := io.select_threshold_hi
        tier.io.threshold_lo := io.select_threshold_lo
        tier.io.topk_valid := selectors(row).io.idxValid
        io.select_valid(row) := tier.io.valid
        io.select_keep(row) := tier.io.keep
        io.select_skipped(row) := tier.io.skipped
      case None =>
        // 固定 top-n：valid 原样透出，keep 恒为 keptPerRow。
        io.select_valid(row) := selectors(row).io.idxValid
        io.select_keep(row) := keptPerRow.U
        io.select_skipped(row) := false.B
    }
  }

  // ---- 调度 --------------------------------------------------------------
  scheduler.io.load := io.sched_load
  scheduler.io.load_row := io.sched_load_row
  scheduler.io.pass := io.sched_pass
  // 装载的是被选中那一行的索引。
  scheduler.io.load_idx := VecInit(
    (0 until keptPerRow).map { k =>
      val fromTopK = Wire(UInt(colBits.W))
      fromTopK := 0.U
      for (row <- 0 until tileQ) {
        when(io.sched_load_row === row.U) { fromTopK := selectors(row).io.idx(k) }
      }
      Mux(io.sched_from_topk, fromTopK, io.sched_ext_idx(k))
    }
  )
  scheduler.io.load_valid := VecInit(
    (0 until keptPerRow).map { k =>
      val fromTopK = Wire(Bool())
      fromTopK := false.B
      for (row <- 0 until tileQ) {
        when(io.sched_load_row === row.U) { fromTopK := selectors(row).io.idxValid(k) }
      }
      Mux(io.sched_from_topk, fromTopK, io.sched_ext_valid(k))
    }
  )
  io.gather_col := scheduler.io.gather_col
  io.gather_active := scheduler.io.gather_active

  // ---- 执行单元 ----------------------------------------------------------
  //
  // sel_cols 直接来自 scheduler：这就是那条曾经断开的线。
  execute.io.q_left_vec := io.execute_q
  execute.io.regs_top := io.execute_cols
  execute.io.clr := io.execute_clr
  execute.io.sel_cols := scheduler.io.sel_cols
  execute.io.acc_ctrl := io.execute_acc_ctrl
  execute.io.exp_ctrl := io.execute_exp_ctrl
  io.execute_row_sum := execute.io.rows_adder_out

  // ---- 归一化 ------------------------------------------------------------
  for (row <- 0 until tileQ) {
    normalisers(row).io.in_valid := io.norm_valid
    normalisers(row).io.numerator := io.norm_numerator(row)
    normalisers(row).io.denominator := io.norm_denominator(row)
    io.out(row) := normalisers(row).io.quotient
  }
  io.out_valid := normalisers(0).io.out_valid
}
