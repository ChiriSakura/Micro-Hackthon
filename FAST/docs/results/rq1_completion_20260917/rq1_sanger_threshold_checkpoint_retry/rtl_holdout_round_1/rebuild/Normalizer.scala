import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import predict_unit.FixedPointDivPipelined

class Normalizer extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_input = IO(Input(Bool()))
  val N_in = IO(Input(UInt(28.W)))
  val D_in = IO(Input(UInt(20.W)))
  val valid_output = IO(Output(Bool()))
  val result_out = IO(Output(SInt(16.W)))

  withClockAndReset(clock, reset) {
    val divider = Module(new FixedPointDivPipelined(bitWidth = 32, point = 0, stages = 8))

    // Connect inputs
    divider.io.in_valid := valid_input

    // Prepare numerator: N_in (S28) is shifted left by 4 to produce a S32 value.
    // The shift on a SInt widens the result automatically.
    val numerator_s32 = N_in.asSInt << 4
    divider.io.numerator := numerator_s32.asFixedPoint(0.BP)

    // Prepare denominator: D_in (U20) is zero-extended to 32 bits and cast to a signed value.
    // The divider expects a signed input.
    val denominator_s32 = D_in.zext.asSInt
    divider.io.denominator := denominator_s32.asFixedPoint(0.BP)

    // Connect outputs
    valid_output := divider.io.out_valid

    // Truncate the S32 quotient from the divider to the S16 output.
    val quotient_s32 = divider.io.quotient.asSInt
    result_out := quotient_s32(15, 0).asSInt
  }
}
