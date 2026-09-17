import chisel3._

class ScoreUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(8.W)))
  val valid_out = IO(Output(Bool()))
  val score_out = IO(Output(UInt(9.W)))

  // Unpack 4-bit components from 8-bit inputs
  val q0 = q_in(3, 0)
  val q1 = q_in(7, 4)
  val k0 = k_in(3, 0)
  val k1 = k_in(7, 4)

  // Perform two parallel 4x4 multiplications, yielding 8-bit products
  val prod0 = q0 * k0
  val prod1 = q1 * k1

  // Use a widening addition (+&) to sum the products into a 9-bit result
  // Max score = (15*15) + (15*15) = 225 + 225 = 450, which requires 9 bits.
  val score_comb = prod0 +& prod1

  // Pipeline registers for score and valid signal
  val score_out_reg = withClockAndReset(clock, reset) { RegInit(0.U(9.W)) }
  val valid_out_reg = withClockAndReset(clock, reset) { RegInit(false.B) }

  // Register update logic for the single pipeline stage
  withClockAndReset(clock, reset) {
    // Propagate valid signal with one cycle of latency
    valid_out_reg := valid_in

    // Latch the computed score when the input is valid
    when(valid_in) {
      score_out_reg := score_comb
    }
  }

  // Connect registers to the module outputs
  score_out := score_out_reg
  valid_out := valid_out_reg
}
