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

  val score_weight_gen = Module(new ScoreWeightGen)
  val select_accumulate = Module(new SelectAccumulate)
  val divider_wrapper = Module(new DividerWrapper)

  // Connect clocks and resets to children (RawModule style, no .io)
  score_weight_gen.clock := clock
  score_weight_gen.reset := reset
  select_accumulate.clock := clock
  select_accumulate.reset := reset
  divider_wrapper.clock := clock
  divider_wrapper.reset := reset

  withClockAndReset(clock, reset) {
    val sIdle :: sBusy :: sDone :: Nil = Enum(3)
    val state = RegInit(sIdle)

    val swg_start = WireDefault(false.B)
    val div_valid_out = divider_wrapper.valid_out

    // FSM
    done := false.B
    switch(state) {
      is(sIdle) {
        when(start) {
          state := sBusy
          swg_start := true.B
        }
      }
      is(sBusy) {
        when(div_valid_out) {
          state := sDone
        }
      }
      is(sDone) {
        done := true.B
        state := sIdle
      }
    }

    // --- Pipeline --- //

    // Stage 0 -> 1: ScoreWeightGen (Latency 3)
    score_weight_gen.start := swg_start
    score_weight_gen.q_in := q
    score_weight_gen.k_in := k

    // Pipeline Register 1 (1 cycle delay)
    val sa_valid_in = RegNext(score_weight_gen.valid_out, false.B)
    val scores_in_sa = RegNext(score_weight_gen.scores_out)
    val weights_in_sa = RegNext(score_weight_gen.weights_out)
    
    // Delay v by 4 cycles (3 for SWG + 1 for pipe reg) to align with scores/weights
    val v_p1 = RegEnable(v, swg_start)
    val v_p2 = RegNext(v_p1)
    val v_p3 = RegNext(v_p2)
    val v_p4 = RegNext(v_p3)

    // Stage 1 -> 2: SelectAccumulate (Latency 5)
    select_accumulate.valid_in := sa_valid_in
    select_accumulate.scores_in := scores_in_sa
    select_accumulate.weights_in := weights_in_sa
    select_accumulate.values_in := v_p4

    // Pipeline Register 2 (1 cycle delay)
    val div_valid_in = RegNext(select_accumulate.valid_out, false.B)
    val N_in_div = RegNext(select_accumulate.N_out)
    val D_in_div = RegNext(select_accumulate.D_out)

    // Stage 2 -> 3: DividerWrapper (Latency 16)
    divider_wrapper.valid_in := div_valid_in
    divider_wrapper.N_in := N_in_div
    divider_wrapper.D_in := D_in_div

    // --- Output Alignment --- //

    // Delay keep_mask by 17 cycles (1 for pipe reg 2 + 16 for divider).
    val keep_mask_delayed = ShiftRegister(select_accumulate.keep_mask_out, 17)

    // Final output registers, updated when divider is done
    val result_reg = Reg(UInt(16.W))
    val keep_mask_reg = Reg(UInt(8.W))

    when(div_valid_out) {
      result_reg := divider_wrapper.result_out
      keep_mask_reg := keep_mask_delayed
    }

    result := result_reg
    keep_mask := keep_mask_reg
  }
}
