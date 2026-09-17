import chisel3._
import chisel3.util._

class Divider extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val numer_in = IO(Input(UInt(15.W)))
  val denom_in = IO(Input(UInt(11.W)))
  val quotient_out = IO(Output(UInt(4.W)))
  val done = IO(Output(Bool()))

  val s_IDLE :: s_CALC :: s_DONE :: Nil = Enum(3)

  withClockAndReset(clock, reset) {
    // Registers with synchronous reset values
    val state_reg = RegInit(s_IDLE)
    val remainder_reg = RegInit(0.U(15.W))
    val divisor_reg = RegInit(0.U(11.W))
    val quotient_reg = RegInit(0.U(4.W))
    val cycle_counter_reg = RegInit(0.U(3.W))

    // Default output values
    done := false.B

    // State machine
    switch(state_reg) {
      is(s_IDLE) {
        when(start) {
          remainder_reg := numer_in
          divisor_reg := denom_in
          quotient_reg := 0.U
          cycle_counter_reg := 4.U
          state_reg := s_CALC
        }
      }

      is(s_CALC) {
        val rem_shifted_left = remainder_reg << 1
        val quot_shifted_left = quotient_reg << 1

        // Top 11 bits of the 15-bit shifted remainder
        val rem_msbs = rem_shifted_left(14, 4)

        // Trial subtraction: rem_msbs - divisor_reg. Widen to 12 bits to capture borrow.
        val trial_sub_ext = Cat(0.U(1.W), rem_msbs) - Cat(0.U(1.W), divisor_reg)
        val sub_successful = !trial_sub_ext(11)

        when(sub_successful) {
          // Update remainder with subtraction result
          remainder_reg := Cat(trial_sub_ext(10, 0), rem_shifted_left(3, 0))
        }.otherwise {
          // Restore remainder (use the shifted value)
          remainder_reg := rem_shifted_left
        }

        quotient_reg := quot_shifted_left | sub_successful

        cycle_counter_reg := cycle_counter_reg - 1.U
        when(cycle_counter_reg === 1.U) {
          state_reg := s_DONE
        }
      }

      is(s_DONE) {
        done := true.B
        state_reg := s_IDLE
      }
    }

    // Assign output from register. The final value is available in the DONE state.
    quotient_out := quotient_reg
  }
}
