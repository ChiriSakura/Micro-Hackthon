import chisel3._
import chisel3.util._

// The runner will compile the reference NormalizationUnit class,
// which is available in the default scope for instantiation.

class NormalizationUnit_rq1 extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val keep_mask_in = IO(Input(UInt(16.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val v_in = IO(Input(UInt(128.W)))
  val result_out = IO(Output(UInt(16.W)))
  val valid_out = IO(Output(Bool()))

  // Instantiate the verified native NormalizationUnit module
  val norm_unit = Module(new NormalizationUnit())

  // Connect the ports of this adapter to the native module's ports
  norm_unit.clock := clock
  norm_unit.reset := reset
  norm_unit.valid_in := valid_in
  norm_unit.keep_mask_in := keep_mask_in
  norm_unit.exponentials_in := exponentials_in
  norm_unit.v_in := v_in
  result_out := norm_unit.result_out
  valid_out := norm_unit.valid_out
}
