// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  这是预测单元和执行单元之间**唯一断开的那一环**。
//
//  追一遍数据通路就能看到断点在哪：
//
//      PrePEArray.s_out   Vec(height, FixedPoint)      每行一个 exp(近似分数)
//              ↓
//      TopK.idx           Vec(n, UInt(log2 m))         top-n 在 m 宽块内的下标
//              ↓
//          ??? 断在这里
//              ↓
//      RePEArray.sel_cols Vec(rows, Vec(pe, UInt(..))) 每个 PE 取哪个列寄存器
//
//  两端是**不同的索引空间**：`TopK.idx` 说的是「在 64 宽的块里排第几」
//  （0..m-1），`sel_cols` 说的是「在流进来的 regWidth 个列寄存器里取第几个」
//  （0..regWidth）。把前者变成后者，正是论文 Algorithm 1 的 block scheduler
//  加 N-index buffer 干的事——把软件块重组成匹配 PEA 尺寸的硬件块。
//
//  ## 一个让实现变简单的认识
//
//  `reg_cols` 是**流进来的**数据。如果存储侧按索引先把 K 列 gather 好再送
//  进来，PE i 就只需要取第 i 个寄存器，`sel_cols` 退化成恒等映射。
//
//  **真正的工作在地址生成，不在列选。** 所以这个模块的主要产出是
//  `gather_col`：每个 pass、每个 PE 要取哪一列 K。N-index buffer 本质上
//  是个地址发生器。
//
//  ## 和论文的差别，必须说清楚
//
//  论文的 Algorithm 1 还做**跨行负载均衡**：不同 query 行保留的列数不同，
//  调度器把它们重新打包，让每个硬件块都填满。这里没有做——每行独立分组，
//  不足一组的用零槽补齐。
//
//  后果是 PE 利用率偏低（正是 `pe_utilisation()` 建模的那个损失），
//  但**结果是正确的**：补零的 PE 乘出 0，不影响求和。先把链路打通、
//  结果对得上 PyTorch，再谈均衡。

package predict_unit

import chisel3._
import chisel3.util._

class IndexScheduler(
    val numRows: Int,       // query 行数
    val keptPerRow: Int,    // TopK 的 n
    val peCountPerRow: Int, // RePEA 每行的 PE 数
    val blockM: Int,        // TopK 的 m，索引空间大小
) extends Module {
  require(numRows > 0 && keptPerRow > 0 && peCountPerRow > 0)
  require(blockM >= keptPerRow, s"keptPerRow=$keptPerRow 不能超过 blockM=$blockM")

  // 一行的 n 个保留列要分几趟才能喂完 peCountPerRow 个 PE。
  val passes: Int = (keptPerRow + peCountPerRow - 1) / peCountPerRow
  private val colBits = log2Ceil(blockM max 2)
  // sel_col 的取值是 0..regWidth，其中 regWidth 是「零逃逸」。这里
  // regWidth == peCountPerRow（gather 之后恒等映射），所以需要能表示
  // peCountPerRow 本身。
  val colSelectBits: Int = log2Ceil(peCountPerRow + 2)

  val io = IO(new Bundle {
    // ---- 从 TopK 收：每行一组索引 --------------------------------------
    val load = Input(Bool())
    val load_row = Input(UInt(log2Ceil(numRows max 2).W))
    val load_idx = Input(Vec(keptPerRow, UInt(colBits.W)))
    // TopK 的 idxValid：某个 lane 没有有效值时（保留数不足 n），对应槽为空。
    val load_valid = Input(Vec(keptPerRow, Bool()))

    // ---- 发给存储侧：这一趟要 gather 哪些 K 列 --------------------------
    val pass = Input(UInt(log2Ceil(passes max 2).W))
    val gather_col = Output(Vec(numRows, Vec(peCountPerRow, UInt(colBits.W))))
    // 该槽这一趟是否真的对应一个保留列。false 时存储侧不必取数，
    // 且 sel_cols 会指向零逃逸。
    val gather_active = Output(Vec(numRows, Vec(peCountPerRow, Bool())))

    // ---- 发给 RePEA：每个 PE 取第几个列寄存器 ---------------------------
    val sel_cols = Output(Vec(numRows, Vec(peCountPerRow, UInt(colSelectBits.W))))
  })

  // 每行保留的索引与有效位。TopK 一行一行地送进来，所以这里要存住。
  private val indices = Reg(Vec(numRows, Vec(keptPerRow, UInt(colBits.W))))
  private val actives = RegInit(
    VecInit(Seq.fill(numRows)(VecInit(Seq.fill(keptPerRow)(false.B))))
  )

  when(io.load) {
    indices(io.load_row) := io.load_idx
    actives(io.load_row) := io.load_valid
  }

  for (row <- 0 until numRows) {
    for (pe <- 0 until peCountPerRow) {
      // 第 p 趟的第 pe 个 PE 对应保留列表里的第 p*P+pe 项。
      val slot = Wire(UInt(log2Ceil(keptPerRow + 1).W))
      slot := io.pass * peCountPerRow.U + pe.U

      val inRange = slot < keptPerRow.U
      val column = Wire(UInt(colBits.W))
      val active = Wire(Bool())
      column := 0.U
      active := false.B
      // keptPerRow 通常很小（8-32），直接展开成多路选择比动态索引更省。
      for (k <- 0 until keptPerRow) {
        when(slot === k.U) {
          column := indices(row)(k)
          active := actives(row)(k)
        }
      }

      io.gather_col(row)(pe) := column
      io.gather_active(row)(pe) := inRange && active
      // gather 之后是恒等映射：PE pe 取第 pe 个寄存器。槽无效时指向
      // peCountPerRow，也就是 RePE 的零逃逸——它会乘出 0，不影响求和。
      io.sel_cols(row)(pe) := Mux(
        inRange && active, pe.U, peCountPerRow.U
      )
    }
  }
}
