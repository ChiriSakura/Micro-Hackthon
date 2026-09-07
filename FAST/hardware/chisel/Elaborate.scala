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

  private def gen(target: String): () => chisel3.RawModule = target match {
    // ---- exponential unit (FAST reconstruction, see exp_unit.scala) --------
    case "ExpUnit" =>
      () => new exp_unit.ExpUnitFixPoint(Bits, Point, intBits = 6, fracBits = 4)

    // ---- predict unit -----------------------------------------------------
    case "TopK" => () => new predict_unit.TopK(m = 64, n = 16, bits = Bits, point = Point)
    case "TopK_S" => () => new predict_unit.TopK(m = 32, n = 8, bits = Bits, point = Point)
    case "TopFirst" =>
      () => new predict_unit.TopFirst(bits = Bits, point = Point, idxBits = 6, depth = 64)
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
    "TopFirst", "TopK_S", "TopK",
    "SRAMBank", "SRAM",
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
        (new ChiselStage).execute(
          Array("--target-dir", s"$outRoot/$t", "-X", "verilog"),
          Seq(ChiselGeneratorAnnotation(gen(t))),
        )
        "ok"
      } catch {
        case e: Throwable =>
          val msg = Option(e.getMessage).getOrElse(e.getClass.getName)
          "FAIL: " + msg.linesIterator.take(3).mkString(" | ")
      }
    val secs = (System.nanoTime() - started) / 1e9
    println(f"ELABORATE $t%-16s ${secs}%6.1fs  $outcome")
    (t, outcome)
  }

  println("=== elaboration summary ===")
  results.foreach { case (t, o) => println(f"  $t%-16s $o") }
  private val failed = results.count(_._2 != "ok")
  println(s"${results.size - failed}/${results.size} modules elaborated")
  if (failed > 0) sys.exit(1)
}
