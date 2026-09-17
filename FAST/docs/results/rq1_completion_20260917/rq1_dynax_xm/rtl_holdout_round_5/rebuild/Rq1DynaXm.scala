import chisel3._
import chisel3.util._

class Rq1DynaXm extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(128.W)))
  val v = IO(Input(UInt(128.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(16.W)))
  val keep_mask = IO(Output(UInt(16.W)))

  withClockAndReset(clock, reset) {
    // Instantiate child modules
    val score_exp_unit = Module(new ScoreAndExpUnit_rq1)
    val selection_unit = Module(new DynaX_SelectionUnit)
    val norm_unit = Module(new NormalizationUnit_rq1)

    // State machine for transaction control
    val s_idle :: s_busy :: Nil = Enum(2)
    val state = RegInit(s_idle)

    // Input registers
    val q_reg = RegInit(0.U(8.W))
    val k_reg = RegInit(0.U(128.W))
    val v_reg = RegInit(0.U(128.W))

    // Pipeline start signal generation
    val score_exp_valid_in = RegInit(false.B)
    score_exp_valid_in := false.B // Default assignment

    // State transitions and input latching
    when(state === s_idle && start) {
      state := s_busy
      q_reg := q
      k_reg := k
      v_reg := v
      score_exp_valid_in := true.B
    } .elsewhen(state === s_busy && norm_unit.valid_out) {
      state := s_idle
    }

    // Connect ScoreAndExpUnit_rq1 (Stage 1)
    score_exp_unit.clock := clock
    score_exp_unit.reset := reset
    score_exp_unit.valid_in := score_exp_valid_in
    score_exp_unit.q_in := q_reg
    score_exp_unit.k_in := k_reg

    // Connect DynaX_SelectionUnit (Stage 2)
    selection_unit.clock := clock
    selection_unit.reset := reset
    selection_unit.valid_in := score_exp_unit.valid_out
    selection_unit.scores_in := score_exp_unit.scores_out
    selection_unit.exponentials_in := score_exp_unit.exponentials_out

    // Delay lines for NormalizationUnit inputs
    // Latency of DynaX_SelectionUnit is 7 cycles.
    val exponentials_delayed = ShiftRegister(score_exp_unit.exponentials_out, 7, 0.U(256.W), true.B)
    
    // Latency of ScoreAndExpUnit_rq1 + DynaX_SelectionUnit is 7 + 7 = 14 cycles.
    val v_delayed = ShiftRegister(v_reg, 14, 0.U(128.W), true.B)

    // Connect NormalizationUnit_rq1 (Stage 3)
    norm_unit.clock := clock
    norm_unit.reset := reset
    norm_unit.valid_in := selection_unit.valid_out
    norm_unit.keep_mask_in := selection_unit.keep_mask_out
    norm_unit.exponentials_in := exponentials_delayed
    norm_unit.v_in := v_delayed

    // Delay line for keep_mask output to align with 'done'
    // Latency of NormalizationUnit_rq1 is 41 cycles.
    val keep_mask_delayed = ShiftRegister(selection_unit.keep_mask_out, 41, 0.U(16.W), true.B)

    // Connect top-level outputs
    done := norm_unit.valid_out
    result := norm_unit.result_out
    keep_mask := keep_mask_delayed
  }
}
