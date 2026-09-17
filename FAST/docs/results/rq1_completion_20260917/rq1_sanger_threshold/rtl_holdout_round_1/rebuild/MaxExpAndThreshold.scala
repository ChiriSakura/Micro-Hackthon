import chisel3._
import chisel3.util._

class MaxExpAndThreshold extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_input = IO(Input(Bool()))
  val scores_in = IO(Input(UInt(144.W)))
  val valid_output = IO(Output(Bool()))
  val exponentials_out = IO(Output(UInt(256.W)))
  val keep_mask_out = IO(Output(UInt(16.W)))

  val exp_table_data = Seq(
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
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  ).map(_.U(16.W))
  val exp_rom = VecInit(exp_table_data)
  val THRESHOLD = 3.U

  withClockAndReset(clock, reset) {
    // --- Stage 0: Input deserialization ---
    val s0_scores = scores_in.asTypeOf(Vec(16, SInt(9.W)))

    // --- Stage 1 & 2: Max score reduction tree ---
    val s1_valid = RegNext(valid_input, false.B)
    val s1_scores = RegNext(s0_scores, VecInit(Seq.fill(16)(0.S(9.W))))

    val max_s1_comb = Wire(Vec(8, SInt(9.W)))
    for (i <- 0 until 8) {
      max_s1_comb(i) := Mux(s0_scores(2 * i) > s0_scores(2 * i + 1), s0_scores(2 * i), s0_scores(2 * i + 1))
    }
    val s1_max_level1 = RegNext(max_s1_comb, VecInit(Seq.fill(8)(0.S(9.W))))

    val s2_valid = RegNext(s1_valid, false.B)
    val s2_scores = RegNext(s1_scores, VecInit(Seq.fill(16)(0.S(9.W))))

    val max_s2_level2 = Wire(Vec(4, SInt(9.W)))
    for (i <- 0 until 4) {
      max_s2_level2(i) := Mux(s1_max_level1(2 * i) > s1_max_level1(2 * i + 1), s1_max_level1(2 * i), s1_max_level1(2 * i + 1))
    }
    val max_s2_level3 = Wire(Vec(2, SInt(9.W)))
    for (i <- 0 until 2) {
      max_s2_level3(i) := Mux(max_s2_level2(2 * i) > max_s2_level2(2 * i + 1), max_s2_level2(2 * i), max_s2_level2(2 * i + 1))
    }
    val h_comb = Mux(max_s2_level3(0) > max_s2_level3(1), max_s2_level3(0), max_s2_level3(1))
    val s2_h = RegNext(h_comb, 0.S(9.W))

    // --- Stage 3: Delta calculation ---
    val s3_valid = RegNext(s2_valid, false.B)
    val deltas_s3_comb = Wire(Vec(16, SInt(10.W)))
    for (i <- 0 until 16) {
      deltas_s3_comb(i) := s2_h - s2_scores(i)
    }
    val s3_deltas = RegNext(deltas_s3_comb, VecInit(Seq.fill(16)(0.S(10.W))))

    // --- Stage 4: EXP LUT lookup ---
    val s4_valid = RegNext(s3_valid, false.B)
    val exps_s4_comb = Wire(Vec(16, UInt(16.W)))
    for (i <- 0 until 16) {
      val delta = s3_deltas(i)
      val in_range = (delta >= 0.S) && (delta < 256.S)
      val addr = delta.asUInt
      exps_s4_comb(i) := Mux(in_range, exp_rom(addr), 0.U)
    }
    val s4_exps = RegNext(exps_s4_comb, VecInit(Seq.fill(16)(0.U(16.W))))

    // --- Stage 5 & 6: Sum reduction tree ---
    val s5_valid = RegNext(s4_valid, false.B)
    val s5_exps = RegNext(s4_exps, VecInit(Seq.fill(16)(0.U(16.W))))

    val sum_s5_comb = Wire(Vec(8, UInt(17.W)))
    for (i <- 0 until 8) {
      sum_s5_comb(i) := s4_exps(2 * i) +& s4_exps(2 * i + 1)
    }
    val s5_sum_level1 = RegNext(sum_s5_comb, VecInit(Seq.fill(8)(0.U(17.W))))

    val s6_valid = RegNext(s5_valid, false.B)
    val s6_exps = RegNext(s5_exps, VecInit(Seq.fill(16)(0.U(16.W))))

    val sum_s6_level2 = Wire(Vec(4, UInt(18.W)))
    for (i <- 0 until 4) {
      sum_s6_level2(i) := s5_sum_level1(2 * i) +& s5_sum_level1(2 * i + 1)
    }
    val sum_s6_level3 = Wire(Vec(2, UInt(19.W)))
    for (i <- 0 until 2) {
      sum_s6_level3(i) := sum_s6_level2(2 * i) +& sum_s6_level2(2 * i + 1)
    }
    val S_comb = sum_s6_level3(0) +& sum_s6_level3(1)
    val s6_S = RegNext(S_comb, 0.U(20.W))

    // --- Stage 7: Thresholding ---
    val s7_valid = RegNext(s6_valid, false.B)
    val s7_exps = RegNext(s6_exps, VecInit(Seq.fill(16)(0.U(16.W))))
    val s7_S = RegNext(s6_S, 0.U(20.W))

    val threshold_val = s7_S * THRESHOLD
    val keep_mask_vec = Wire(Vec(16, Bool()))
    for (i <- 0 until 16) {
      val scaled_exp = s7_exps(i) << 8
      keep_mask_vec(i) := scaled_exp > threshold_val
    }

    // --- Outputs ---
    valid_output := s7_valid
    exponentials_out := s7_exps.asUInt
    keep_mask_out := keep_mask_vec.asUInt
  }
}
