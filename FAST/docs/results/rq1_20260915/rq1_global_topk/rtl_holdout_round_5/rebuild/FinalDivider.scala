import chisel3._
import chisel3.util._

class FinalDivider extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val numer = IO(Input(UInt(28.W)))
  val denom = IO(Input(UInt(20.W)))
  val quotient = IO(Output(UInt(16.W)))
  val valid_out = IO(Output(Bool()))

  // --- Constants ---
  val STAGES = 18
  val DIVIDEND_WIDTH = 32
  val DIVISOR_WIDTH = 20
  val QUOTIENT_WIDTH = 16
  val ITERATIONS = DIVIDEND_WIDTH // Radix-2 needs one iteration per bit of dividend

  // Remainder needs to be one bit wider than the divisor to hold the result of the trial subtraction.
  val REM_WIDTH = DIVISOR_WIDTH + 1

  // --- Pipeline State Bundle ---
  class DivState extends Bundle {
    val remainder = UInt(REM_WIDTH.W)
    val quotient = UInt(ITERATIONS.W)
    val dividend_shifted = UInt(DIVIDEND_WIDTH.W)
    val divisor = UInt(DIVISOR_WIDTH.W)
    val negative = Bool()
    val divideByZero = Bool()
    val valid = Bool()
  }

  // --- Radix-2 Restoring Division Step (Combinational) ---
  def step(state: DivState): DivState = {
    val next = Wire(new DivState)

    // Form partial remainder: shift old remainder left, bring in next dividend bit.
    val shifted_rem = Cat(state.remainder(REM_WIDTH - 2, 0), state.dividend_shifted(DIVIDEND_WIDTH - 1))

    // Trial subtraction. The divisor is zero-extended to match the shifted_rem width.
    val can_subtract = shifted_rem >= state.divisor
    val trial_sub = shifted_rem - state.divisor

    // Update remainder (restoring if subtraction failed) and the next quotient bit.
    next.remainder := Mux(can_subtract, trial_sub, shifted_rem)
    next.quotient := Cat(state.quotient(ITERATIONS - 2, 0), can_subtract)
    
    // Shift dividend to expose the next bit for the following iteration.
    next.dividend_shifted := state.dividend_shifted << 1

    // Propagate control signals and constants through the pipeline.
    next.divisor := state.divisor
    next.negative := state.negative
    next.divideByZero := state.divideByZero
    next.valid := state.valid
    
    next
  }

  // --- Input Stage (Combinational) ---
  // Prepare operands for unsigned division: take absolute values and record the sign.
  val numer_sint = numer.asSInt
  val dividend_sint = numer_sint << 4 // Scale by 16 as per algorithm: (N*16)/D
  val dividend_abs = dividend_sint.abs.asUInt
  val divisor_abs = denom // Denominator is already unsigned
  val result_sign = numer_sint < 0.S // Denominator is unsigned, so sign is just numerator's sign
  val is_zero_denom = denom === 0.U

  // Define the initial state for the first pipeline stage.
  val initial_state = Wire(new DivState)
  initial_state.remainder := 0.U
  initial_state.quotient := 0.U
  initial_state.dividend_shifted := dividend_abs
  initial_state.divisor := divisor_abs
  initial_state.negative := result_sign
  initial_state.divideByZero := is_zero_denom
  initial_state.valid := valid_in

  // --- Pipeline Body ---
  // We must perform 32 iterations over 18 stages. This requires some stages to perform
  // more than one iteration combinationally.
  // Distribution: 14 stages * 2 iterations/stage + 4 stages * 1 iteration/stage = 32 iterations.
  val iters_in_fast_stage = 2
  val num_fast_stages = ITERATIONS - STAGES // 32 - 18 = 14

  val final_state = (0 until STAGES).foldLeft(initial_state) { (state_in, stage_idx) =>
    val iters_this_stage = if (stage_idx < num_fast_stages) iters_in_fast_stage else 1
    
    // Chain the combinational step functions for this stage.
    val state_after_steps = (0 until iters_this_stage).foldLeft(state_in) { (s, _) => step(s) }
    
    // Register the output of this stage's combinational logic.
    withClockAndReset(clock, reset) {
      RegNext(state_after_steps, 0.U.asTypeOf(new DivState))
    }
  }

  // --- Output Stage (Combinational) ---
  // Process the result from the final pipeline stage.
  val magnitude = final_state.quotient
  val signed_quotient = Mux(final_state.negative, -magnitude.asSInt, magnitude.asSInt)
  
  // Handle division by zero, otherwise apply the calculated sign for trunc-towards-zero behavior.
  val result = Mux(final_state.divideByZero, 0.S, signed_quotient)

  // Assign to outputs, truncating the result to the 16-bit port width.
  quotient := result.asUInt(QUOTIENT_WIDTH - 1, 0)
  valid_out := final_state.valid
}
