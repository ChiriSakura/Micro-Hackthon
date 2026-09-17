import chisel3._
import chisel3.util._

class ScoreAndExpUnit_rq1 extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(128.W)))
  val scores_out = IO(Output(UInt(144.W)))
  val exponentials_out = IO(Output(UInt(256.W)))
  val valid_out = IO(Output(Bool()))

  // Instantiate the native ScoreAndExpUnit module provided as a linked reference.
  val scoreAndExpUnit_inst = Module(new ScoreAndExpUnit)

  // Connect the IOs of this adapter to the instantiated native module.
  scoreAndExpUnit_inst.clock := clock
  scoreAndExpUnit_inst.reset := reset
  scoreAndExpUnit_inst.valid_in := valid_in
  scoreAndExpUnit_inst.q_in := q_in
  scoreAndExpUnit_inst.k_in := k_in
  scores_out := scoreAndExpUnit_inst.scores_out
  exponentials_out := scoreAndExpUnit_inst.exponentials_out
  valid_out := scoreAndExpUnit_inst.valid_out
}
