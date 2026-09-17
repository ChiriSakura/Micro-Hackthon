import chisel3._
import chisel3.util._

class ScoreCalculator extends RawModule {
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(8.W)))
  val score_out = IO(Output(SInt(9.W)))

  // Unpack the 8-bit inputs into two 4-bit signed integers each.
  // The .asSInt method reinterprets the UInt bit pattern as a two's complement SInt.
  val q0 = q_in(3, 0).asSInt
  val q1 = q_in(7, 4).asSInt
  val k0 = k_in(3, 0).asSInt
  val k1 = k_in(7, 4).asSInt

  // Perform two 4x4 signed multiplications. The result of each is an 8-bit SInt.
  val p0 = q0 * k0
  val p1 = q1 * k1

  // Add the two 8-bit signed products. The sum can range from -112 to 128.
  // The maximum positive value (128) requires 9 bits to represent in two's complement.
  // The widening addition operator `+&` is used to produce a 9-bit result, preventing overflow.
  val score = p0 +& p1

  // Assign the 9-bit signed result to the output port.
  score_out := score
}
