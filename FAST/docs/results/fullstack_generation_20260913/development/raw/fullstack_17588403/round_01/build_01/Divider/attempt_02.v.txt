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

  // State machine states
  val s_idle :: s_setup :: s_calc :: s_done :: Nil = Enum(4)

  // Wires to bridge register outputs from the sequential block to the combinational domain
  val state_current = Wire(UInt(2.W))
  val q_current = Wire(UInt(4.W))

  // Assign outputs combinationally from the state wires
  quotient_out := q_current
  done := state_current === s_done

  withClockAndReset(clock, reset) {
    // State and data registers
    val state_reg = RegInit(s_idle)
    val p_reg = Reg(SInt(12.W))       // Partial remainder (denom.width + 1)
    val a_reg = Reg(UInt(15.W))       // Remainder of numerator
    val d_reg = Reg(UInt(11.W))       // Denominator
    val q_reg = Reg(UInt(4.W))        // Quotient
    val cycle_reg = Reg(UInt(3.W))    // Cycle counter for calculation

    // Connect register outputs to the external wires
    state_current := state_reg
    q_current := q_reg

    // Combinational logic for one step of non-restoring division
    // This logic is inside the sequential block to access the registers directly
    val p_shifted = (p_reg(10, 0) ## a_reg(14)).asSInt
    val a_next = a_reg << 1
    val d_ext = d_reg.zext.asSInt

    val p_plus_d = p_shifted + d_ext
    val p_minus_d = p_shifted - d_ext
    val p_next = Mux(p_reg(11), p_plus_d, p_minus_d)

    val q_bit = !p_next(11)
    val q_next = (q_reg << 1) | q_bit

    // State machine and register update logic
    switch(state_reg) {
      is(s_idle) {
        when(start) {
          state_reg := s_setup
        }
      }
      is(s_setup) {
        state_reg := s_calc
        // Initialize registers for a new division operation
        p_reg := 0.S
        a_reg := numer_in
        d_reg := denom_in
        q_reg := 0.U
        cycle_reg := 4.U
      }
      is(s_calc) {
        // Update registers with the result of the current iteration
        p_reg := p_next
        a_reg := a_next
        q_reg := q_next
        cycle_reg := cycle_reg - 1.U

        // After 4 cycles (when counter is 1), the calculation is complete for the next cycle
        when(cycle_reg === 1.U) {
          state_reg := s_done
        }
      }
      is(s_done) {
        // Pulse done for one cycle and return to idle
        state_reg := s_idle
      }
    }
  }
}
