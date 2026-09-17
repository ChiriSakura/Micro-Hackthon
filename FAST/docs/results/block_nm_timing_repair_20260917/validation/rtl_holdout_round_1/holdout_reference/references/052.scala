// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  动态 X:M 的**分档选择**：按 block 的概率质量决定这一块留几个。
//
//  ## 硬件原来没有这一层
//
//  DynaX 软件侧的 `gen_sparsity_mask_xm` 是三档的：
//
//      块质量 > threshold_0   ->  留 n1
//      块质量 < threshold_1   ->  留 0
//      其余                   ->  留 n2
//
//  而硬件的 `TopK(m, n)` 是**固定 top-n 级联**，永远留 n 个——没有阈值比较，
//  没有分档。于是「硬件实现的是不是 X:M」这个问题的答案一直是「不是，是
//  top-n」，而 tile 抓取的参照也用的是固定 top-n，两边一致地错，形状匹配
//  看不出来。
//
//  这正是评审 P0-5 的根子：不是 testbench 没测，是这一层不存在。
//
//  ## 质量从哪来
//
//  `PrePEArray_1_2` 已经算出每行的 `exp_sum`（sumRegs，exp 之后的和）——
//  块质量是现成的，不需要新的算术。这里只做比较和分档。
//
//  ## 软件那个 `* token_len / m` 的缩放
//
//  软件里 `sum_m = sum(block) * token_len / m`，即把块内和放大到「如果整行
//  都是这个密度」的尺度上。阈值是在那个尺度上定的，所以硬件要么同样缩放，
//  要么把阈值预先除掉——这里选后者：**缩放放在软件侧算阈值时做**，硬件只比
//  原始的块和。理由是乘法器省下来了，而阈值本来就是标定出来的常数。
package predict_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

class BlockTierSelect(
    val bits: Int,
    val point: Int,
    /** 高档保留数（软件的 n1）。 */
    val n1: Int,
    /** 中档保留数（软件的 n2）。 */
    val n2: Int,
    /** TopK 级联的宽度：硬件一次最多能给出这么多个索引。 */
    val keptPerRow: Int,
) extends Module {
  require(0 < n2 && n2 <= n1 && n1 <= keptPerRow,
    s"需要 0 < n2 <= n1 <= keptPerRow，收到 n1=$n1 n2=$n2 kept=$keptPerRow")

  private val fpType = FixedPoint(bits.W, point.BP)

  val io = IO(new Bundle {
    /** 这个 block 的概率质量（`PrePEArray` 的 exp_sum）。 */
    val mass = Input(fpType)
    /** 高档阈值（软件的 threshold_0，已按 m/token_len 折算）。 */
    val threshold_hi = Input(fpType)
    /** 丢弃阈值（软件的 threshold_1，同样已折算）。 */
    val threshold_lo = Input(fpType)
    /** TopK 给出的 valid，按分档结果被裁剪之后输出。 */
    val topk_valid = Input(Vec(keptPerRow, Bool()))

    /** 这一块实际保留几个：n1 / n2 / 0。 */
    val keep = Output(UInt(log2Ceil(keptPerRow + 1).W))
    /** 裁剪后的 valid：前 keep 个为真。 */
    val valid = Output(Vec(keptPerRow, Bool()))
    /** 这一块整块被跳过。调度器可以据此完全不发这一块的取数请求。 */
    val skipped = Output(Bool())
  })

  // 三档。**比较的顺序和软件一致**：先按 lo 判丢弃，再用 hi 覆盖成高档。
  // 软件里是两次 `torch.where` 叠加，等价于「hi 优先」。
  private val below = io.mass < io.threshold_lo
  private val above = io.mass > io.threshold_hi
  io.keep := Mux(above, n1.U, Mux(below, 0.U, n2.U))
  io.skipped := below && !above

  // 裁剪：TopK 的第 k 个索引只有在 k < keep 时才算数。
  //
  // **不是把 TopK 关掉**——级联仍然跑满，只是后面的索引不被采纳。这样
  // 时序不随分档变化（分档是数据相关的，让关键路径跟着数据变会让 STA
  // 说不清），代价是功耗上省不到那部分。这个取舍要记在能量模型里。
  for (k <- 0 until keptPerRow) {
    io.valid(k) := io.topk_valid(k) && (k.U < io.keep)
  }
}
