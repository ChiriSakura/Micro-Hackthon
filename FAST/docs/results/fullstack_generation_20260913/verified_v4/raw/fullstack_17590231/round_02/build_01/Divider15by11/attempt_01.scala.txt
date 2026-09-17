import chisel3._
import chisel3.util._

class Divider15by11 extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val dividend = IO(Input(UInt(15.W)))
  val divisor = IO(Input(UInt(11.W)))
  val quotient = IO(Output(UInt(15.W)))
  val valid_out = IO(Output(Bool()))

  withClockAndReset(clock, reset) {
    // Registers to hold inputs for the one-cycle operation, creating a single pipeline stage.
    val dividend_reg = RegInit(0.U(15.W))
    val divisor_reg = RegInit(0.U(11.W))
    val valid_reg = RegInit(false.B)

    // On a start pulse, latch the inputs into the pipeline registers.
    when(start) {
      dividend_reg := dividend
      divisor_reg := divisor
    }
    
    // The valid_out signal is a one-cycle delayed version of the start signal.
    valid_reg := start
    valid_out := valid_reg

    // --- Combinational Restoring Divider Core ---
    // This logic operates on the registered inputs, making the result available
    // one cycle after the inputs were latched. The 'foldLeft' construct unrolls
    // the division algorithm into 15 combinational stages.
    val (final_rem, calculated_quotient) = (0 until 15).foldLeft((0.U(11.W), 0.U(15.W))) {
      // acc: a tuple of (current_remainder, current_quotient)
      // i: the iteration number, from 0 to 14, for each quotient bit
      case ((rem, quot), i) =>
        // Process one bit of the dividend, from MSB (i=0) to LSB (i=14).
        val dividend_bit = dividend_reg(14 - i)

        // Form the next partial remainder by shifting the current one and appending the dividend bit.
        // The temporary remainder needs 12 bits for the subtraction against the 11-bit divisor.
        val temp_rem = (rem << 1) | dividend_bit

        // Trial subtraction: check if the temporary remainder is large enough.
        val can_subtract = temp_rem >= divisor_reg

        // If subtraction is possible, the new remainder is the result of the subtraction.
        // Otherwise, the remainder is restored to the temporary value.
        val next_rem = Mux(can_subtract, temp_rem - divisor_reg, temp_rem)

        // Build the quotient by shifting and appending the comparison result (the new quotient bit).
        val next_quot = (quot << 1) | can_subtract

        // Return the new state (remainder, quotient) for the next stage.
        // The remainder is truncated back to 11 bits.
        (next_rem(10, 0), next_quot)
    }

    // The output quotient is the combinational result from the registered inputs.
    // This ensures the quotient is valid in the same cycle as valid_out.
    quotient := calculated_quotient
  }
}
