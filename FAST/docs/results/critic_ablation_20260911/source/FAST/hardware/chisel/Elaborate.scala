// Emit Verilog for one DynaX module so Verilator can compile it.
//
// Chisel is pinned to 3.6: the DynaX sources use chisel3.experimental.FixedPoint,
// which Chisel 5 removed. Moving to 5.x means porting those sources first, so the
// pin is a statement about the RTL, not a preference.
//> using scala "2.13.12"
// Chisel 3.6 still lives under edu.berkeley.cs; the org.chipsalliance coordinates
// only start at Chisel 5, which is exactly the release that dropped FixedPoint.
//> using dep "edu.berkeley.cs::chisel3:3.6.1"
//> using plugin "edu.berkeley.cs:::chisel3-plugin:3.6.1"

import chisel3.stage.{ChiselGeneratorAnnotation, ChiselStage}

object Elaborate extends App {
  // Datapath format shared by every module: Q8.8 signed fixed point. `point`
  // also sets the exponential unit's mantissa resolution.
  private val Bits = 16
  private val Point = 8

  // The two configurations the DynaX paper reports (Table 2 / Sec. 6):
  //
  //   DynaX-S: 32x32 PrePEA, 4-bit operands, 1:2 Q pruning, N:M = 8:32,
  //            four 32x4 RePEAs
  //   DynaX-L: 64x32 PrePEA, 6-bit operands, 1:4 Q pruning, N:M = 16:64,
  //            four 64x8 RePEAs
  //
  // The operand widths are not free parameters: prepe_1_2.scala hardcodes
  // UInt(4.W) ports and prepe_1_4.scala hardcodes UInt(6.W), which is how the
  // sources identify which paper configuration each belongs to.

  // Partial-sum width inside a PrePE row. The psum is a purely spatial chain --
  // pes(r)(c).psum_in comes from pes(r)(c-1).psum_out and each PE contributes
  // exactly one product per sCalc cycle -- so the row accumulates width/K
  // products, not `width` of them. K is 2 for 1:2 pruning and 4 for 1:4.
  //
  // prepe_*.scala also require internalBits + append <= bits: they zero-extend
  // the psum into the exponential unit's format with
  // Cat(0.U((bits - internalBits - append).W), ...), which fails elaboration on
  // a negative width. 17 bits (the width if the chain were 32 long) is exactly
  // how that constraint announces itself.
  private val PSumBitsS = 12 // 4x4-bit products, chain of 32/2 = 16
  private val PSumBitsL = 15 // 6x6-bit products, chain of 32/4 = 8

  // Column registers feeding one RePE, and the width of the selector that
  // picks among them (+1 for the "read zero" escape value col_vec(regWidth)).
  private def colSelectBits(regWidth: Int): Int =
    chisel3.util.log2Ceil(regWidth + 2)

  /** 把 "PLAN:k=v,k=v" 解析成参数表。
    *
    * 用 key=value 而不是 JSON，是因为加一个 JSON 库要多一条依赖，而这里
    * 要传的只是十来个整数。格式简单到肉眼能核对——一个规划参数传错了，
    * 造出来的是另一个设计，而它看起来完全正常。
    */
  private def planOf(spec: String): Map[String, Int] =
    spec.stripPrefix("PLAN:").split(",").filter(_.nonEmpty).map { entry =>
      val Array(key, value) = entry.split("=", 2)
      key.trim -> value.trim.toInt
    }.toMap

  /** PrePEA 一行的部分和位宽。
    *
    * **算出来而不是让调用方传。** 它由 width 和剪枝比 K 唯一决定：
    * 每个乘积是 operand x operand 位，一行累加 width/K 个乘积，所以
    *
    *     psumBits = 2 * operandBits + ceil(log2(width / K))
    *
    * 而 `prepe_*.scala` 还要求 `internalBits + append <= bits`。传错这个数
    * 的后果是 elaborate 在一个负位宽上失败，或者更糟——静默截断部分和。
    * 让调用方传，就是把一个可推导的量变成一个可以传错的量。
    */
  private def psumBitsFor(width: Int, k: Int, operandBits: Int): Int =
    2 * operandBits + chisel3.util.log2Ceil(math.max(width / k, 2))

  private def gen(target: String): () => chisel3.RawModule = target match {
    // Exact component inventories for frozen candidates. These are independent
    // modules, not an integrated dynamic-X:M attention accelerator.
    case s if s.startsWith("InventoryRePE_") =>
      val Pattern = "InventoryRePE_R([0-9]+)P([0-9]+)W([0-9]+)".r
      val Pattern(rows, pes, regs) = s
      () => new execute_unit.RePEArray(
        peCountPerRow = pes.toInt, bits = Bits, point = Point,
        regWidth = regs.toInt, numRows = rows.toInt,
        colSelectBits = colSelectBits(regs.toInt))
    case s if s.startsWith("InventoryPrePE_") =>
      val Pattern = "InventoryPrePE_R([0-9]+)D([0-9]+)".r
      val Pattern(rows, dim) = s
      () => new predict_unit.PrePEArray_1_2(
        bits = Bits, point = Point, append = 0,
        internalBits = psumBitsFor(dim.toInt, 2, 4),
        width = dim.toInt, height = rows.toInt)
    case s if s.startsWith("InventoryTopK_") =>
      val Pattern = "InventoryTopK_M([0-9]+)N([0-9]+)".r
      val Pattern(m, n) = s
      () => new predict_unit.TopK(m = m.toInt, n = n.toInt, bits = Bits, point = Point)
    case s if s.startsWith("InventoryFeeder_") =>
      val Pattern = "InventoryFeeder_W([0-9]+)B([0-9]+)D([0-9]+)".r
      val Pattern(regs, banks, depth) = s
      () => new execute_unit.KeyFeeder(bits = Bits, point = Point,
        regWidth = regs.toInt, bankCount = banks.toInt, bankDepth = depth.toInt)
    // ---- exponential unit (FAST reconstruction, see exp_unit.scala) --------
    case "ExpUnit" =>
      () => new exp_unit.ExpUnitFixPoint(Bits, Point, intBits = 6, fracBits = 4)

    // ---- predict unit -----------------------------------------------------
    case "TopK" => () => new predict_unit.TopK(m = 64, n = 16, bits = Bits, point = Point)
    case "TopK_S" => () => new predict_unit.TopK(m = 32, n = 8, bits = Bits, point = Point)
    case "TopFirst" =>
      () => new predict_unit.TopFirst(bits = Bits, point = Point, idxBits = 6, depth = 64)
    // 预测单元和执行单元之间的断点：TopK 的块内索引 -> RePEA 的列选 +
    // 存储侧的 gather 地址。论文的 Algorithm 1（block scheduler +
    // N-index buffer）就是这一环，开源里没有。
    // 完整的 attention tile：把 5 个模块连成一条链。开源 DynaX 没有顶层，
    // 每个大模块的实例化次数都是 0——这是第一个把它们连起来的东西。
    // 把控制收进硬件的那一层：状态机自己走完 QK -> exp -> AV -> norm，
    // 跨趟累加在寄存器里，完成拍数由硬件数。见 attention_tile_top.scala。
    // 动态阈值分档的 tile：n1=8 / n2=4 / m=32，对应 `xm:8:4:32`。
    // 和 `AttentionTile` 同尺寸，唯一区别是选择语义从固定 top-n 变成三档。
    // 完整系统：分档选择 + 硬件自己挑的索引 + 带反压的取数引擎 + 计算阵列。
    // 这是唯一能回答「总延迟里有多少是等存储」的配置。
    case "AttentionTileSystem" =>
      () => new AttentionTileSystem(
        bits = Bits, point = Point,
        tileQ = 4, tileK = 32, headDim = 8,
        keptPerRow = 8, peCountPerRow = 8,
        psumBits = 12, dividerStages = 8,
        keptHigh = 8, keptLow = 4,
        bankCount = 8,
      )
    // bank 数扫描用：冲突 -> 反压 -> 停顿的实测曲线，对照代价模型里
    // 那个标定出来的 gather_slowdown 系数。
    case s if s.startsWith("AttentionTileSystem_B") =>
      val banks = s.stripPrefix("AttentionTileSystem_B").toInt
      () => new AttentionTileSystem(
        bits = Bits, point = Point,
        tileQ = 4, tileK = 32, headDim = 8,
        keptPerRow = 8, peCountPerRow = 8,
        psumBits = 12, dividerStages = 8,
        keptHigh = 8, keptLow = 4,
        bankCount = banks,
      )
    case "AttentionTile_Tiered" =>
      () => new AttentionTile(
        bits = Bits, point = Point,
        tileQ = 4, tileK = 32, headDim = 8,
        keptPerRow = 8, peCountPerRow = 8,
        psumBits = 12, dividerStages = 8,
        keptHigh = 8, keptLow = 4,
      )
    case "AttentionTileTop" =>
      () => new AttentionTileTop(
        bits = Bits, point = Point,
        tileQ = 4, tileK = 32, headDim = 8,
        keptPerRow = 8, peCountPerRow = 8,
        psumBits = 12, dividerStages = 8,
      )
    // 多趟：kept > peCountPerRow，跨趟累加器才真的被用到。
    case "AttentionTileTop_MultiPass" =>
      () => new AttentionTileTop(
        bits = Bits, point = Point,
        tileQ = 4, tileK = 32, headDim = 8,
        keptPerRow = 8, peCountPerRow = 4,
        psumBits = 12, dividerStages = 8,
      )
    case "AttentionTile" =>
      () => new AttentionTile(
        bits = Bits, point = Point,
        tileQ = 4, tileK = 32, headDim = 8,
        // kept == peCountPerRow：一趟就覆盖全部保留列，scheduler.passes = 1。
        // 分多趟本身是对的（结果相加），但会把「数据通路对不对」和
        // 「多趟累加对不对」两个变量搅在一起，先验证前者。
        keptPerRow = 8, peCountPerRow = 8,
        psumBits = 12, dividerStages = 8,
      )
    // 按 planner 给的参数造一个完整的注意力 tile。
    //
    // **这是「计划」变成「设计」的那一步。** 在它之前，planner 能说出
    // 「32x4、queue 2、8 banks」，但没有任何东西把那句话变成可综合的顶层
    // ——`gen` 是一个固定的目标枚举，AttentionTile 被写死在 4x32x8。
    // 系统因此能**规划**出 DynaX 尺寸，却造不出它。
    case s if s.startsWith("PLAN:") =>
      val p = planOf(s)
      val width = p.getOrElse("headDim", 32)
      () => new AttentionTile(
        bits = p.getOrElse("bits", Bits),
        point = p.getOrElse("point", Point),
        tileQ = p("tileQ"),
        tileK = p("tileK"),
        headDim = width,
        keptPerRow = p("keptPerRow"),
        peCountPerRow = p("peCountPerRow"),
        // 1:2 剪枝，4 位操作数——和 `PrePEArray_1_2` 的端口宽度一致。
        psumBits = p.getOrElse("psumBits", psumBitsFor(width, 2, 4)),
        dividerStages = p.getOrElse("dividerStages", 8),
      )
    case "IndexScheduler" =>
      () => new predict_unit.IndexScheduler(
        numRows = 4, keptPerRow = 8, peCountPerRow = 4, blockM = 32)
    case "IndexScheduler_S" =>
      () => new predict_unit.IndexScheduler(
        numRows = 32, keptPerRow = 8, peCountPerRow = 4, blockM = 32)
    // 跨行负载均衡的工作队列。queue_depth 是协同优化器的搜索维度，而
    // pe_utilisation() 对它单调递增、area_units() 又不收它的面积——只有
    // 收益没有成本。这几个配置用来量出「深度 vs 面积」和「深度 vs 利用率」
    // 两条实测曲线，把那个维度从模型变成测量。
    //
    // 尺寸取论文的两个配置：DynaX-S 是 32 行 x 4 PE，DynaX-L 是 64 行 x 8 PE。
    case s if s.startsWith("BlockSched_R") =>
      val Pattern = "BlockSched_R([0-9]+)P([0-9]+)M([0-9]+)Q([0-9]+)".r
      val Pattern(rows, pes, block, depth) = s
      () => new predict_unit.BlockScheduler(
        numRows = rows.toInt, peCountPerRow = pes.toInt,
        queueDepth = depth.toInt, blockM = block.toInt)
    case s if s.startsWith("BlockSched_S") =>
      val depth = s.stripPrefix("BlockSched_S").toInt
      () => new predict_unit.BlockScheduler(
        numRows = 32, peCountPerRow = 4, queueDepth = depth, blockM = 64)
    case s if s.startsWith("BlockSched_L") =>
      val depth = s.stripPrefix("BlockSched_L").toInt
      () => new predict_unit.BlockScheduler(
        numRows = 64, peCountPerRow = 8, queueDepth = depth, blockM = 64)
    case "FixedPointDiv" => () => new predict_unit.FixedPointDiv(Bits, Point)
    // 流水化除法器，级数是搜索维度。实测发现组合除法（上游）是整个系统
    // 的瓶颈：14.83 ns / 67 MHz，而执行阵列能跑 450 MHz。这几个配置用来
    // 量出面积与频率的取舍曲线，让协同优化器能在上面取点。
    case "DivPipe1" => () => new predict_unit.FixedPointDivPipelined(Bits, Point, 1)
    case "DivPipe4" => () => new predict_unit.FixedPointDivPipelined(Bits, Point, 4)
    case "DivPipe8" => () => new predict_unit.FixedPointDivPipelined(Bits, Point, 8)
    case "DivPipe12" => () => new predict_unit.FixedPointDivPipelined(Bits, Point, 12)
    case "DivPipe24" => () => new predict_unit.FixedPointDivPipelined(Bits, Point, 24)
    case "PSumSoftmax" => () => new predict_unit.PSumSoftmax(Bits, Point)

    // 控制广播扇出的**对照实验**：同一个阵列，只改广播树级数。
    //
    // 扁平广播（stages=0）实测让 STA 报出 196 ns 的单级延迟——那是缺缓冲的
    // 伪影，时序适配器整个丢弃，于是预测阵列从来没有可用的时序数。这两个
    // 目标用来量「加了树之后时序是否变得可信、代价是多少面积和几拍延迟」。
    case "PrePEArray_S_Flat" =>
      () =>
        new predict_unit.PrePEArray_1_2(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsS, width = 32, height = 32,
          broadcastStages = 0,
        )
    case "PrePEArray_S_Buffered" =>
      () =>
        new predict_unit.PrePEArray_1_2(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsS, width = 32, height = 32,
          broadcastStages = 2,
        )
    // 计划尺寸：16x64 和 32x64 是循环实际规划出来的形状，扇出最坏。
    case "PrePEArray_Plan_Flat" =>
      () =>
        new predict_unit.PrePEArray_1_2(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsS, width = 64, height = 32,
          broadcastStages = 0,
        )
    case "PrePEArray_Plan_Buffered" =>
      () =>
        new predict_unit.PrePEArray_1_2(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsS, width = 64, height = 32,
          broadcastStages = 2,
        )
    case "PrePEArray_S" =>
      () =>
        new predict_unit.PrePEArray_1_2(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsS, width = 32, height = 32,
        )
    case "PrePEArray_L" =>
      () =>
        new predict_unit.PrePEArray_1_4(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsL, width = 32, height = 64,
        )
    // A small predict array for the functional bench: 2 rows of 4 PEs over an
    // 8-wide head dimension. The 1:2 pruning decision lives in the array's
    // cycleToggle block rather than in a PE, so it can only be checked here.
    // 尺寸二分用：隔离 32x32 的失配是 height 还是 width 引起的。
    case "PrePEArray_H32W8" =>
      () => new predict_unit.PrePEArray_1_2(
        bits = Bits, point = Point, append = 0,
        internalBits = PSumBitsS, width = 8, height = 32)
    case "PrePEArray_H2W32" =>
      () => new predict_unit.PrePEArray_1_2(
        bits = Bits, point = Point, append = 0,
        internalBits = PSumBitsS, width = 32, height = 2)
    case "PrePEArray_T" =>
      () =>
        new predict_unit.PrePEArray_1_2(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsS, width = 8, height = 2,
        )
    // The 1:4 counterpart, at the same small size. Its selection stage is a
    // three-deep shift register plus a four-way comparator, so it needs its own
    // bench: the 1:2 array's two-way compare cannot stand in for it.
    case "PrePEArray14_T" =>
      () =>
        new predict_unit.PrePEArray_1_4(
          bits = Bits, point = Point, append = 0,
          internalBits = PSumBitsL, width = 8, height = 2,
        )
    // Single-PE variants: same logic, seconds instead of minutes to elaborate,
    // so a datapath bug shows up before paying for the full array.
    case "PrePE_1_2" => () => new predict_unit.PrePE_1_2(PSumBitsS)
    case "PrePE_1_4" => () => new predict_unit.PrePE_1_4(PSumBitsL)

    // ---- execute unit -----------------------------------------------------
    case "RePE" =>
      () => new execute_unit.RePE(Bits, Point, regWidth = 8, colSelectBits(8), id = (0, 0))
    case "RePERow" =>
      () =>
        new execute_unit.RePERow(
          peCount = 8, bits = Bits, point = Point,
          regWidth = 8, colSelectBits = colSelectBits(8), rowId = 0,
        )
    // A small array for the functional bench. The systolic behaviour is
    // size-independent -- rows chain identically whether there are 4 or 64 --
    // and 4 rows still exercises the inter-row link, while keeping the port
    // count hand-writable. The paper-sized configurations below prove it
    // composes; this one proves it is right.
    case "RePEArray_T" =>
      () =>
        new execute_unit.RePEArray(
          peCountPerRow = 2, bits = Bits, point = Point,
          regWidth = 4, numRows = 4, colSelectBits = colSelectBits(4),
        )
    // 论文尺寸。功能验证走 slurm/rtl/fast_rtl_verify_paper.slurm：
    // testbench 的端口访问由 tb/gen_ports.py 按尺寸生成，因为 64x8 的
    // sel_cols 有 512 个端口。
    case "RePEArray_S" =>
      () =>
        new execute_unit.RePEArray(
          peCountPerRow = 4, bits = Bits, point = Point,
          regWidth = 8, numRows = 32, colSelectBits = colSelectBits(8),
        )
    case "RePEArray_L" =>
      () =>
        new execute_unit.RePEArray(
          peCountPerRow = 8, bits = Bits, point = Point,
          regWidth = 16, numRows = 64, colSelectBits = colSelectBits(16),
        )

    // 按稀疏索引取 K 列的引擎。补的是一个结构性缺口：阵列每拍要 regWidth
    // 个新标量（S 是 128 位/拍），而上游的 SRAM 是单地址端口、每拍 64 位。
    //
    // **总容量固定为 2048 条目**，bank 数变而容量不变——否则测出来的差异里
    // 混着容量的影响，分不清是 bank 组织的功劳还是单纯装得多。
    // 容量固定也让列索引位宽恒为 11 位，激励文件可以跨配置复用。
    // 后缀 H = XOR 散列 bank 映射。实测取模映射会和 xm 的索引步长混叠，
    // 这一档用来量出散列能买回多少。
    case s if s.startsWith("KeyFeeder_SH") =>
      val banks = s.stripPrefix("KeyFeeder_SH").toInt
      () => new execute_unit.KeyFeeder(
        bits = Bits, point = Point, regWidth = 8,
        bankCount = banks, bankDepth = 2048 / banks, hashBanks = true)
    case s if s.startsWith("KeyFeeder_S") =>
      val banks = s.stripPrefix("KeyFeeder_S").toInt
      () => new execute_unit.KeyFeeder(
        bits = Bits, point = Point, regWidth = 8,
        bankCount = banks, bankDepth = 2048 / banks)
    case s if s.startsWith("KeyFeeder_L") =>
      val banks = s.stripPrefix("KeyFeeder_L").toInt
      () => new execute_unit.KeyFeeder(
        bits = Bits, point = Point, regWidth = 16,
        bankCount = banks, bankDepth = 2048 / banks)
    case "SRAMBank" => () => new execute_unit.SRAMBank(depth = 256, width = 64)
    case "SRAM" => () => new execute_unit.SRAM(bankCount = 4, bankDepth = 256, bankWidth = 64)

    case other => sys.error(s"no elaboration entry for '$other'")
  }

  // Every module the DynaX release actually contains, smallest first so a
  // datapath bug surfaces on a single PE before an array of 512 of them.
  private val All = Seq(
    "ExpUnit",
    "FixedPointDiv", "PSumSoftmax",
    "DivPipe1", "DivPipe4", "DivPipe8", "DivPipe12", "DivPipe24",
    "IndexScheduler", "IndexScheduler_S", "AttentionTile",
    "BlockSched_S0", "BlockSched_S2", "BlockSched_S4", "BlockSched_S8", "BlockSched_S16",
    "BlockSched_L0", "BlockSched_L2", "BlockSched_L4", "BlockSched_L8", "BlockSched_L16",
    "TopFirst", "TopK_S", "TopK",
    "SRAMBank", "SRAM",
    "KeyFeeder_S4", "KeyFeeder_S8", "KeyFeeder_S16", "KeyFeeder_S32",
    "KeyFeeder_SH4", "KeyFeeder_SH8", "KeyFeeder_SH16", "KeyFeeder_SH32",
    "KeyFeeder_L8", "KeyFeeder_L16", "KeyFeeder_L32",
    "PrePE_1_2", "PrePE_1_4", "PrePEArray_T", "PrePEArray14_T",
    "RePE", "RePERow", "RePEArray_T",
    "PrePEArray_S", "PrePEArray_L",
    "RePEArray_S", "RePEArray_L",
  )

  private val requested = if (args.length > 0) args(0) else "TopK"
  // "ALL" sweeps everything; "LIST:a,b,c" elaborates a caller-chosen set. The
  // list form exists so the verification job can elaborate exactly the targets
  // it is about to simulate, in one JVM, rather than paying JVM start and
  // Chisel's own warm-up once per module.
  private val targets =
    if (requested == "ALL") All
    else if (requested.startsWith("LIST:"))
      requested.stripPrefix("LIST:").split(",").map(_.trim).filter(_.nonEmpty).toSeq
    // "PLAN:k=v,..." 整个字符串就是一个目标——它描述的是一个设计，不是
    // 一个名字。输出目录用固定名 "Plan"，因为参数串里有逗号和等号。
    else Seq(requested)
  private val outRoot = if (args.length > 1) args(1) else "generated"

  // One JVM for the whole sweep, and one module's failure must not hide the
  // next module's result -- the point of the sweep is the full list.
  private val results = targets.map { t =>
    val started = System.nanoTime()
    val outcome =
      try {
        // One directory per target, not one shared directory: RePEArray_S and
        // RePEArray_L both elaborate to a module named RePEArray, so a shared
        // target-dir silently leaves only whichever ran last.
        val dir = if (t.startsWith("PLAN:")) "Plan" else t
        (new ChiselStage).execute(
          Array("--target-dir", s"$outRoot/$dir", "-X", "verilog"),
          Seq(ChiselGeneratorAnnotation(gen(t))),
        )
        "ok"
      } catch {
        case e: Throwable =>
          val msg = Option(e.getMessage).getOrElse(e.getClass.getName)
          "FAIL: " + msg.linesIterator.take(3).mkString(" | ")
      }
    val secs = (System.nanoTime() - started) / 1e9
    val shown = if (t.startsWith("PLAN:")) "Plan" else t
    println(f"ELABORATE $shown%-16s ${secs}%6.1fs  $outcome")
    (t, outcome)
  }

  println("=== elaboration summary ===")
  results.foreach { case (t, o) =>
    println(f"  ${if (t.startsWith("PLAN:")) "Plan" else t}%-16s $o")
  }
  private val failed = results.count(_._2 != "ok")
  println(s"${results.size - failed}/${results.size} modules elaborated")
  if (failed > 0) sys.exit(1)
}
