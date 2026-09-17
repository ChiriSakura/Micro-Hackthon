import chisel3._
import chisel3.util._

class SelectAccumulate extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val scores_in = IO(Input(UInt(72.W)))
  val weights_in = IO(Input(UInt(128.W)))
  val values_in = IO(Input(UInt(64.W)))
  val N_out = IO(Output(UInt(28.W)))
  val D_out = IO(Output(UInt(19.W)))
  val keep_mask_out = IO(Output(UInt(8.W)))
  val valid_out = IO(Output(Bool()))

  withClockAndReset(clock, reset) {
    // 5-stage pipeline valid signal chain
    val valid_p1 = RegNext(valid_in, false.B)
    val valid_p2 = RegNext(valid_p1, false.B)
    val valid_p3 = RegNext(valid_p2, false.B)
    val valid_p4 = RegNext(valid_p3, false.B)
    valid_out := RegNext(valid_p4, false.B)

    // Stage 1: Latch inputs
    val scores_p1_reg = RegNext(scores_in, 0.U)
    val weights_p1_reg = RegNext(weights_in, 0.U)
    val values_p1_reg = RegNext(values_in, 0.U)

    // Stage 2: Unpack and calculate block sums
    val weights_p1 = weights_p1_reg.asTypeOf(Vec(8, UInt(16.W)))
    val B0 = (weights_p1(0) +& weights_p1(1)) +& (weights_p1(2) +& weights_p1(3))
    val B1 = (weights_p1(4) +& weights_p1(5)) +& (weights_p1(6) +& weights_p1(7))
    val S = B0 +& B1

    val scores_p2_reg = RegNext(scores_p1_reg, 0.U)
    val weights_p2_reg = RegNext(weights_p1_reg, 0.U)
    val values_p2_reg = RegNext(values_p1_reg, 0.U)
    val S_p2 = RegNext(S, 0.U)
    val B0_p2 = RegNext(B0, 0.U)
    val B1_p2 = RegNext(B1, 0.U)

    // Stage 3: Determine n0, n1 and compute ranks
    val scores_p2 = scores_p2_reg.asTypeOf(Vec(8, SInt(9.W)))
    
    val t0_quarters = 5.U
    val t1_quarters = 1.U

    val cmp0_lhs = B0_p2 << 3
    val cmp1_lhs = B1_p2 << 3
    val cmp_t0_rhs = t0_quarters * S_p2
    val cmp_t1_rhs = t1_quarters * S_p2

    val n0 = Mux(cmp0_lhs > cmp_t0_rhs, 2.U(2.W), Mux(cmp0_lhs < cmp_t1_rhs, 0.U(2.W), 1.U(2.W)))
    val n1 = Mux(cmp1_lhs > cmp_t0_rhs, 2.U(2.W), Mux(cmp1_lhs < cmp_t1_rhs, 0.U(2.W), 1.U(2.W)))

    val b0_scores = scores_p2.slice(0, 4)
    val b0_ranks = Wire(Vec(4, UInt(2.W)))
    for (i <- 0 until 4) {
      val my_score = b0_scores(i)
      val my_idx = i.U(2.W)
      val rank_bits = for (j <- 0 until 4 if i != j) yield {
        val other_score = b0_scores(j)
        val other_idx = j.U(2.W)
        (my_score < other_score) || (my_score === other_score && my_idx > other_idx)
      }
      b0_ranks(i) := rank_bits.foldLeft(0.U(2.W))(_ + _.asUInt)
    }

    val b1_scores = scores_p2.slice(4, 8)
    val b1_ranks = Wire(Vec(4, UInt(2.W)))
    for (i <- 0 until 4) {
      val my_score = b1_scores(i)
      val my_idx = (i + 4).U(3.W)
      val rank_bits = for (j <- 0 until 4 if i != j) yield {
        val other_score = b1_scores(j)
        val other_idx = (j + 4).U(3.W)
        (my_score < other_score) || (my_score === other_score && my_idx > other_idx)
      }
      b1_ranks(i) := rank_bits.foldLeft(0.U(2.W))(_ + _.asUInt)
    }

    val weights_p3_reg = RegNext(weights_p2_reg, 0.U)
    val values_p3_reg = RegNext(values_p2_reg, 0.U)
    val n0_p3 = RegNext(n0, 0.U)
    val n1_p3 = RegNext(n1, 0.U)
    val b0_ranks_p3 = RegNext(b0_ranks, VecInit(Seq.fill(4)(0.U(2.W))))
    val b1_ranks_p3 = RegNext(b1_ranks, VecInit(Seq.fill(4)(0.U(2.W))))

    // Stage 4: Generate keep_mask and compute weighted values
    val weights_p3 = weights_p3_reg.asTypeOf(Vec(8, UInt(16.W)))
    val values_p3 = values_p3_reg.asTypeOf(Vec(8, SInt(8.W)))

    val keep_vec = Wire(Vec(8, Bool()))
    for (i <- 0 until 4) { keep_vec(i) := b0_ranks_p3(i) < n0_p3 }
    for (i <- 0 until 4) { keep_vec(i + 4) := b1_ranks_p3(i) < n1_p3 }
    val keep_mask = keep_vec.asUInt

    val weighted_values = Wire(Vec(8, SInt(25.W)))
    for (i <- 0 until 8) {
      weighted_values(i) := weights_p3(i).zext * values_p3(i)
    }

    val weights_p4_vec = RegNext(weights_p3, VecInit(Seq.fill(8)(0.U(16.W))))
    val keep_mask_p4 = RegNext(keep_mask, 0.U)
    val weighted_values_p4 = RegNext(weighted_values, VecInit(Seq.fill(8)(0.S(25.W))))

    // Stage 5: Accumulate N and D
    val masked_weights = Wire(Vec(8, UInt(16.W)))
    val masked_w_values = Wire(Vec(8, SInt(25.W)))
    for (i <- 0 until 8) {
      masked_weights(i) := Mux(keep_mask_p4(i), weights_p4_vec(i), 0.U)
      masked_w_values(i) := Mux(keep_mask_p4(i), weighted_values_p4(i), 0.S)
    }

    val D_sum = masked_weights.reduceTree(_ +& _)
    val N_sum = masked_w_values.reduceTree(_ +& _)

    val N_reg = RegNext(N_sum, 0.S(28.W))
    val D_reg = RegNext(D_sum, 0.U(19.W))
    val keep_mask_reg = RegNext(keep_mask_p4, 0.U(8.W))

    N_out := N_reg.asUInt
    D_out := D_reg
    keep_mask_out := keep_mask_reg
  }
}
