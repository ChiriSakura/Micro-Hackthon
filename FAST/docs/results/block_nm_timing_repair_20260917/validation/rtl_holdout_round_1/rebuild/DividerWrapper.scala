import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import predict_unit.FixedPointDivPipelined

class DividerWrapper extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val numer_in = IO(Input(SInt(32.W)))
  val denom_in = IO(Input(UInt(20.W)))
  val quotient_out = IO(Output(SInt(16.W)))
  val valid_out = IO(Output(Bool()))

  withClockAndReset(clock, reset) {
    val divider = Module(new FixedPointDivPipelined(
      bitWidth = 32,
      point = 0,
      stages = 33
    ))

    divider.io.in_valid := valid_in

    // Cast the SInt numerator to the divider's FixedPoint input type.
    divider.io.numerator := numer_in.asFixedPoint(0.BP)

    // The denominator is an unsigned 20-bit value. It must be zero-extended to 32 bits
    // to match the divider's input width. The native divider expects a signed FixedPoint,
    // but its internal logic takes the absolute value, so providing a positive number is correct.
    divider.io.denominator := denom_in.zext.asSInt.asFixedPoint(0.BP)

    // The valid signal is propagated through the divider's pipeline.
    valid_out := divider.io.out_valid

    // The divider produces a 32-bit FixedPoint result. It is converted to SInt,
    // and the assignment to the 16-bit output port truncates it as required.
    quotient_out := divider.io.quotient.asSInt
  }
}
