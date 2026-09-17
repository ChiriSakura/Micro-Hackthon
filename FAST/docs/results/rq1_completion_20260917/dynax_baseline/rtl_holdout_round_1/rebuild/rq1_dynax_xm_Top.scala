import chisel3._
import chisel3.util._

class rq1_dynax_xm_Top extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(128.W)))
  val v = IO(Input(UInt(128.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(16.W)))
  val keep_mask = IO(Output(UInt(16.W)))

  val scoreExpUnit = Module(new ScoreAndExpUnit_Adapter)
  val selectionUnit = Module(new SelectionUnit)
  val normUnit = Module(new NormalizationUnit_Adapter)

  withClockAndReset(clock, reset) {
    // This state machine ensures only one transaction is processed at a time.
    // 'actual_start' is a one-cycle pulse that initiates the pipeline.
    val busy_reg = RegInit(false.B)
    val can_start = !busy_reg
    val actual_start = start && can_start

    val done_pulse = normUnit.valid_out

    when(actual_start) {
      busy_reg := true.B
    }.elsewhen(done_pulse) {
      busy_reg := false.B
    }

    // Stage 1: Score & Exp (Latency 7)
    // Inputs are guaranteed to be stable, so they can be connected directly.
    scoreExpUnit.clock := clock
    scoreExpUnit.reset := reset
    scoreExpUnit.valid_in := actual_start
    scoreExpUnit.q_in := q
    scoreExpUnit.k_in := k

    // Stage 2: Selection (Latency 12)
    // Connects to the output of the Score & Exp unit.
    selectionUnit.clock := clock
    selectionUnit.reset := reset
    selectionUnit.valid_in := scoreExpUnit.valid_out
    selectionUnit.scores_in := scoreExpUnit.scores_out
    selectionUnit.exponentials_in := scoreExpUnit.exponentials_out

    // Delay 'v' to align with normUnit input.
    // normUnit starts after 7 (ScoreExp) + 12 (Selection) = 19 cycles.
    val v_delayed = ShiftRegister(v, 19)

    // Stage 3: Normalization (Latency 41)
    // Connects to the output of the Selection unit, with the 'v' input appropriately delayed.
    normUnit.clock := clock
    normUnit.reset := reset
    normUnit.valid_in := selectionUnit.valid_out
    normUnit.keep_mask_in := selectionUnit.keep_mask_out
    normUnit.exponentials_in := selectionUnit.exponentials_passthru
    normUnit.v_in := v_delayed

    // Delay 'keep_mask' to align with the final 'done' pulse.
    // 'keep_mask_out' is valid after 19 cycles.
    // 'done' is valid after 19 + 41 = 60 cycles.
    // The required delay is 41 cycles.
    val keep_mask_delayed = ShiftRegister(selectionUnit.keep_mask_out, 41)

    // Final outputs are valid with the 'done' pulse from the last stage.
    done := done_pulse
    result := normUnit.result_out
    keep_mask := keep_mask_delayed
  }
}
