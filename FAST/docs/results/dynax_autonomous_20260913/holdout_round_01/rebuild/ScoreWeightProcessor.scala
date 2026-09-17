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

  // The exp_table is implemented as a 256-entry ROM with 16-bit values.
  // Initialized directly from the integer array to avoid string parsing issues.
  val expTable = VecInit(Seq(
    65535.U(16.W), 61564.U(16.W), 57834.U(16.W), 54330.U(16.W), 51039.U(16.W), 47946.U(16.W), 45042.U(16.W), 42313.U(16.W),
    39749.U(16.W), 37341.U(16.W), 35078.U(16.W), 32953.U(16.W), 30957.U(16.W), 29081.U(16.W), 27319.U(16.W), 25664.U(16.W),
    24109.U(16.W), 22648.U(16.W), 21276.U(16.W), 19987.U(16.W), 18776.U(16.W), 17639.U(16.W), 16570.U(16.W), 15566.U(16.W),
    14623.U(16.W), 13737.U(16.W), 12905.U(16.W), 12123.U(16.W), 11388.U(16.W), 10698.U(16.W), 10050.U(16.W), 9441.U(16.W),
    8869.U(16.W), 8332.U(16.W), 7827.U(16.W), 7353.U(16.W), 6907.U(16.W), 6489.U(16.W), 6096.U(16.W), 5726.U(16.W),
    5379.U(16.W), 5054.U(16.W), 4747.U(16.W), 4460.U(16.W), 4190.U(16.W), 3936.U(16.W), 3697.U(16.W), 3473.U(16.W),
    3263.U(16.W), 3065.U(16.W), 2879.U(16.W), 2705.U(16.W), 2541.U(16.W), 2387.U(16.W), 2242.U(16.W), 2107.U(16.W),
    1979.U(16.W), 1859.U(16.W), 1746.U(16.W), 1641.U(16.W), 1541.U(16.W), 1448.U(16.W), 1360.U(16.W), 1278.U(16.W),
    1200.U(16.W), 1128.U(16.W), 1059.U(16.W), 995.U(16.W), 935.U(16.W), 878.U(16.W), 825.U(16.W), 775.U(16.W),
    728.U(16.W), 684.U(16.W), 642.U(16.W), 604.U(16.W), 567.U(16.W), 533.U(16.W), 500.U(16.W), 470.U(16.W),
    442.U(16.W), 415.U(16.W), 390.U(16.W), 366.U(16.W), 344.U(16.W), 323.U(16.W), 303.U(16.W), 285.U(16.W),
    268.U(16.W), 252.U(16.W), 236.U(16.W), 222.U(16.W), 209.U(16.W), 196.U(16.W), 184.U(16.W), 173.U(16.W),
    162.U(16.W), 153.U(16.W), 143.U(16.W), 135.U(16.W), 127.U(16.W), 119.U(16.W), 112.U(16.W), 105.U(16.W),
    99.U(16.W), 93.U(16.W), 87.U(16.W), 82.U(16.W), 77.U(16.W), 72.U(16.W), 68.U(16.W), 64.U(16.W),
    60.U(16.W), 56.U(16.W), 53.U(16.W), 50.U(16.W), 47.U(16.W), 44.U(16.W), 41.U(16.W), 39.U(16.W),
    36.U(16.W), 34.U(16.W), 32.U(16.W), 30.U(16.W), 28.U(16.W), 27.U(16.W), 25.U(16.W), 23.U(16.W),
    22.U(16.W), 21.U(16.W), 19.U(16.W), 18.U(16.W), 17.U(16.W), 16.U(16.W), 15.U(16.W), 14.U(16.W),
    13.U(16.W), 13.U(16.W), 12.U(16.W), 11.U(16.W), 10.U(16.W), 10.U(16.W), 9.U(16.W), 9.U(16.W),
    8.U(16.W), 8.U(16.W), 7.U(16.W), 7.U(16.W), 6.U(16.W), 6.U(16.W), 6.U(16.W), 5.U(16.W),
    5.U(16.W), 5.U(16.W), 4.U(16.W), 4.U(16.W), 4.U(16.W), 4.U(16.W), 3.U(16.W), 3.U(16.W),
    3.U(16.W), 3.U(16.W), 3.U(16.W), 2.U(16.W), 2.U(16.W), 2.U(16.W), 2.U(16.W), 2.U(16.W),
    2.U(16.W), 2.U(16.W), 2.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W),
    1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W),
    1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
    0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W)
  ))

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
    val p0 = q0 * k0
    val p1 = q1 * k1
    scores_s0(i) := p0 +& p1
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
