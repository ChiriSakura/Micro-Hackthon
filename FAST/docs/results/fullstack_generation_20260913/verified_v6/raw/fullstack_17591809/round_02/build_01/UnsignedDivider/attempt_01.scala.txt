import chisel3._
import chisel3.util._

class UnsignedDivider extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val numerator_in = IO(Input(UInt(15.W)))
  val denominator_in = IO(Input(UInt(11.W)))
  val valid_out = IO(Output(Bool()))
  val quotient_out = IO(Output(UInt(4.W)))

  val N_WIDTH = 15
  val D_WIDTH = 11
  val Q_WIDTH = 4
  val STAGES = 4 // Reduced from 15 per critic instruction

  // The number of iterations in a restoring divider is the width of the numerator.
  val ITERATIONS = N_WIDTH

  // Calculate iterations per stage using ceiling division. This groups steps.
  val perStage = (ITERATIONS + STAGES - 1) / STAGES

  // Internal state carried between pipeline stages.
  class DivState extends Bundle {
    // Remainder must be 1 bit wider than divisor for the trial subtraction.
    val remainder = UInt((D_WIDTH + 1).W)
    // Quotient is built up one bit at a time.
    val quotient = UInt(ITERATIONS.W)
    // Dividend is shifted left, feeding bits into the remainder.
    val dividend = UInt(N_WIDTH.W)
    // Divisor is constant throughout the operation.
    val divisor = UInt(D_WIDTH.W)
    val divideByZero = Bool()
    val valid = Bool()
  }

  // A single step of the radix-2 restoring division algorithm.
  def step(state: DivState): DivState = {
    val next = Wire(new DivState)

    // Shift the remainder left and bring in the most significant bit of the dividend.
    val shifted_rem = Cat(state.remainder(D_WIDTH - 1, 0), state.dividend(N_WIDTH - 1))

    // Trial subtraction: check if the divisor fits into the shifted remainder.
    val can_subtract = shifted_rem >= state.divisor
    val next_rem = Mux(can_subtract, shifted_rem - state.divisor, shifted_rem)
    val quotient_bit = can_subtract

    // Update state for the next iteration.
    next.remainder := next_rem(D_WIDTH, 0)
    next.quotient := Cat(state.quotient(ITERATIONS - 2, 0), quotient_bit)
    next.dividend := Cat(state.dividend(N_WIDTH - 2, 0), 0.U(1.W))

    // Propagate constant values.
    next.divisor := state.divisor
    next.divideByZero := state.divideByZero
    next.valid := state.valid

    next
  }

  // --- Pipeline Construction ---

  // Stage 0: Input latching and initialization.
  val initial_state = Wire(new DivState)
  initial_state.remainder := 0.U
  initial_state.quotient := 0.U
  initial_state.dividend := numerator_in
  initial_state.divisor := denominator_in
  initial_state.divideByZero := (denominator_in === 0.U)
  initial_state.valid := valid_in

  // Generate the pipeline stages by chaining combinational step blocks and registers.
  var carried_state = initial_state
  var remaining_iterations = ITERATIONS

  for (i <- 0 until STAGES) {
    var stage_comb_out = carried_state
    val iterations_this_stage = math.min(perStage, remaining_iterations)

    for (j <- 0 until iterations_this_stage) {
      stage_comb_out = step(stage_comb_out)
    }

    remaining_iterations -= iterations_this_stage

    carried_state = withClockAndReset(clock, reset) {
      RegNext(stage_comb_out, 0.U.asTypeOf(new DivState))
    }
  }

  // --- Output Stage ---
  val final_state = carried_state

  // Handle division by zero, otherwise use the computed quotient.
  val full_quotient = Mux(final_state.divideByZero, 0.U, final_state.quotient)

  // Connect to outputs.
  valid_out := final_state.valid
  // The final result is truncated to 4 bits as per the numeric bounds and output port width.
  quotient_out := full_quotient(Q_WIDTH - 1, 0)
}
