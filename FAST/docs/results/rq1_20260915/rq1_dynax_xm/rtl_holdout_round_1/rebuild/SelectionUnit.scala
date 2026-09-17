import chisel3._
import chisel3.util._

// Internal helper type for sorting.
// It holds the composite key (for sorting) and the original index (for mask generation).
class SorterItem extends Bundle {
  // Composite key: 9-bit score (MSB) and 4-bit tie-breaker (LSB).
  // The key is signed to handle negative scores correctly.
  val key = SInt(13.W)
  // Original index within the 8-element block (0-7).
  val index = UInt(3.W)
}

class SelectionUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val scores_in = IO(Input(UInt(144.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val keep_mask_out = IO(Output(UInt(16.W)))
  val exponentials_out = IO(Output(UInt(256.W)))
  val valid_out = IO(Output(Bool()))

  withClockAndReset(clock, reset) {

    // --- Pipeline passthrough for valid and exponentials (10 stages) ---
    // Use ShiftRegister with resetData to ensure registers are cleared on reset.
    valid_out := ShiftRegister(valid_in, 10, false.B, true.B)
    exponentials_out := ShiftRegister(exponentials_in, 10, 0.U.asTypeOf(exponentials_in), true.B)

    // --- Stage 0: Input Unpacking (Combinational) ---
    val scores = scores_in.asTypeOf(Vec(16, SInt(9.W)))
    val exponentials = exponentials_in.asTypeOf(Vec(16, UInt(16.W)))

    // --- Summation Pipeline (Stages 1-4) ---
    // All RegNext calls now include a reset value.
    val sum0_s1_next = VecInit((0 until 4).map(i => exponentials(2 * i) +& exponentials(2 * i + 1)))
    val sum1_s1_next = VecInit((0 until 4).map(i => exponentials(8 + 2 * i) +& exponentials(8 + 2 * i + 1)))
    val sum0_s1 = RegNext(sum0_s1_next, 0.U.asTypeOf(sum0_s1_next))
    val sum1_s1 = RegNext(sum1_s1_next, 0.U.asTypeOf(sum1_s1_next))
    
    val sum0_s2_next = VecInit((0 until 2).map(i => sum0_s1(2 * i) +& sum0_s1(2 * i + 1)))
    val sum1_s2_next = VecInit((0 until 2).map(i => sum1_s1(2 * i) +& sum1_s1(2 * i + 1)))
    val sum0_s2 = RegNext(sum0_s2_next, 0.U.asTypeOf(sum0_s2_next))
    val sum1_s2 = RegNext(sum1_s2_next, 0.U.asTypeOf(sum1_s2_next))
    
    val B0_s3 = RegNext(sum0_s2(0) +& sum0_s2(1), 0.U(19.W))
    val B1_s3 = RegNext(sum1_s2(0) +& sum1_s2(1), 0.U(19.W))
    
    val S_s4 = RegNext(B0_s3 +& B1_s3, 0.U(20.W))
    val B0_s4 = RegNext(B0_s3, 0.U(19.W))
    val B1_s4 = RegNext(B1_s3, 0.U(19.W))

    // --- k-Determination Pipeline (Stage 5) ---
    val k0_s5 = RegNext(Mux((B0_s4 << 1) > S_s4, 7.U(4.W), 6.U(4.W)), 0.U(4.W))
    val k1_s5 = RegNext(Mux((B1_s4 << 1) > S_s4, 7.U(4.W), 6.U(4.W)), 0.U(4.W))

    // --- Sorter Pipeline (Stages 1-6) ---
    
    def compareAndSwap(a: SorterItem, b: SorterItem): (SorterItem, SorterItem) = {
      val greater = a.key > b.key
      val sorted_a = Mux(greater, a, b)
      val sorted_b = Mux(greater, b, a)
      (sorted_a, sorted_b)
    }

    def sortingNetworkStage(items: Vec[SorterItem], pairs: Seq[(Int, Int)]): Vec[SorterItem] = {
      val next_items = Wire(Vec(8, new SorterItem))
      next_items := items
      for ((i, j) <- pairs) {
        val (sorted_i, sorted_j) = compareAndSwap(items(i), items(j))
        next_items(i) := sorted_i
        next_items(j) := sorted_j
      }
      next_items
    }

    val block0_items_in = Wire(Vec(8, new SorterItem))
    val block1_items_in = Wire(Vec(8, new SorterItem))
    for (i <- 0 until 8) {
      val global_idx0 = i.U(4.W)
      val global_idx1 = (i + 8).U(4.W)
      block0_items_in(i).key   := Cat(scores(i).asUInt, 15.U(4.W) - global_idx0).asSInt
      block0_items_in(i).index := i.U(3.W)
      block1_items_in(i).key   := Cat(scores(i + 8).asUInt, 15.U(4.W) - global_idx1).asSInt
      block1_items_in(i).index := i.U(3.W)
    }
    
    val s1_pairs = Seq((0, 1), (2, 3), (4, 5), (6, 7))
    val s2_pairs = Seq((0, 2), (1, 3), (4, 6), (5, 7))
    val s3_pairs = Seq((1, 2), (5, 6))
    val s4_pairs = Seq((0, 4), (1, 5), (2, 6), (3, 7))
    val s5_pairs = Seq((2, 4), (3, 5))
    val s6_pairs = Seq((1, 2), (3, 4), (5, 6))

    val sorter_reset_val = 0.U.asTypeOf(Vec(8, new SorterItem))

    val s1_out0 = RegNext(sortingNetworkStage(block0_items_in, s1_pairs), sorter_reset_val)
    val s2_out0 = RegNext(sortingNetworkStage(s1_out0, s2_pairs), sorter_reset_val)
    val s3_out0 = RegNext(sortingNetworkStage(s2_out0, s3_pairs), sorter_reset_val)
    val s4_out0 = RegNext(sortingNetworkStage(s3_out0, s4_pairs), sorter_reset_val)
    val s5_out0 = RegNext(sortingNetworkStage(s4_out0, s5_pairs), sorter_reset_val)
    val sorted0_s6 = RegNext(sortingNetworkStage(s5_out0, s6_pairs), sorter_reset_val)

    val s1_out1 = RegNext(sortingNetworkStage(block1_items_in, s1_pairs), sorter_reset_val)
    val s2_out1 = RegNext(sortingNetworkStage(s1_out1, s2_pairs), sorter_reset_val)
    val s3_out1 = RegNext(sortingNetworkStage(s2_out1, s3_pairs), sorter_reset_val)
    val s4_out1 = RegNext(sortingNetworkStage(s3_out1, s4_pairs), sorter_reset_val)
    val s5_out1 = RegNext(sortingNetworkStage(s4_out1, s5_pairs), sorter_reset_val)
    val sorted1_s6 = RegNext(sortingNetworkStage(s5_out1, s6_pairs), sorter_reset_val)

    // --- Mask Generation (Stages 7-10) ---
    
    val k0_s6 = RegNext(k0_s5, 0.U(4.W))
    val k1_s6 = RegNext(k1_s5, 0.U(4.W))
    
    val keep_mask_comb = Wire(Vec(16, Bool()))
    keep_mask_comb.foreach(_ := false.B)

    for (i <- 0 until 8) {
      when(i.U < k0_s6) {
        keep_mask_comb(sorted0_s6(i).index) := true.B
      }
      when(i.U < k1_s6) {
        keep_mask_comb(sorted1_s6(i).index + 8.U) := true.B
      }
    }

    // Register the mask for the remaining 4 stages to meet the 10-cycle latency.
    keep_mask_out := ShiftRegister(keep_mask_comb.asUInt, 4, 0.U, true.B)
  }
}
