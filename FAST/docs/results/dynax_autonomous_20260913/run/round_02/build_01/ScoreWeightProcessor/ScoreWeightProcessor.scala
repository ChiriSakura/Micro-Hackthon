import chisel3._
import chisel3.util._

class ScoreWeightProcessor extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(64.W)))
  val valid_out = IO(Output(Bool()))
  val scores_out = IO(Output(UInt(72.W)))
  val weights_out = IO(Output(UInt(128.W)))

  // ROM initialized from the packed hex string in the algorithm contract.
  // The string packs values from index 255 down to 0.
  // We extract them assuming little-endian packing (index 0 at LSBs).
  val expTablePacked = BigInt("10001000100010001000100010001000100010001000100010001000100010001000100020002000200020002000200020002000300030003000300030004000400040004000500050005000600060006000700070008000800090009000a000a000b000c000d000d000e000f00100011001200130015001600170019001b001c001e00200022002400270029002c002f003200350038003c004000440048004d00520057005d0063006900700077007f0087008f009900a200ad00b800c400d100de00ec00fc010c011d012f01430158016e0186019f01ba01d601f402150237025c028202ac02d803070339036e03a703e30423046804b004fe055005a80605066906d2074307bb083b08c2095309ed0a910b3f0bf90cbf0d910e710f60105e116c128b13be1503165e17d019591afb1cb91e93208c22a524e1274229ca2c7c2f5b326935a9391f3cce40ba44e749584e13531c58785e2d64406ab7719978ed80b9890691dd9b45a549aff2bb4ac75fd43ae1eaf07cffff", 16)
  val expTable = VecInit(Seq.tabulate(256) { i =>
    ((expTablePacked >> (i * 16)) & 0xFFFFL).U(16.W)
  })

  // 3-stage pipeline valid signal propagation
  val valid_s1 = withClockAndReset(clock, reset) { RegNext(valid_in, false.B) }
  val valid_s2 = withClockAndReset(clock, reset) { RegNext(valid_s1, false.B) }
  valid_out := withClockAndReset(clock, reset) { RegNext(valid_s2, false.B) }

  // Stage 0: Score calculation (combinational logic)
  val q0 = q_in(3, 0).asSInt
  val q1 = q_in(7, 4).asSInt
  
  val scores_s0 = Wire(Vec(8, SInt(9.W)))
  for (i <- 0 until 8) {
    val k0 = k_in(i * 8 + 3, i * 8 + 0).asSInt
    val k1 = k_in(i * 8 + 7, i * 8 + 4).asSInt
    scores_s0(i) := (q0 * k0) +& (q1 * k1)
  }

  // Pipeline Register: Stage 0 -> 1
  val scores_s1 = withClockAndReset(clock, reset) {
    RegEnable(scores_s0.asUInt, 0.U((9 * 8).W), valid_in)
  }.asTypeOf(Vec(8, SInt(9.W)))

  // Stage 1: Max score and deltas (combinational logic)
  val h = scores_s1.reduce((a, b) => Mux(a > b, a, b))
  
  val deltas_s1 = Wire(Vec(8, UInt(8.W)))
  for (i <- 0 until 8) {
    deltas_s1(i) := (h - scores_s1(i)).asUInt(7, 0)
  }

  // Pipeline Registers: Stage 1 -> 2
  val scores_s2 = withClockAndReset(clock, reset) {
    RegEnable(scores_s1.asUInt, 0.U((9 * 8).W), valid_s1)
  }.asTypeOf(Vec(8, SInt(9.W)))
  
  val deltas_s2 = withClockAndReset(clock, reset) {
    RegEnable(deltas_s1.asUInt, 0.U((8 * 8).W), valid_s1)
  }.asTypeOf(Vec(8, UInt(8.W)))

  // Stage 2: Weight lookup (combinational logic using ROM)
  val weights_s2 = Wire(Vec(8, UInt(16.W)))
  for (i <- 0 until 8) {
    weights_s2(i) := expTable(deltas_s2(i))
  }

  // Pipeline Registers: Stage 2 -> 3 (Output Registers)
  val scores_out_reg = withClockAndReset(clock, reset) {
    RegEnable(scores_s2.asUInt, 0.U((9 * 8).W), valid_s2)
  }
  
  val weights_out_reg = withClockAndReset(clock, reset) {
    RegEnable(weights_s2.asUInt, 0.U((16 * 8).W), valid_s2)
  }

  // Connect outputs
  scores_out := scores_out_reg
  weights_out := weights_out_reg
}
