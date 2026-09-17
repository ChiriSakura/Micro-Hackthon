import chisel3._
import chisel3.util._

class Accumulator extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val in_valid = IO(Input(Bool()))
  val weights = IO(Input(UInt(36.W)))
  val values = IO(Input(UInt(16.W)))
  val out_valid = IO(Output(Bool()))
  val weight_sum = IO(Output(UInt(11.W)))
  val weighted_value_sum = IO(Output(UInt(15.W)))

  withClockAndReset(clock, reset) {
    // --- Stage 1: Multiplication and Input Unpacking ---
    // This stage is purely combinational, its results are registered below.

    // Unpack 4x 9-bit weights from the 36-bit input
    val w_vec = Wire(Vec(4, UInt(9.W)))
    // Unpack 4x 4-bit values from the 16-bit input
    val v_vec = Wire(Vec(4, UInt(4.W)))
    for (i <- 0 until 4) {
      w_vec(i) := weights(9 * (i + 1) - 1, 9 * i)
      v_vec(i) := values(4 * (i + 1) - 1, 4 * i)
    }

    // Compute 4 parallel products: weight[i] * value[i]
    val products = Wire(Vec(4, UInt(13.W)))
    for (i <- 0 until 4) {
      // 9-bit weight * 4-bit value results in a 13-bit product.
      products(i) := w_vec(i) * v_vec(i)
    }

    // --- Pipeline Registers (Stage 1 -> Stage 2) ---
    // These registers hold the results of Stage 1 for use in Stage 2.
    val stage2_valid = RegNext(in_valid, false.B)
    val stage2_weights = Reg(Vec(4, UInt(9.W)))
    val stage2_products = Reg(Vec(4, UInt(13.W)))

    // Latch the combinational results of Stage 1 when the input is valid.
    when(in_valid) {
      stage2_weights := w_vec
      stage2_products := products
    }

    // --- Stage 2: Adder Trees ---
    // This stage sums the values from the pipeline registers.

    // Adder tree for weights. Max sum is 4*450=1800, which fits in 11 bits.
    val w_sum_01 = stage2_weights(0) +& stage2_weights(1) // 9b + 9b -> 10b
    val w_sum_23 = stage2_weights(2) +& stage2_weights(3) // 9b + 9b -> 10b
    val total_w_sum = w_sum_01 +& w_sum_23               // 10b + 10b -> 11b

    // Adder tree for weighted values. Max sum is 4*(450*15)=27000, fits in 15 bits.
    val wv_sum_01 = stage2_products(0) +& stage2_products(1) // 13b + 13b -> 14b
    val wv_sum_23 = stage2_products(2) +& stage2_products(3) // 13b + 13b -> 14b
    val total_wv_sum = wv_sum_01 +& wv_sum_23                // 14b + 14b -> 15b

    // --- Output Registers (Stage 2 -> Output) ---
    // Final registers to align data with the 2-cycle latency.
    val out_valid_reg = RegNext(stage2_valid, false.B)
    val weight_sum_reg = RegInit(0.U(11.W))
    val weighted_value_sum_reg = RegInit(0.U(15.W))

    // Latch the results of the adder trees when Stage 2 is valid.
    when(stage2_valid) {
      weight_sum_reg := total_w_sum
      weighted_value_sum_reg := total_wv_sum
    }

    // --- Assign Outputs ---
    out_valid := out_valid_reg
    weight_sum := weight_sum_reg
    weighted_value_sum := weighted_value_sum_reg
  }
}
