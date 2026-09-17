import chisel3._
import chisel3.util._

class ScoreAndWeightUnit extends RawModule {
  val q_vec = IO(Input(UInt(8.W)))
  val k_vec = IO(Input(UInt(8.W)))
  val threshold = IO(Input(UInt(9.W)))
  val weight = IO(Output(UInt(9.W)))

  // 1. Input Unpacking: The 8-bit inputs are split into two 4-bit components.
  val q0 = q_vec(3, 0)
  val q1 = q_vec(7, 4)
  val k0 = k_vec(3, 0)
  val k1 = k_vec(7, 4)

  // 2. Multiplication: Two parallel 4x4 unsigned multipliers are used.
  // The product of two 4-bit numbers results in an 8-bit value.
  val prod0 = q0 * k0
  val prod1 = q1 * k1

  // 3. Addition: The two 8-bit products are summed to calculate the score.
  // The maximum score is (15*15) + (15*15) = 450, which requires 9 bits.
  // The widening addition operator `+&` is used to produce a 9-bit result, preserving the carry bit.
  val score = prod0 +& prod1

  // 4. Thresholding: The 9-bit score is compared with the 9-bit threshold.
  val score_ge_thresh = score >= threshold

  // 5. Muxing: The output weight is selected based on the comparison.
  // If the score is greater than or equal to the threshold, the weight is the score; otherwise, it is 0.
  // The zero literal is explicitly sized to match the 9-bit output width.
  weight := Mux(score_ge_thresh, score, 0.U(9.W))
}
