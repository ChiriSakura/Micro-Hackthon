import chisel3._

class ScoreUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(8.W)))
  val valid_out = IO(Output(Bool()))
  val score_out = IO(Output(UInt(9.W)))

  // Combinational logic for score calculation
  val q0 = q_in(3, 0)
  val q1 = q_in(7, 4)
  val k0 = k_in(3, 0)
  val k1 = k_in(7, 4)

  val prod0 = q0 * k0
  val prod1 = q1 * k1

  val score_comb = prod0 +& prod1

  // Pipeline registers
  val score_out_reg = withClockAndReset(clock, reset) { RegInit(0.U(9.W)) }
  val valid_out_reg = withClockAndReset(clock, reset) { RegInit(false.B) }

  // Sequential update logic
  withClockAndReset(clock, reset) {
    valid_out_reg := valid_in
    when(valid_in) {
      score_out_reg := score_comb
    }
  }

  // Connect registers to outputs
  score_out := score_out_reg
  valid_out := valid_out_reg
}
