import chisel3._
import chisel3.util._

class ScoreWeightGen extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(64.W)))
  val scores_out = IO(Output(UInt(72.W)))
  val weights_out = IO(Output(UInt(128.W)))
  val valid_out = IO(Output(Bool()))

  val exp_table = VecInit(Seq(
    65535, 61564, 57834, 54330, 51039, 47946, 45042, 42313, 39749, 37341, 35078, 32953, 30957, 29081, 27319, 25664,
    24109, 22648, 21276, 19987, 18776, 17639, 16570, 15566, 14623, 13737, 12905, 12123, 11388, 10698, 10050, 9441,
    8869, 8332, 7827, 7353, 6907, 6489, 6096, 5726, 5379, 5054, 4747, 4460, 4190, 3936, 3697, 3473, 3263, 3065,
    2879, 2705, 2541, 2387, 2242, 2107, 1979, 1859, 1746, 1641, 1541, 1448, 1360, 1278, 1200, 1128, 1059, 995,
    935, 878, 825, 775, 728, 684, 642, 604, 567, 533, 500, 470, 442, 415, 390, 366, 344, 323, 303, 285,
    268, 252, 236, 222, 209, 196, 184, 173, 162, 153, 143, 135, 127, 119, 112, 105, 99, 93, 87, 82,
    77, 72, 68, 64, 60, 56, 53, 50, 47, 44, 41, 39, 36, 34, 32, 30, 28, 27, 25, 23, 22, 21,
    19, 18, 17, 16, 15, 14, 13, 13, 12, 11, 10, 10, 9, 9, 8, 8, 7, 7, 6, 6, 6, 5,
    5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  ).map(_.U(16.W)))

  withClockAndReset(clock, reset) {
    // Pipeline valid signal propagation for 3-cycle latency
    val valid_s1 = RegNext(start, false.B)
    val valid_s2 = RegNext(valid_s1, false.B)
    val valid_s3 = RegNext(valid_s2, false.B)

    // Stage 1: Input Latching
    // On a start pulse, latch the inputs.
    val q_s1 = RegEnable(q_in, 0.U(8.W), start)
    val k_s1 = RegEnable(k_in, 0.U(64.W), start)

    // Stage 2: Score Calculation
    // This stage's logic is combinational, fed by stage 1 registers.
    // The results are latched into stage 2 registers, enabled by valid_s1.
    val q0 = q_s1(3, 0).asSInt
    val q1 = q_s1(7, 4).asSInt
    
    val scores_s2_comb = Wire(Vec(8, SInt(9.W)))
    for (i <- 0 until 8) {
      val k_i0 = k_s1(4 * (2 * i + 0) + 3, 4 * (2 * i + 0)).asSInt
      val k_i1 = k_s1(4 * (2 * i + 1) + 3, 4 * (2 * i + 1)).asSInt
      scores_s2_comb(i) := (q0 * k_i0) +& (q1 * k_i1)
    }

    val scores_s2_reg = RegEnable(scores_s2_comb, VecInit(Seq.fill(8)(0.S(9.W))), valid_s1)

    // Stage 3: Weight Calculation
    // This stage's logic is combinational, fed by stage 2 registers.
    // The results are latched into stage 3 registers, enabled by valid_s2.
    val max_score = scores_s2_reg.reduceTree((a, b) => Mux(a > b, a, b))
    
    val weights_s3_comb = Wire(Vec(8, UInt(16.W)))
    for (i <- 0 until 8) {
      val delta = (max_score - scores_s2_reg(i)).asUInt
      weights_s3_comb(i) := exp_table(delta(7, 0))
    }

    // Stage 3 Output Registers
    val scores_out_reg = RegEnable(Cat(scores_s2_reg.map(_.asUInt).reverse), 0.U(72.W), valid_s2)
    val weights_out_reg = RegEnable(Cat(weights_s3_comb.reverse), 0.U(128.W), valid_s2)

    // Assign outputs from final stage registers
    scores_out := scores_out_reg
    weights_out := weights_out_reg
    valid_out := valid_s3
  }
}
