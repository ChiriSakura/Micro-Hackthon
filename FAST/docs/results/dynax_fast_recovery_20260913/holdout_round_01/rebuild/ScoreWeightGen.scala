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
    // Stage 1: Input Latching (registers values for use in Stage 2)
    val valid_p1 = RegNext(start, false.B)
    val q_p1 = RegNext(q_in, 0.U)
    val k_p1 = RegNext(k_in, 0.U)

    // Stage 2: Score Calculation
    // Combinational logic for score computation
    val scores_s2_comb = Wire(Vec(8, SInt(9.W)))
    val q0 = q_p1(3, 0).asSInt
    val q1 = q_p1(7, 4).asSInt
    for (i <- 0 until 8) {
      val k_i0 = k_p1(4 * (2 * i + 0) + 3, 4 * (2 * i + 0)).asSInt
      val k_i1 = k_p1(4 * (2 * i + 1) + 3, 4 * (2 * i + 1)).asSInt
      // Use widening add (+&) to produce a 9-bit sum from two 8-bit products, preventing overflow.
      scores_s2_comb(i) := (q0 * k_i0) +& (q1 * k_i1)
    }

    // Stage 2 registers
    val valid_p2 = RegNext(valid_p1, false.B)
    val scores_p2 = RegInit(VecInit(Seq.fill(8)(0.S(9.W))))
    when(valid_p1) {
      scores_p2 := scores_s2_comb
    }

    // Stage 3: Weight Calculation
    // Combinational logic for weight computation
    val weights_s3_comb = Wire(Vec(8, UInt(16.W)))
    val max_score = scores_p2.reduce((a, b) => Mux(a > b, a, b))
    for (i <- 0 until 8) {
      val delta = (max_score - scores_p2(i)).asUInt
      weights_s3_comb(i) := exp_table(delta(7, 0))
    }

    // Stage 3 registers
    val valid_p3_reg = RegNext(valid_p2, false.B)
    val scores_p3_reg = RegInit(0.U(72.W))
    val weights_p3_reg = RegInit(0.U(128.W))
    when(valid_p2) {
      scores_p3_reg := Cat(scores_p2.map(_.asUInt).reverse)
      weights_p3_reg := Cat(weights_s3_comb.reverse)
    }

    // Outputs
    scores_out := scores_p3_reg
    weights_out := weights_p3_reg
    valid_out := valid_p3_reg
  }
}
