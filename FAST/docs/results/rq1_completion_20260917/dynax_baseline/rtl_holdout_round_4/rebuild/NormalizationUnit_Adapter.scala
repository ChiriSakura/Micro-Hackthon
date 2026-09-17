import chisel3._
import chisel3.util._

// The class 'NormalizationUnit' is provided by the linked reference 'verified_rq1_normalization'.
// It is assumed to be available in the compilation scope, so no package import is needed.

class NormalizationUnit_Adapter extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val keep_mask_in = IO(Input(UInt(16.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val v_in = IO(Input(UInt(128.W)))
  val result_out = IO(Output(UInt(16.W)))
  val valid_out = IO(Output(Bool()))

  // Instantiate the verified, native NormalizationUnit module from the linked library.
  val normUnit = Module(new NormalizationUnit())

  // Connect the adapter's ports directly to the instantiated module's ports.
  normUnit.clock := clock
  normUnit.reset := reset
  normUnit.valid_in := valid_in
  normUnit.keep_mask_in := keep_mask_in
  normUnit.exponentials_in := exponentials_in
  normUnit.v_in := v_in
  result_out := normUnit.result_out
  valid_out := normUnit.valid_out
}
