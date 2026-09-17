// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  跨行负载均衡——`index_scheduler.scala` 里明说了没做的那一半。
//
//  ## 它对应模型里的哪一个数
//
//  `fast/agents/codesign.py` 有：
//
//      pe_utilisation = 1 / (1 + (imbalance - 1) / (1 + queue_depth))
//
//  函数自己的注释写着「It is a model, not a measurement」。而 `queue_depth`
//  是协同优化器的一个**搜索维度**。更糟的是：这个公式对 queue_depth 单调
//  递增，而 `area_units()` 完全不收 queue_depth 的面积——只有收益没有成本，
//  优化器必然选最深的那个，而且看不出自己选错了。
//
//  流水化除法器那次是同一个形状的洞（模型缺了时钟周期这一项，44 倍的 EDP
//  差异完全看不见）。这个模块是用来把 queue_depth 从「模型」变成「实测」的：
//  综合它拿面积，仿真它拿利用率曲线。
//
//  ## 为什么队列能提高利用率
//
//  动态稀疏下每个 query 行保留的列数不同。一趟（pass）里一行最多喂
//  `peCountPerRow` 个保留列，所以行 r 处理一个 tile 需要
//  `ceil(kept_r / peCountPerRow)` 趟。没有队列时，阵列必须等最慢的行走完
//  才能换 tile，短行在那期间干等——利用率退化成 `mean/max`，也就是
//  `1/imbalance`，正是上面那个公式在 queue_depth=0 处的极限值。
//
//  给每行一个深度 `queueDepth + 1` 的工作队列后，先走完的行可以直接开始
//  下一个 tile 的活，最多领先其余行 `queueDepth` 趟。领先量被队列深度卡住，
//  这就是面积换利用率的那个取舍。
//
//  ## 耦合到底在哪里——这一点第一版做错过
//
//  最初的实现只给每行一个独立 FIFO，没有任何跨行约束。实测出来的利用率
//  对 queue_depth **完全平坦**（xm 在深度 0 和 16 都是 0.921）：行本来就
//  互不影响，队列没有东西可以缓解。测的是一个恒真命题。
//
//  真正的耦合在 **tile 边界**。上游 RePEArray 里 `regs_top` 是一个共享的
//  K 列寄存器窗口，逐行下移广播给所有行；`sel_cols(r)(p)` 只能在**当前
//  窗口里**选列。所以一行不可能去算窗口里没有的 K 列——窗口推进到 tile t+1
//  之前，所有行都被钉在 tile t 上。先算完的行只能空转。
//
//  于是 `queueDepth` 的物理含义是：**允许领先多少个 tile**。
//
//    * 深度 0：所有在干活的行必须在同一个 tile 上。一个 tile 花
//      `max_r passes_r` 拍，利用率退化成 `mean/max = 1/imbalance`——
//      正是 `pe_utilisation()` 在 0 处的解析极限。
//    * 深度 Q：先完成的行可以进到后面最多 Q 个 tile，利用率向 1 靠。
//
//  两个限制同时生效，都由 queueDepth 决定，也都是物理的：**tile 屏障**
//  （领先不超过 Q 个 tile）和 **缓冲容量**（每行只缓冲了 queueDepth+1 趟，
//  没有缓冲的数据就没法提前算）。
//
//  面积成本就是那个缓冲。这是 queue_depth 这笔交易的成本侧，
//  `area_units()` 现在完全没收。

package predict_unit

import chisel3._
import chisel3.util._

class BlockScheduler(
    val numRows: Int,        // query 行数 = RePEArray 的行数
    val peCountPerRow: Int,  // 每行的 PE 数 = 一趟能喂几个保留列
    val queueDepth: Int,     // 允许领先的趟数；0 = 严格锁步
    val blockM: Int,         // TopK 的 m，列索引空间
) extends Module {
  require(numRows > 0 && peCountPerRow > 0 && blockM >= 2)
  require(queueDepth >= 0)

  private val colBits = log2Ceil(blockM max 2)
  // 深度 queueDepth+1：一个槽装「当前正在做的这一趟」，剩下 queueDepth 个
  // 槽才是真正的领先余量。所以 queueDepth=0 得到严格锁步，和模型的
  // queue_depth=0 语义对齐。
  val entries: Int = queueDepth + 1

  /** 一趟工作：这一趟这一行要算哪几个保留列。 */
  class Pass extends Bundle {
    val cols = Vec(peCountPerRow, UInt(colBits.W))
    // 该趟是不是本行在这个 tile 里的最后一趟。tile 屏障靠它来数每行
    // 走到第几个 tile 了——所以它是控制信号，不是可选的元数据。
    val last = Bool()
    // 该槽是否对应一个真实的保留列。保留数不是 peCountPerRow 的整数倍时，
    // 最后一趟会有空槽——空槽的 PE 乘 0，不影响求和，但**要算进利用率的
    // 损失**，因为那个 PE 确实空转了。
    val active = Vec(peCountPerRow, Bool())
  }

  val io = IO(new Bundle {
    // ---- 生产侧：每行独立入队 -------------------------------------------
    //
    // **入队必须是每行并行的**，不能是单端口轮转。attention_tile.scala 里
    // 每个 query 行有自己的 TopK，索引本来就是并行产生的。做成单端口的话，
    // 生产者每拍只能喂一行、而阵列每拍要吃 numRows 行，瓶颈变成入队带宽，
    // 测出来的曲线反映的是那个人为瓶颈，和 queue_depth 没关系。
    val enq_valid = Input(Vec(numRows, Bool()))
    val enq_cols = Input(Vec(numRows, Vec(peCountPerRow, UInt(colBits.W))))
    val enq_active = Input(Vec(numRows, Vec(peCountPerRow, Bool())))
    // 每行标出「这是本 tile 的最后一趟」。
    val enq_last = Input(Vec(numRows, Bool()))
    // 每行的队列还能不能收。生产者被这个信号卡住，正是「领先量受限于
    // 队列深度」这件事在硬件里的体现。
    val enq_ready = Output(Vec(numRows, Bool()))
    val enq_ready_bits = Output(UInt(numRows.W))

    // ---- 消费侧：RePEArray 每拍吃一趟 -----------------------------------
    val issue_en = Input(Bool())
    val issue_cols = Output(Vec(numRows, Vec(peCountPerRow, UInt(colBits.W))))
    val issue_active = Output(Vec(numRows, Vec(peCountPerRow, Bool())))
    // 这一拍每行有没有活。利用率的分子就是它。
    val row_busy = Output(Vec(numRows, Bool()))
    // 同样的信息打包成一个字。testbench 读这个而不是读 numRows 个独立端口：
    // 64 行时那是 64 个端口，读法一旦写错，错的是「测量」而不是「被测对象」,
    // 而这种错不会让任何断言失败。
    val row_busy_bits = Output(UInt(numRows.W))

    // ---- 性能计数器 ------------------------------------------------------
    //
    // 放在硬件里而不是在 testbench 里数，有两个理由：一是真芯片上也需要
    // 它来验证调度策略；二是 testbench 数出来的是「testbench 以为发生了
    // 什么」，计数器数出来的是「硬件里实际发生了什么」，这两者不一致的
    // 时候，前者会安静地骗人。
    val perf_clear = Input(Bool())
    // 有任何一行在干活的拍数（分母）
    val cycles_active = Output(UInt(32.W))
    // 所有行「行·拍」忙碌数的累加（分子）；除以 numRows*cycles_active
    // 就是利用率。
    val row_cycles_busy = Output(UInt(32.W))
    // PE 粒度：把一趟里的空槽也算进去，得到比行粒度更严的利用率。
    val pe_cycles_busy = Output(UInt(32.W))
    val drained = Output(Bool())
  })

  // 每行一个独立队列。用 Chisel 的 Queue 而不是自己写指针：这里要量的是
  // 深度与利用率的关系，不是我能不能写对一个 FIFO。
  //
  // `pipe = true` 不是可选项。默认的 Queue 在**满**的那一拍不接受入队，
  // 哪怕同一拍正在出队。深度 0（entries=1）时这让吞吐正好减半：一拍出、
  // 一拍等补，实测利用率 0.379 而解析界是 0.708。那个 2 倍是 FIFO 的
  // 握手伪影，不是负载不均衡——把它留在数据里，标定出来的就是一条
  // 「队列深度能治好 FIFO 自己的气泡」的假曲线。
  private val queues = Seq.fill(numRows)(Module(new Queue(new Pass, entries, pipe = true)))

  private val rowBusy = Wire(Vec(numRows, Bool()))
  private val peBusyCount = Wire(Vec(numRows, UInt(log2Ceil(peCountPerRow + 1).W)))
  private val leaving = Wire(Vec(numRows, Bool()))
  private val holdBarrier = Wire(Vec(numRows, Bool()))

  // 每行当前走到第几个 tile。tile 屏障就是限制这些计数器之间的差。
  //
  // **每个 tile 每行必须恰好有一个 last 趟，包括保留数为 0 的行**，否则
  // 这个计数器数的是「本行有活干的第几个 tile」而不是真实 tile 序号，
  // 参与稀疏的行会和其它行错位，屏障就在拿两个不同的量相比。
  //
  // 调度器为空行发一趟全 inactive 的空趟来对齐。这不是为了对齐而付出的
  // 代价——那一拍那一行本来就在空转，空趟如实反映了它。topk 上这个 bug
  // 让利用率从 0.609 掉到 0.394（空行最多），xm 上只差 0.5%。
  //
  // ## 为什么记「领先量」而不是「tile 序号」
  //
  // 第一版给每行一个 16 位 tile 序号，屏障取所有活跃行的 min。Chisel 的
  // `reduce` 是左结合的，生成的是 numRows 级 16 位比较器**线性链**——
  // 综合实测 32 行 19.0 ns（52 MHz）、64 行 36.6 ns（27 MHz），几乎不随
  // 深度变、和行数成正比，正是线性链的签名。而执行阵列是 2.23 ns。
  // 调度器会直接变成整个系统的新瓶颈。
  //
  // 换成相对量之后，宽度从 16 位降到 log2(queueDepth+2)，而且**没有任何
  // 跨行的算术**：只有一个共享寄存器 `barrierTile` 和每行一个小计数器。
  //
  //   ahead(r) = 该行领先屏障几个 tile，恒在 [0, queueDepth+1]
  //
  // 屏障条件退化成 `ahead(r) <= queueDepth`（几位的比较），
  // 「还压在屏障上」退化成 `ahead(r) === 0`（几位的相等）。
  private val aheadBits = log2Ceil(queueDepth + 3)
  private val ahead = RegInit(VecInit(Seq.fill(numRows)(0.U(aheadBits.W))))

  private val hasWork = VecInit(queues.map(_.io.deq.valid))

  for (r <- 0 until numRows) {
    val q = queues(r)
    q.io.enq.valid := io.enq_valid(r)
    q.io.enq.bits.cols := io.enq_cols(r)
    q.io.enq.bits.active := io.enq_active(r)
    q.io.enq.bits.last := io.enq_last(r)
    io.enq_ready(r) := q.io.enq.ready

    // tile 屏障：领先屏障不得超过 queueDepth 个 tile。
    // queueDepth=0 时退化成「所有在干活的行必须在同一个 tile 上」。
    val withinBarrier = ahead(r) <= queueDepth.U
    val fire = io.issue_en && q.io.deq.valid && withinBarrier
    q.io.deq.ready := io.issue_en && withinBarrier
    leaving(r) := fire && q.io.deq.bits.last
    // 还压在屏障 tile 上、且这一拍没走完的行，挡住窗口推进。
    //
    // 队列**空**的行也算挡住（fire 为假）：模块看不到生产者后面还会不会
    // 给这一行送这个 tile 的活，提前推进屏障会让它落到屏障后面，
    // `ahead` 就要下溢——那是死锁，不是性能损失。保守地等一拍不会错。
    holdBarrier(r) := (ahead(r) === 0.U) && !leaving(r)

    // 被屏障挡住的行这一拍就是空转的——那正是 imbalance 造成的损失，
    // 必须如实体现在 row_busy 上，否则测出来的利用率是假的。
    //
    // 空趟（全 inactive）也算空转：它存在只是为了推进 tile 计数器，
    // 那一拍没有任何 PE 在算。把它算成忙会让 row_util 虚高。
    rowBusy(r) := fire && q.io.deq.bits.active.reduceTree(_ || _)
    io.issue_cols(r) := q.io.deq.bits.cols
    // 没发射时输出全 inactive，下游 PE 读零逃逸。
    for (p <- 0 until peCountPerRow) {
      io.issue_active(r)(p) := fire && q.io.deq.bits.active(p)
    }
    peBusyCount(r) := PopCount(io.issue_active(r))
  }

  // 屏障推进：没有行还压在当前 tile 上时，K 列窗口换到下一个 tile。
  //
  // `ahead` 的更新必须和这个推进一起看，否则会下溢：
  //   走完本 tile (+1) 且屏障推进 (-1) -> 不变
  //   只走完                            -> +1
  //   只推进                            -> -1
  // 屏障只在「所有行要么已经领先、要么这一拍正好走完」时推进，所以推进后
  // 每行的 ahead 都 >= 1，减 1 不会到负数。
  //
  // A barrier transaction is atomic: issue permission, last-pass completion,
  // and the shared barrier advance must use the SAME cycle's state. Registering
  // only the completion/advance while issuing from the old ahead value permits
  // a row to cross the boundary twice and can underflow another row's counter.
  // A 128-tile real trace slice exposed this as deadlock at depths 0, 2 and 4.
  private val barrierAdvance = io.issue_en && !holdBarrier.reduceTree(_ || _)

  for (r <- 0 until numRows) {
    when(leaving(r) && !barrierAdvance) { ahead(r) := ahead(r) + 1.U }
      .elsewhen(!leaving(r) && barrierAdvance) { ahead(r) := ahead(r) - 1.U }
    assert(ahead(r) <= (queueDepth + 1).U, "tile lead exceeded barrier window")
  }

  io.row_busy := rowBusy
  io.row_busy_bits := rowBusy.asUInt
  io.enq_ready_bits := VecInit(queues.map(_.io.enq.ready)).asUInt
  // 排空 = 所有队列都空。不能看 rowBusy：被屏障挡住的那一拍 rowBusy 是 0，
  // 但队列里还有活，那时判排空会让仿真提前结束、少算一大截工作。
  io.drained := !hasWork.asUInt.orR

  // ---- 计数器 -------------------------------------------------------------
  // Public counters have a cycle-level contract: all three account for the
  // same issuing edge, and perf_clear takes precedence on that edge. A pipeline
  // cannot silently change this interface or keep adding pre-clear samples.
  // Balanced trees reduce combinational depth without changing the protocol.
  private val counting = io.issue_en && hasWork.asUInt.orR
  private val cyclesActive = RegInit(0.U(32.W))
  private val rowCyclesBusy = RegInit(0.U(32.W))
  private val peCyclesBusy = RegInit(0.U(32.W))

  when(io.perf_clear) {
    cyclesActive := 0.U
    rowCyclesBusy := 0.U
    peCyclesBusy := 0.U
  }.elsewhen(counting) {
    cyclesActive := cyclesActive + 1.U
    rowCyclesBusy := rowCyclesBusy + PopCount(rowBusy)
    peCyclesBusy := peCyclesBusy + peBusyCount.reduceTree(_ +& _)
  }

  io.cycles_active := cyclesActive
  io.row_cycles_busy := rowCyclesBusy
  io.pe_cycles_busy := peCyclesBusy
}