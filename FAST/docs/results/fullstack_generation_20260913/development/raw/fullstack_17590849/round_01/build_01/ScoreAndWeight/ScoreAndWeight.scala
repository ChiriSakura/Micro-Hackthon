import chisel3._
import chisel3.util._

class ScoreAndWeight extends RawModule {
  val q_vec = IO(Input(UInt(8.W)))
  val k_vec = IO(Input(UInt(8.W)))
  val weight = IO(Output(UInt(9.W)))

  // Unpack 4-bit components from 8-bit input vectors
  // q[d] is at bits 4*d +: 4
  val q0 = q_vec(3, 0)
  val q1 = q_vec(7, 4)

  // For a single key vector, k[i][d] is at bits 4*d +: 4
  val k0 = k_vec(3, 0)
  val k1 = k_vec(7, 4)

  // Compute 4x4 -> 8-bit products
  val p0 = q0 * k0
  val p1 = q1 * k1

  // Add 8-bit products to get a 9-bit score. The +& operator performs
  // widening addition to preserve the carry bit, preventing silent truncation.
  // Max score = (15*15) + (15*15) = 225 + 225 = 450, which requires 9 bits.
  val score = p0 +& p1

  // The threshold is a hardcoded constant as per the system plan.
  val threshold = 64.U(9.W)

  // Apply the threshold: if score is below threshold, weight is 0.
  // Otherwise, weight is the score.
  weight := Mux(score >= threshold, score, 0.U(9.W))
}
