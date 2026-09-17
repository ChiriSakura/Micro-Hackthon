// Read-only Chisel reference: carry-preserving addition and explicit clock/reset.
import chisel3._
class ReferenceAddStage extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val a = IO(Input(UInt(8.W)))
  val b = IO(Input(UInt(8.W)))
  val valid_out = IO(Output(Bool()))
  val sum = IO(Output(UInt(9.W)))
  withClockAndReset(clock, reset) {
    val validReg = RegInit(false.B)
    val sumReg = RegInit(0.U(9.W))
    validReg := valid_in
    when(valid_in) { sumReg := a +& b }
    valid_out := validReg
    sum := sumReg
  }
}
