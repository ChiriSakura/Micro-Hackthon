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

  // 1. Unpack inputs into vectors for lane-wise processing
  val scores = VecInit((0 until 8).map(i => scores_in(9 * i + 8, 9 * i).asSInt))
  val weights = VecInit((0 until 8).map(i => weights_in(16 * i + 15, 16 * i)))
  val values = VecInit((0 until 8).map(i => v_in(8 * i + 7, 8 * i).asSInt))

  // 2. Calculate block sums (B0, B1) and total sum (S) of weights.
  // Use widening addition (+&) to ensure sums (up to 19 bits) do not overflow.
  val B0 = weights.slice(0, 4).reduce(_ +& _)
  val B1 = weights.slice(4, 8).reduce(_ +& _)
  val S = B0 +& B1

  // 3. X:M Selection Logic (t0_quarters=6, t1_quarters=2)
  // Comparisons are performed on widened values to prevent truncation.
  val S_times_6 = (S << 2) +& (S << 1)
  val S_times_2 = S << 1

  val B0_times_8 = B0 << 3
  val keep_count_0 = Mux(B0_times_8 > S_times_6, 2.U(2.W), Mux(B0_times_8 < S_times_2, 0.U(2.W), 1.U(2.W)))

  val B1_times_8 = B1 << 3
  val keep_count_1 = Mux(B1_times_8 > S_times_6, 2.U(2.W), Mux(B1_times_8 < S_times_2, 0.U(2.W), 1.U(2.W)))

  // 4. Top-2 Sorting Networks for each block
  // Helper for compare-and-swap, implementing the tie-breaking rule (smaller index wins).
  def compareAndSwap(scoreA: SInt, idxA: UInt, scoreB: SInt, idxB: UInt): ((SInt, UInt), (SInt, UInt)) = {
    val cond = scoreA > scoreB || (scoreA === scoreB && idxA < idxB)
    val top_s = Mux(cond, scoreA, scoreB)
    val top_i = Mux(cond, idxA, idxB)
    val bot_s = Mux(cond, scoreB, scoreA)
    val bot_i = Mux(cond, idxB, idxA)
    ((top_s, top_i), (bot_s, bot_i))
  }

  // Minimal Top-2 sorter for Block 0 (indices 0-3)
  val ((b0_s01_s, b0_s01_i), (b0_s10_s, b0_s10_i)) = compareAndSwap(scores(0), 0.U(3.W), scores(1), 1.U(3.W))
  val ((b0_s23_s, b0_s23_i), (b0_s32_s, b0_s32_i)) = compareAndSwap(scores(2), 2.U(3.W), scores(3), 3.U(3.W))
  val ((b0_top1_s, b0_top1_i), (b0_mid1_s, b0_mid1_i)) = compareAndSwap(b0_s01_s, b0_s01_i, b0_s23_s, b0_s23_i)
  val ((b0_mid2_s, b0_mid2_i), _)                      = compareAndSwap(b0_s10_s, b0_s10_i, b0_s32_s, b0_s32_i)
  val ((b0_top2_s, b0_top2_i), _)                      = compareAndSwap(b0_mid1_s, b0_mid1_i, b0_mid2_s, b0_mid2_i)
  val b0_top1_idx = b0_top1_i
  val b0_top2_idx = b0_top2_i

  // Minimal Top-2 sorter for Block 1 (indices 4-7)
  val ((b1_s45_s, b1_s45_i), (b1_s54_s, b1_s54_i)) = compareAndSwap(scores(4), 4.U(3.W), scores(5), 5.U(3.W))
  val ((b1_s67_s, b1_s67_i), (b1_s76_s, b1_s76_i)) = compareAndSwap(scores(6), 6.U(3.W), scores(7), 7.U(3.W))
  val ((b1_top1_s, b1_top1_i), (b1_mid1_s, b1_mid1_i)) = compareAndSwap(b1_s45_s, b1_s45_i, b1_s67_s, b1_s67_i)
  val ((b1_mid2_s, b1_mid2_i), _)                      = compareAndSwap(b1_s54_s, b1_s54_i, b1_s76_s, b1_s76_i)
  val ((b1_top2_s, b1_top2_i), _)                      = compareAndSwap(b1_mid1_s, b1_mid1_i, b1_mid2_s, b1_mid2_i)
  val b1_top1_idx = b1_top1_i
  val b1_top2_idx = b1_top2_i

  // 5. Generate keep_mask based on keep_counts and sorted indices
  val k = Wire(Vec(8, Bool()))
  for (i <- 0 until 4) {
    k(i) := (keep_count_0 > 0.U && b0_top1_idx === i.U) || (keep_count_0 > 1.U && b0_top2_idx === i.U)
  }
  for (i <- 4 until 8) {
    k(i) := (keep_count_1 > 0.U && b1_top1_idx === i.U) || (keep_count_1 > 1.U && b1_top2_idx === i.U)
  }
  keep_mask_out := k.asUInt

  // 6. Aggregate Numerator (N) and Denominator (D) based on the keep_mask
  val selected_weights = Wire(Vec(8, UInt(16.W)))
  // Product of 16u * 8s is 25s. Sum of 4 products is 27s.
  val selected_products = Wire(Vec(8, SInt(25.W)))

  for (i <- 0 until 8) {
    selected_weights(i) := Mux(k(i), weights(i), 0.U)
    val product = weights(i).zext * values(i)
    selected_products(i) := Mux(k(i), product, 0.S)
  }

  D_out := selected_weights.reduce(_ +& _)
  N_out := selected_products.reduce(_ +& _)
}
