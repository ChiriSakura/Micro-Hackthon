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
    val scores_p1 = RegEnable(scores_in, 0.U, valid_in)
    val weights_p1 = RegEnable(weights_in, 0.U, valid_in)
    val values_p1 = RegEnable(values_in, 0.U, valid_in)

    // Stage 2: Calculate block sums
    val weights_vec_p1 = weights_p1.asTypeOf(Vec(8, UInt(16.W)))
    val B0 = weights_vec_p1.slice(0, 4).reduce(_ +& _)
    val B1 = weights_vec_p1.slice(4, 8).reduce(_ +& _)
    val S = B0 +& B1

    // Stage 2 -> 3 pipeline registers
    val scores_p2 = RegEnable(scores_p1, 0.U, valid_p1)
    val weights_p2 = RegEnable(weights_p1, 0.U, valid_p1)
    val values_p2 = RegEnable(values_p1, 0.U, valid_p1)
    val S_p2 = RegEnable(S, 0.U, valid_p1)
    val B0_p2 = RegEnable(B0, 0.U, valid_p1)
    val B1_p2 = RegEnable(B1, 0.U, valid_p1)

    // Stage 3: Determine n0, n1 and compute ranks
    val scores_vec_p2 = scores_p2.asTypeOf(Vec(8, SInt(9.W)))
    val t0_quarters = 5.U
    val t1_quarters = 1.U
    
    val cmp_width = 22
    val cmp0_lhs = (B0_p2 << 3).pad(cmp_width)
    val cmp1_lhs = (B1_p2 << 3).pad(cmp_width)
    val cmp_t0_rhs = (t0_quarters * S_p2).pad(cmp_width)
    val cmp_t1_rhs = (t1_quarters * S_p2).pad(cmp_width)

    val n0 = Mux(cmp0_lhs > cmp_t0_rhs, 2.U(2.W), Mux(cmp0_lhs < cmp_t1_rhs, 0.U(2.W), 1.U(2.W)))
    val n1 = Mux(cmp1_lhs > cmp_t0_rhs, 2.U(2.W), Mux(cmp1_lhs < cmp_t1_rhs, 0.U(2.W), 1.U(2.W)))

    val ranks_vec = Wire(Vec(8, UInt(2.W)))
    val b0_scores = scores_vec_p2.slice(0, 4)
    for (i <- 0 until 4) {
      val i_score = b0_scores(i)
      val i_idx = i.U(3.W)
      val rank = (0 until 4).map { j =>
        val j_score = b0_scores(j)
        val j_idx = j.U(3.W)
        ((j_score > i_score) || (j_score === i_score && j_idx < i_idx)).asUInt
      }.reduce(_ +& _)
      ranks_vec(i) := rank
    }
    val b1_scores = scores_vec_p2.slice(4, 8)
    for (i <- 0 until 4) {
      val i_score = b1_scores(i)
      val i_idx = (i + 4).U(3.W)
      val rank = (0 until 4).map { j =>
        val j_score = b1_scores(j)
        val j_idx = (j + 4).U(3.W)
        ((j_score > i_score) || (j_score === i_score && j_idx < i_idx)).asUInt
      }.reduce(_ +& _)
      ranks_vec(i + 4) := rank
    }

    // Stage 3 -> 4 pipeline registers
    val weights_p3 = RegEnable(weights_p2, 0.U, valid_p2)
    val values_p3 = RegEnable(values_p2, 0.U, valid_p2)
    val n0_p3 = RegEnable(n0, 0.U, valid_p2)
    val n1_p3 = RegEnable(n1, 0.U, valid_p2)
    val ranks_p3 = RegEnable(ranks_vec, VecInit(Seq.fill(8)(0.U(2.W))), valid_p2)

    // Stage 4: Generate keep_mask and compute weighted values
    val weights_vec_p3 = weights_p3.asTypeOf(Vec(8, UInt(16.W)))
    val values_vec_p3 = values_p3.asTypeOf(Vec(8, SInt(8.W)))

    val keep_vec = Wire(Vec(8, Bool()))
    for (i <- 0 until 4) { keep_vec(i) := ranks_p3(i) < n0_p3 }
    for (i <- 0 until 4) { keep_vec(i + 4) := ranks_p3(i + 4) < n1_p3 }
    val keep_mask = keep_vec.asUInt

    val weighted_values_vec = Wire(Vec(8, SInt(24.W)))
    for (i <- 0 until 8) {
      weighted_values_vec(i) := (weights_vec_p3(i).zext * values_vec_p3(i)).asSInt
    }

    // Stage 4 -> 5 pipeline registers
    val keep_mask_p4 = RegEnable(keep_mask, 0.U, valid_p3)
    val weights_p4 = RegEnable(weights_p3, 0.U, valid_p3)
    val weighted_values_p4 = RegEnable(weighted_values_vec, VecInit(Seq.fill(8)(0.S(24.W))), valid_p3)

    // Stage 5: Accumulate N and D
    val weights_vec_p4 = weights_p4.asTypeOf(Vec(8, UInt(16.W)))
    val masked_weights = Wire(Vec(8, UInt(16.W)))
    val masked_w_values = Wire(Vec(8, SInt(24.W)))
    for (i <- 0 until 8) {
      masked_weights(i) := Mux(keep_mask_p4(i), weights_vec_p4(i), 0.U)
      masked_w_values(i) := Mux(keep_mask_p4(i), weighted_values_p4(i), 0.S)
    }

    val D_sum = masked_weights.reduceTree(_ +& _)
    val N_sum = masked_w_values.reduceTree(_ +& _)

    // Stage 5 -> Output registers
    val N_reg = RegInit(0.S(28.W))
    val D_reg = RegInit(0.U(19.W))
    val keep_mask_reg = RegInit(0.U(8.W))
    when(valid_p4) {
      N_reg := N_sum.asSInt
      D_reg := D_sum
      keep_mask_reg := keep_mask_p4
    }

    N_out := N_reg.asUInt
    D_out := D_reg
    keep_mask_out := keep_mask_reg
  }
}
