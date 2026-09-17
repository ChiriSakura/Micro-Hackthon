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

  // Instantiate child modules
  val scoreExpUnit = Module(new ScoreAndExpUnit_Adapter)
  val selectionUnit = Module(new SelectionUnit)
  val normUnit = Module(new NormalizationUnit_Adapter)

  withClockAndReset(clock, reset) {
    // State machine to manage pipeline busy status.
    // This ensures one transaction at a time.
    val busy_reg = RegInit(false.B)
    val can_start = !busy_reg
    val actual_start = start && can_start

    // The done pulse from the last stage signals the end of a transaction.
    val done_pulse = normUnit.valid_out

    when(actual_start) {
      busy_reg := true.B
    }.elsewhen(done_pulse) {
      busy_reg := false.B
    }

    // Stage 1: ScoreAndExpUnit_Adapter (Latency 7)
    // Inputs are latched by the first stage on 'actual_start'.
    // The top-level inputs q, k, v are guaranteed to be stable until done.
    scoreExpUnit.clock := clock
    scoreExpUnit.reset := reset
    scoreExpUnit.valid_in := actual_start
    scoreExpUnit.q_in := q
    scoreExpUnit.k_in := k

    // Stage 2: SelectionUnit (Latency 12)
    // Connects to the output of the Score & Exp unit.
    selectionUnit.clock := clock
    selectionUnit.reset := reset
    selectionUnit.valid_in := scoreExpUnit.valid_out
    selectionUnit.scores_in := scoreExpUnit.scores_out
    selectionUnit.exponentials_in := scoreExpUnit.exponentials_out

    // Delay 'v' input to align with NormalizationUnit's input timing.
    // The NormalizationUnit starts after the ScoreExp and Selection units complete.
    // Delay = Latency(ScoreExp) + Latency(Selection) = 7 + 12 = 19 cycles.
    // The previous attempt failed by incorrectly passing 'reset' as an enable signal.
    // The correct implementation uses the default always-on enable.
    val v_delayed = ShiftRegister(v, 19)

    // Stage 3: NormalizationUnit_Adapter (Latency 41)
    // Connects to the output of the Selection unit.
    normUnit.clock := clock
    normUnit.reset := reset
    normUnit.valid_in := selectionUnit.valid_out
    normUnit.keep_mask_in := selectionUnit.keep_mask_out
    normUnit.exponentials_in := selectionUnit.exponentials_passthru
    normUnit.v_in := v_delayed

    // Delay 'keep_mask' from SelectionUnit to align with the final output.
    // The keep_mask is available at the output of the SelectionUnit. The final result
    // is available at the output of the NormalizationUnit. The delay needed is the
    // latency of the NormalizationUnit.
    // Delay = Latency(Normalization) = 41 cycles.
    // This also fixes the same bug as v_delayed.
    val keep_mask_delayed = ShiftRegister(selectionUnit.keep_mask_out, 41)

    // Final outputs are valid with the 'done' pulse from the last stage.
    done := done_pulse
    result := normUnit.result_out
    keep_mask := keep_mask_delayed
  }
}
