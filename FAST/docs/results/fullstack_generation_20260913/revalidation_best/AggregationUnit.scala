import chisel3._
import chisel3.util._

class AggregationUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val scores_in = IO(Input(UInt(36.W)))
  val values_in = IO(Input(UInt(16.W)))
  val valid_out = IO(Output(Bool()))
  val weight_sum_out = IO(Output(UInt(11.W)))
  val weighted_value_sum_out = IO(Output(UInt(15.W)))

  // --- Stage 1: Thresholding and Weighted Value Calculation ---

  // Unpack inputs into vectors of 4-bit values and 9-bit scores
  val scores = VecInit(Seq.tabulate(4)(i => scores_in(9 * (i + 1) - 1, 9 * i)))
  val values = VecInit(Seq.tabulate(4)(i => values_in(4 * (i + 1) - 1, 4 * i)))

  // Combinational logic for stage 1
  val threshold = 64.U(9.W)
  val weights = Wire(Vec(4, UInt(9.W)))
  val weighted_values = Wire(Vec(4, UInt(13.W)))

  for (i <- 0 until 4) {
    weights(i) := Mux(scores(i) >= threshold, scores(i), 0.U(9.W))
    // 9-bit weight * 4-bit value = 13-bit weighted value
    weighted_values(i) := weights(i) * values(i)
  }

  // Stage 1 pipeline registers
  val valid_s1 = withClockAndReset(clock, reset) { RegInit(false.B) }
  val weights_s1 = withClockAndReset(clock, reset) { RegInit(VecInit(Seq.fill(4)(0.U(9.W)))) }
  val weighted_values_s1 = withClockAndReset(clock, reset) { RegInit(VecInit(Seq.fill(4)(0.U(13.W)))) }

  // Stage 1 update logic
  withClockAndReset(clock, reset) {
    valid_s1 := valid_in
    when(valid_in) {
      weights_s1 := weights
      weighted_values_s1 := weighted_values
    }
  }

  // --- Stage 2: Summation ---

  // Combinational logic for stage 2 (two-level adder trees)
  // Max weight sum = 4 * 450 = 1800 (11 bits)
  val weight_sum_s1_01 = weights_s1(0) +& weights_s1(1) // 10-bit
  val weight_sum_s1_23 = weights_s1(2) +& weights_s1(3) // 10-bit
  val weight_sum_comb = weight_sum_s1_01 +& weight_sum_s1_23 // 11-bit

  // Max weighted value sum = 4 * (450 * 15) = 27000 (15 bits)
  val weighted_value_sum_s1_01 = weighted_values_s1(0) +& weighted_values_s1(1) // 14-bit
  val weighted_value_sum_s1_23 = weighted_values_s1(2) +& weighted_values_s1(3) // 14-bit
  val weighted_value_sum_comb = weighted_value_sum_s1_01 +& weighted_value_sum_s1_23 // 15-bit

  // Stage 2 pipeline registers
  val valid_out_reg = withClockAndReset(clock, reset) { RegInit(false.B) }
  val weight_sum_out_reg = withClockAndReset(clock, reset) { RegInit(0.U(11.W)) }
  val weighted_value_sum_out_reg = withClockAndReset(clock, reset) { RegInit(0.U(15.W)) }

  // Stage 2 update logic
  withClockAndReset(clock, reset) {
    valid_out_reg := valid_s1
    when(valid_s1) {
      weight_sum_out_reg := weight_sum_comb
      weighted_value_sum_out_reg := weighted_value_sum_comb
    }
  }

  // Connect registers to outputs
  valid_out := valid_out_reg
  weight_sum_out := weight_sum_out_reg
  weighted_value_sum_out := weighted_value_sum_out_reg
}
