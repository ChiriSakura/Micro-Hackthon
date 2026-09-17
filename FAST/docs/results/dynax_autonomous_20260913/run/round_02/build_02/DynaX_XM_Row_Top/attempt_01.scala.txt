import chisel3._
import chisel3.util._

class DynaX_XM_Row_Top extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(64.W)))
  val v = IO(Input(UInt(64.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(16.W)))
  val keep_mask = IO(Output(UInt(8.W)))

  // Child module instantiations
  val score_proc = Module(new ScoreWeightProcessor)
  val sel_agg = Module(new SelectorAggregator)
  val divider = Module(new FinalDivider)

  // Connect child module clocks and resets
  score_proc.clock := clock
  score_proc.reset := reset
  divider.clock := clock
  divider.reset := reset

  val sIdle :: sProcess :: sWaitWeights :: sAggregate :: sDivStart :: sWaitDivider :: sDone :: Nil = Enum(7)

  val state = withClockAndReset(clock, reset) { RegInit(sIdle) }

  // Input latches
  val q_reg = withClockAndReset(clock, reset) { Reg(UInt(8.W)) }
  val k_reg = withClockAndReset(clock, reset) { Reg(UInt(64.W)) }
  val v_reg = withClockAndReset(clock, reset) { Reg(UInt(64.W)) }

  // Intermediate value registers for pipelining between stages
  val scores_reg = withClockAndReset(clock, reset) { Reg(UInt(72.W)) }
  val weights_reg = withClockAndReset(clock, reset) { Reg(UInt(128.W)) }
  val N_reg = withClockAndReset(clock, reset) { Reg(SInt(27.W)) }
  val D_reg = withClockAndReset(clock, reset) { Reg(UInt(19.W)) }

  // Output registers
  val result_reg = withClockAndReset(clock, reset) { Reg(UInt(16.W)) }
  val keep_mask_reg = withClockAndReset(clock, reset) { Reg(UInt(8.W)) }
  val done_reg = withClockAndReset(clock, reset) { RegInit(false.B) }

  // Connect outputs to registers
  result := result_reg
  keep_mask := keep_mask_reg
  done := done_reg

  // Default assignments to child modules
  score_proc.valid_in := false.B
  score_proc.q_in := 0.U
  score_proc.k_in := 0.U

  sel_agg.scores_in := 0.U
  sel_agg.weights_in := 0.U
  sel_agg.v_in := 0.U

  divider.valid_in := false.B
  divider.numer_in := 0.U
  divider.denom_in := 0.U

  // Default assignment for done pulse
  done_reg := false.B

  // FSM logic
  switch(state) {
    is(sIdle) {
      when(start) {
        q_reg := q
        k_reg := k
        v_reg := v
        state := sProcess
      }
    }
    is(sProcess) {
      score_proc.valid_in := true.B
      score_proc.q_in := q_reg
      score_proc.k_in := k_reg
      state := sWaitWeights
    }
    is(sWaitWeights) {
      when(score_proc.valid_out) {
        scores_reg := score_proc.scores_out
        weights_reg := score_proc.weights_out
        state := sAggregate
      }
    }
    is(sAggregate) {
      sel_agg.scores_in := scores_reg
      sel_agg.weights_in := weights_reg
      sel_agg.v_in := v_reg

      // Latch the outputs of the combinational aggregator
      N_reg := sel_agg.N_out
      D_reg := sel_agg.D_out
      keep_mask_reg := sel_agg.keep_mask_out

      state := sDivStart
    }
    is(sDivStart) {
      divider.valid_in := true.B
      divider.numer_in := N_reg.asUInt
      divider.denom_in := D_reg
      state := sWaitDivider
    }
    is(sWaitDivider) {
      when(divider.valid_out) {
        result_reg := divider.quot_out
        state := sDone
      }
    }
    is(sDone) {
      done_reg := true.B
      when(!start) {
        state := sIdle
      }
    }
  }
}
