import chisel3._
import chisel3.util._

class ProcessingElement extends RawModule {
  val q0 = IO(Input(UInt(4.W)))
  val q1 = IO(Input(UInt(4.W)))
  val k0 = IO(Input(UInt(4.W)))
  val k1 = IO(Input(UInt(4.W)))
  val v_in = IO(Input(UInt(4.W)))
  val weight_out = IO(Output(UInt(9.W)))
  val weighted_v_out = IO(Output(UInt(13.W)))

  // Calculate score = (q0 * k0) + (q1 * k1)
  // 4b * 4b -> 8b
  val prod0 = q0 * k0
  val prod1 = q1 * k1
  // 8b + 8b -> 9b. Max score is (15*15)+(15*15) = 450, which fits in 9 bits.
  val score = prod0 + prod1

  // Apply threshold: weight = (score >= threshold) ? score : 0
  // The threshold is hardcoded to 64 as per the selected configuration.
  val threshold = 64.U(9.W)
  val weight = Mux(score >= threshold, score, 0.U(9.W))

  // Calculate weighted value: weighted_v = weight * v_in
  // 9b * 4b -> 13b. Max is 450 * 15 = 6750, which fits in 13 bits.
  val weighted_v = weight * v_in

  // Assign to outputs
  weight_out := weight
  weighted_v_out := weighted_v
}
