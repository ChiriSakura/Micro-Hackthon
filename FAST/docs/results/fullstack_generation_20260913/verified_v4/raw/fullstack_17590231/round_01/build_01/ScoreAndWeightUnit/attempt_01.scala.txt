import chisel3._
import chisel3.util._

class ScoreAndWeightUnit extends RawModule {
  val q_vec = IO(Input(UInt(8.W)))
  val k_vec = IO(Input(UInt(8.W)))
  val threshold = IO(Input(UInt(9.W)))
  val weight = IO(Output(UInt(9.W)))

  // 1. Input Unpacking: Split 8-bit vectors into two 4-bit components.
  val q0 = q_vec(3, 0)
  val q1 = q_vec(7, 4)
  val k0 = k_vec(3, 0)
  val k1 = k_vec(7, 4)

  // 2. Multiplication: Two parallel 4x4 unsigned multipliers.
  // The product of two 4-bit numbers is an 8-bit number.
  val prod0 = q0 * k0
  val prod1 = q1 * k1

  // 3. Addition: Sum the products to get the score.
  // The maximum score is (15*15) + (15*15) = 450, which requires 9 bits.
  // The `+&` operator performs a widening addition to produce a 9-bit result,
  // preserving the carry-out bit from the 8-bit sum.
  val score = prod0 +& prod1

  // 4. Thresholding: Compare the 9-bit score against the 9-bit threshold.
  val score_ge_thresh = score >= threshold

  // 5. Muxing: Select the output weight.
  // If the score is greater than or equal to the threshold, the weight is the score.
  // Otherwise, the weight is zero. The zero literal is sized to match the output width.
  weight := Mux(score_ge_thresh, score, 0.U(9.W))
}
