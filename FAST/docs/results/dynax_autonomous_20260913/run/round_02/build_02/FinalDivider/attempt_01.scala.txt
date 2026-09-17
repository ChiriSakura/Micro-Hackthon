import chisel3._
import chisel3.util._
import predict_unit.FixedPointDivPipelined

class FinalDivider extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val numer_in = IO(Input(UInt(27.W)))
  val denom_in = IO(Input(UInt(19.W)))
  val valid_out = IO(Output(Bool()))
  val quot_out = IO(Output(UInt(16.W)))

  val divider = withClockAndReset(clock, reset) {
    Module(new FixedPointDivPipelined(
      bitWidth = 31,
      point = 0, // Integer division
      stages = 9 // As per uArch critic and updated plan
    ))
  }

  divider.io.in_valid := valid_in

  // Prepare the numerator for the divider.
  // The operation is `numer_in * 16`, which is a left shift by 4.
  // numer_in is a 27-bit signed number (passed as UInt). We cast it to SInt.
  // The SInt shift operator `<<` performs an arithmetic shift and widens the result.
  // The result will be 27 + 4 = 31 bits wide, matching the divider's input width.
  val scaled_numer = numer_in.asSInt << 4
  divider.io.numerator := scaled_numer.asFixedPoint(0.BP)

  // Prepare the denominator for the divider.
  // denom_in is a 19-bit unsigned number. The divider expects a 31-bit signed input.
  // To treat it as a positive number, we must zero-extend it to 31 bits.
  val extended_denom = Cat(0.U((31 - 19).W), denom_in)
  divider.io.denominator := extended_denom.asSInt.asFixedPoint(0.BP)

  // The divider's output is a 31-bit signed result. Truncate to 16 bits for the final output.
  // The .asUInt cast provides the raw bits for the UInt output port.
  quot_out := divider.io.quotient.asSInt(15, 0).asUInt
  valid_out := divider.io.out_valid
}
