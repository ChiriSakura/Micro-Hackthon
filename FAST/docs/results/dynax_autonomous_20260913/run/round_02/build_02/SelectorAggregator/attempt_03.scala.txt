import chisel3._
import chisel3.util._

class SelectorAggregator extends RawModule {
  // IO ports as specified in the system plan
  val scores_in = IO(Input(UInt(72.W)))
  val weights_in = IO(Input(UInt(128.W)))
  val v_in = IO(Input(UInt(64.W)))
  val N_out = IO(Output(SInt(27.W)))
  val D_out = IO(Output(UInt(19.W)))
  val keep_mask_out = IO(Output(UInt(8.W)))

  // 1. Unpack inputs
  val s = VecInit(Seq.tabulate(8)(i => scores_in(9 * i + 8, 9 * i).asSInt))
  val e = VecInit(Seq.tabulate(8)(i => weights_in(16 * i + 15, 16 * i)))
  val v = VecInit(Seq.tabulate(8)(i => v_in(8 * i + 7, 8 * i).asSInt))
  val i_const = Seq.tabulate(8)(_.U(3.W))

  // 2. Calculate block sums and total sum
  val B0 = e.slice(0, 4).reduce(_ +& _) // 18-bit
  val B1 = e.slice(4, 8).reduce(_ +& _) // 18-bit
  val S = B0 +& B1                     // 19-bit

  // 3. X:M Selection Logic (t0_quarters=6, t1_quarters=2)
  // Widen to 25 bits to avoid overflow during multiplication, as diagnosed.
  val B0_wide = B0.pad(25)
  val B1_wide = B1.pad(25)
  val S_wide = S.pad(25)

  val S_times_6 = (S_wide << 2) + S_wide
  val S_times_2 = S_wide << 1

  val B0_times_8 = B0_wide << 3
  val keep_count_0 = Mux(B0_times_8 > (S_wide * 6.U), 2.U(2.W), Mux(B0_times_8 < (S_wide * 2.U), 0.U(2.W), 1.U(2.W)))

  val B1_times_8 = B1_wide << 3
  val keep_count_1 = Mux(B1_times_8 > (S_wide * 6.U), 2.U(2.W), Mux(B1_times_8 < (S_wide * 2.U), 0.U(2.W), 1.U(2.W)))

  // 4. Top-2 Sorting Networks (from behavior spec)
  // Block 0 Sorter (indices 0-3)
  val b0_c01 = s(0) > s(1) || (s(0) === s(1) && i_const(0) < i_const(1))
  val b0_s01_s = Mux(b0_c01, s(0), s(1)); val b0_s01_i = Mux(b0_c01, i_const(0), i_const(1))
  val b0_s10_s = Mux(b0_c01, s(1), s(0)); val b0_s10_i = Mux(b0_c01, i_const(1), i_const(0))

  val b0_c23 = s(2) > s(3) || (s(2) === s(3) && i_const(2) < i_const(3))
  val b0_s23_s = Mux(b0_c23, s(2), s(3)); val b0_s23_i = Mux(b0_c23, i_const(2), i_const(3))
  val b0_s32_s = Mux(b0_c23, s(3), s(2)); val b0_s32_i = Mux(b0_c23, i_const(3), i_const(2))

  val b0_c02 = b0_s01_s > b0_s23_s || (b0_s01_s === b0_s23_s && b0_s01_i < b0_s23_i)
  val b0_s02_s = Mux(b0_c02, b0_s01_s, b0_s23_s); val b0_s02_i = Mux(b0_c02, b0_s01_i, b0_s23_i)
  val b0_s20_s = Mux(b0_c02, b0_s23_s, b0_s01_s); val b0_s20_i = Mux(b0_c02, b0_s23_i, b0_s01_i)

  val b0_c13 = b0_s10_s > b0_s32_s || (b0_s10_s === b0_s32_s && b0_s10_i < b0_s32_i)
  val b0_s13_s = Mux(b0_c13, b0_s10_s, b0_s32_s); val b0_s13_i = Mux(b0_c13, b0_s10_i, b0_s32_i)

  val b0_c12 = b0_s20_s > b0_s13_s || (b0_s20_s === b0_s13_s && b0_s20_i < b0_s13_i)
  val b0_s12_s = Mux(b0_c12, b0_s20_s, b0_s13_s); val b0_s12_i = Mux(b0_c12, b0_s20_i, b0_s13_i)

  val b0_top1_idx = b0_s02_i
  val b0_top2_idx = b0_s12_i

  // Block 1 Sorter (indices 4-7)
  val b1_c45 = s(4) > s(5) || (s(4) === s(5) && i_const(4) < i_const(5))
  val b1_s45_s = Mux(b1_c45, s(4), s(5)); val b1_s45_i = Mux(b1_c45, i_const(4), i_const(5))
  val b1_s54_s = Mux(b1_c45, s(5), s(4)); val b1_s54_i = Mux(b1_c45, i_const(5), i_const(4))

  val b1_c67 = s(6) > s(7) || (s(6) === s(7) && i_const(6) < i_const(7))
  val b1_s67_s = Mux(b1_c67, s(6), s(7)); val b1_s67_i = Mux(b1_c67, i_const(6), i_const(7))
  val b1_s76_s = Mux(b1_c67, s(7), s(6)); val b1_s76_i = Mux(b1_c67, i_const(7), i_const(6))

  val b1_c46 = b1_s45_s > b1_s67_s || (b1_s45_s === b1_s67_s && b1_s45_i < b1_s67_i)
  val b1_s46_s = Mux(b1_c46, b1_s45_s, b1_s67_s); val b1_s46_i = Mux(b1_c46, b1_s45_i, b1_s67_i)
  val b1_s64_s = Mux(b1_c46, b1_s67_s, b1_s45_s); val b1_s64_i = Mux(b1_c46, b1_s67_i, b1_s45_i)

  val b1_c57 = b1_s54_s > b1_s76_s || (b1_s54_s === b1_s76_s && b1_s54_i < b1_s76_i)
  val b1_s57_s = Mux(b1_c57, b1_s54_s, b1_s76_s); val b1_s57_i = Mux(b1_c57, b1_s54_i, b1_s76_i)

  val b1_c56 = b1_s64_s > b1_s57_s || (b1_s64_s === b1_s57_s && b1_s64_i < b1_s57_i)
  val b1_s56_s = Mux(b1_c56, b1_s64_s, b1_s57_s); val b1_s56_i = Mux(b1_c56, b1_s64_i, b1_s57_i)

  val b1_top1_idx = b1_s46_i
  val b1_top2_idx = b1_s56_i

  // 5. Generate keep_mask
  val k = Wire(Vec(8, Bool()))
  for (j <- 0 until 4) {
    k(j) := (keep_count_0 > 0.U && b0_top1_idx === j.U) || (keep_count_0 > 1.U && b0_top2_idx === j.U)
  }
  for (j <- 4 until 8) {
    k(j) := (keep_count_1 > 0.U && b1_top1_idx === j.U) || (keep_count_1 > 1.U && b1_top2_idx === j.U)
  }
  keep_mask_out := k.asUInt

  // 6. Aggregate Numerator (N) and Denominator (D)
  val N_terms = Wire(Vec(8, SInt(25.W)))
  val D_terms = Wire(Vec(8, UInt(16.W)))

  for (j <- 0 until 8) {
    // Product of UInt(16).zext (SInt(17)) and SInt(8) is SInt(25).
    val product = e(j).zext * v(j)
    N_terms(j) := Mux(k(j), product, 0.S(25.W))
    D_terms(j) := Mux(k(j), e(j), 0.U(16.W))
  }

  // Sum of up to 4x 25-bit N_terms fits in 27 bits. Sum of up to 8x 16-bit D_terms fits in 19 bits.
  N_out := N_terms.reduce(_ +& _)
  D_out := D_terms.reduce(_ +& _)
}
