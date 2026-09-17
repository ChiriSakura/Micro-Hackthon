import chisel3._
import chisel3.util._

class ScoreAndExpUnit_Adapter extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(128.W)))
  val scores_out = IO(Output(UInt(144.W)))
  val exponentials_out = IO(Output(UInt(256.W)))
  val valid_out = IO(Output(Bool()))

  // The 'ScoreAndExpUnit' class is provided by the linked reference 'verified_rq1_score_exp'.
  // This adapter instantiates it and connects the ports.
  val scoreAndExpUnit = Module(new ScoreAndExpUnit)

  scoreAndExpUnit.clock := clock
  scoreAndExpUnit.reset := reset
  scoreAndExpUnit.valid_in := valid_in
  scoreAndExpUnit.q_in := q_in
  scoreAndExpUnit.k_in := k_in
  scores_out := scoreAndExpUnit.scores_out
  exponentials_out := scoreAndExpUnit.exponentials_out
  valid_out := scoreAndExpUnit.valid_out
}
