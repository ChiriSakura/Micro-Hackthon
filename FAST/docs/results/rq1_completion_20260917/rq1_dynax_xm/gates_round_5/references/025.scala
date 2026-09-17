import chisel3._
import chisel3.util._

class ScoreAndExpUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(128.W)))
  val scores_out = IO(Output(UInt(144.W)))
  val exponentials_out = IO(Output(UInt(256.W)))
  val valid_out = IO(Output(Bool()))

  withClockAndReset(clock, reset) {
    // EXP Table ROM from algorithm contract, padded to 256 entries
    val exp_rom = VecInit(Seq(
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
      1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W)
    ) ++ Seq.fill(256 - 203)(0.U(16.W)))

    // --- Stage 1: Score Calculation (Combinational) ---
    val q = Wire(Vec(2, SInt(4.W)))
    q(0) := q_in(3, 0).asSInt
    q(1) := q_in(7, 4).asSInt

    val k = Wire(Vec(16, Vec(2, SInt(4.W))))
    for (i <- 0 until 16) {
      k(i)(0) := k_in(8 * i + 3, 8 * i + 0).asSInt
      k(i)(1) := k_in(8 * i + 7, 8 * i + 4).asSInt
    }

    val scores_s1_w = Wire(Vec(16, SInt(9.W)))
    for (i <- 0 until 16) {
      scores_s1_w(i) := (q(0) * k(i)(0)) +& (q(1) * k(i)(1))
    }
    
    val scores_s2_r = RegNext(scores_s1_w, VecInit(Seq.fill(16)(0.S(9.W))))

    // --- Stages 2-5: Pipelined Max Score Calculation ---
    val scores_s3_r = RegNext(scores_s2_r, VecInit(Seq.fill(16)(0.S(9.W))))
    val max_s2_w = Wire(Vec(8, SInt(9.W)))
    for (i <- 0 until 8) { max_s2_w(i) := Mux(scores_s2_r(2 * i) > scores_s2_r(2 * i + 1), scores_s2_r(2 * i), scores_s2_r(2 * i + 1)) }
    val max_s3_r = RegNext(max_s2_w, VecInit(Seq.fill(8)(0.S(9.W))))

    val scores_s4_r = RegNext(scores_s3_r, VecInit(Seq.fill(16)(0.S(9.W))))
    val max_s3_w = Wire(Vec(4, SInt(9.W)))
    for (i <- 0 until 4) { max_s3_w(i) := Mux(max_s3_r(2 * i) > max_s3_r(2 * i + 1), max_s3_r(2 * i), max_s3_r(2 * i + 1)) }
    val max_s4_r = RegNext(max_s3_w, VecInit(Seq.fill(4)(0.S(9.W))))

    val scores_s5_r = RegNext(scores_s4_r, VecInit(Seq.fill(16)(0.S(9.W))))
    val max_s4_w = Wire(Vec(2, SInt(9.W)))
    for (i <- 0 until 2) { max_s4_w(i) := Mux(max_s4_r(2 * i) > max_s4_r(2 * i + 1), max_s4_r(2 * i), max_s4_r(2 * i + 1)) }
    val max_s5_r = RegNext(max_s4_w, VecInit(Seq.fill(2)(0.S(9.W))))

    val scores_s6_r = RegNext(scores_s5_r, VecInit(Seq.fill(16)(0.S(9.W))))
    val h_s5_w = Mux(max_s5_r(0) > max_s5_r(1), max_s5_r(0), max_s5_r(1))
    val h_s6_r = RegNext(h_s5_w, 0.S(9.W))

    // --- Stage 6: Delta Calculation ---
    val scores_s7_r = RegNext(scores_s6_r, VecInit(Seq.fill(16)(0.S(9.W))))
    val deltas_s6_w = Wire(Vec(16, UInt(8.W)))
    for (i <- 0 until 16) {
      deltas_s6_w(i) := (h_s6_r - scores_s6_r(i))(7, 0)
    }
    val deltas_s7_r = RegNext(deltas_s6_w, VecInit(Seq.fill(16)(0.U(8.W))))

    // --- Stage 7: EXP Lookup & Output ---
    val exponentials_s7_w = Wire(Vec(16, UInt(16.W)))
    for (i <- 0 until 16) {
      exponentials_s7_w(i) := exp_rom(deltas_s7_r(i))
    }
    
    val scores_out_r = RegNext(scores_s7_r, VecInit(Seq.fill(16)(0.S(9.W))))
    val exponentials_out_r = RegNext(exponentials_s7_w, VecInit(Seq.fill(16)(0.U(16.W))))

    // --- Valid Signal Pipeline (7 stages) ---
    valid_out := (0 until 7).foldLeft(valid_in)((v, _) => RegNext(v, false.B))

    // --- Output Assignment ---
    scores_out := scores_out_r.asUInt
    exponentials_out := exponentials_out_r.asUInt
  }
}
