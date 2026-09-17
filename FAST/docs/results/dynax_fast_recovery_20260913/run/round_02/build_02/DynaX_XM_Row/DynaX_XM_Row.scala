import chisel3._
import chisel3.util._

class DynaX_XM_Row extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(64.W)))
  val v = IO(Input(UInt(64.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(16.W)))
  val keep_mask = IO(Output(UInt(8.W)))

  // Instantiate children
  val score_weight_gen = Module(new ScoreWeightGen)
  val select_accumulate = Module(new SelectAccumulate)
  val divider_wrapper = Module(new DividerWrapper)

  // Connect clocks and resets to children
  score_weight_gen.clock := clock
  score_weight_gen.reset := reset
  select_accumulate.clock := clock
  select_accumulate.reset := reset
  divider_wrapper.clock := clock
  divider_wrapper.reset := reset

  withClockAndReset(clock, reset) {
    // This module implements a simple, feed-forward pipeline connecting the three child modules.
    // The total latency is 18 cycles:
    // ScoreWeightGen (3) -> PipeReg (1) -> SelectAccumulate (5) -> PipeReg (1) -> DividerWrapper (8)

    // --- Pipeline Stage 1: ScoreWeightGen (Latency 3) ---
    // The ScoreWeightGen module latches its inputs on its 'start' signal.
    score_weight_gen.start := start
    score_weight_gen.q_in := q
    score_weight_gen.k_in := k

    // --- Pipeline Register 1 (1 cycle delay) ---
    // This register stage buffers the output of ScoreWeightGen before it enters SelectAccumulate.
    val sa_valid_in = RegNext(score_weight_gen.valid_out, false.B)
    val sa_scores_in = RegNext(score_weight_gen.scores_out, 0.U(72.W))
    val sa_weights_in = RegNext(score_weight_gen.weights_out, 0.U(128.W))

    // --- V Input Delay Path ---
    // The 'v' input needs to be delayed by 4 cycles to align with the data entering SelectAccumulate.
    // Delay = Latency of ScoreWeightGen (3) + Latency of Pipeline Register 1 (1) = 4 cycles.
    // A simple register chain is used. The first register is enabled by the 'start' pulse.
    val v_p1 = RegEnable(v, 0.U(64.W), start)
    val v_p2 = RegNext(v_p1, 0.U(64.W))
    val v_p3 = RegNext(v_p2, 0.U(64.W))
    val v_delayed_for_sa = RegNext(v_p3, 0.U(64.W))

    // --- Pipeline Stage 2: SelectAccumulate (Latency 5) ---
    select_accumulate.valid_in := sa_valid_in
    select_accumulate.scores_in := sa_scores_in
    select_accumulate.weights_in := sa_weights_in
    select_accumulate.values_in := v_delayed_for_sa

    // --- Pipeline Register 2 (1 cycle delay) ---
    // This register stage buffers the output of SelectAccumulate before it enters DividerWrapper.
    val div_valid_in = RegNext(select_accumulate.valid_out, false.B)
    val div_N_in = RegNext(select_accumulate.N_out, 0.U(28.W))
    val div_D_in = RegNext(select_accumulate.D_out, 0.U(19.W))

    // --- Keep Mask Delay Path ---
    // The 'keep_mask' is produced by SelectAccumulate and needs to be delayed to align with the 'result' from the DividerWrapper.
    // Delay required = Latency of Pipeline Register 2 (1) + Latency of DividerWrapper (8) = 9 cycles.
    // The previous attempt failed because it used an enable on the ShiftRegister, which prevented the value from propagating.
    // The correct implementation is a simple delay chain without an enable, which shifts every cycle.
    val keep_mask_delayed = ShiftRegister(select_accumulate.keep_mask_out, 9)

    // --- Pipeline Stage 3: DividerWrapper (Latency 8) ---
    divider_wrapper.valid_in := div_valid_in
    divider_wrapper.N_in := div_N_in
    divider_wrapper.D_in := div_D_in

    // --- Final Outputs ---
    // The 'done' signal is the valid output from the final pipeline stage.
    // 'result' and the delayed 'keep_mask' are valid at the same time as 'done', as per the contract.
    done := divider_wrapper.valid_out
    result := divider_wrapper.result_out
    keep_mask := keep_mask_delayed
  }
}
