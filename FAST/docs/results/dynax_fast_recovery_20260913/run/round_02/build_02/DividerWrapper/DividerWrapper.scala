import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import predict_unit._

class DividerWrapper extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val N_in = IO(Input(UInt(28.W)))
  val D_in = IO(Input(UInt(19.W)))
  val result_out = IO(Output(UInt(16.W)))
  val valid_out = IO(Output(Bool()))

  val divider = withClockAndReset(clock, reset) {
    Module(new FixedPointDivPipelined(bitWidth = 32, point = 0, stages = 8))
  }

  // Per the algorithm, the numerator is N*16. N_in is a 28-bit signed value.
  // Shifting left by 4 on its SInt representation multiplies by 16 and produces a 32-bit signed result.
  val numerator_s32 = (N_in.asSInt << 4).asSInt

  // The denominator D_in is a 19-bit unsigned value. It is zero-extended to 32 bits
  // and then cast to a signed integer for the divider's input.
  val denominator_s32 = Cat(0.U((32 - 19).W), D_in).asSInt

  divider.io.in_valid := valid_in
  divider.io.numerator := numerator_s32.asFixedPoint(0.BP)
  divider.io.denominator := denominator_s32.asFixedPoint(0.BP)

  valid_out := divider.io.out_valid

  // The linked reference `FixedPointDivPipelined` handles division by zero by returning 0.
  // The final result is the lower 16 bits of the 32-bit quotient, truncating toward zero.
  result_out := divider.io.quotient.asUInt(15, 0)
}
