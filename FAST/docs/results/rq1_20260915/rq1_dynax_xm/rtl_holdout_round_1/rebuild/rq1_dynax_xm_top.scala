import chisel3._
import chisel3.util._

class rq1_dynax_xm_top extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(128.W)))
  val v = IO(Input(UInt(128.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(16.W)))
  val keep_mask = IO(Output(UInt(16.W)))

  val score_unit = Module(new ScoreAndExpUnit())
  val selection_unit = Module(new SelectionUnit())
  val normalization_unit = Module(new NormalizationUnit())

  withClockAndReset(clock, reset) {
    // FSM
    val sIdle :: sCompute :: Nil = Enum(2)
    val state = RegInit(sIdle)
    val pipeline_latency = 60
    val counter = RegInit(0.U(log2Ceil(pipeline_latency).W))

    val start_pulse = (state === sIdle) && start
    done := (state === sCompute) && (counter === (pipeline_latency - 1).U)

    switch(state) {
      is(sIdle) {
        when(start) {
          state := sCompute
          counter := 0.U
        }
      }
      is(sCompute) {
        counter := counter + 1.U
        when(done) {
          state := sIdle
        }
      }
    }

    // Latch v input on start. q and k are fed directly, relying on the protocol
    // that inputs are stable until done.
    val v_reg = RegEnable(v, 0.U(128.W), start_pulse)

    // Connect ScoreAndExpUnit (Latency: 7)
    score_unit.clock := clock
    score_unit.reset := reset
    score_unit.valid_in := start_pulse
    score_unit.q_in := q
    score_unit.k_in := k

    // Pipeline Register 1 (Latency: 1)
    val scores_reg1 = RegNext(score_unit.scores_out, 0.U)
    val exps_reg1 = RegNext(score_unit.exponentials_out, 0.U)
    val valid_reg1 = RegNext(score_unit.valid_out, false.B)

    // Connect SelectionUnit (Latency: 10)
    selection_unit.clock := clock
    selection_unit.reset := reset
    selection_unit.valid_in := valid_reg1
    selection_unit.scores_in := scores_reg1
    selection_unit.exponentials_in := exps_reg1

    // Pipeline Register 2 (Latency: 1)
    val keep_mask_reg2 = RegNext(selection_unit.keep_mask_out, 0.U)
    val exps_reg2 = RegNext(selection_unit.exponentials_out, 0.U)
    val valid_reg2 = RegNext(selection_unit.valid_out, false.B)

    // Delay `v` input for NormalizationUnit.
    // Latency to norm_unit valid_in: 7(Score) + 1(Reg) + 10(Select) + 1(Reg) = 19 cycles.
    // v is latched at cycle 0, available in v_reg at cycle 1. It needs to be delayed
    // by 18 cycles to arrive at cycle 19.
    val v_delayed = (0 until 18).foldLeft(v_reg)((in, _) => RegNext(in, 0.U(128.W)))

    // Connect NormalizationUnit (Latency: 41)
    normalization_unit.clock := clock
    normalization_unit.reset := reset
    normalization_unit.valid_in := valid_reg2
    normalization_unit.keep_mask_in := keep_mask_reg2
    normalization_unit.exponentials_in := exps_reg2
    normalization_unit.v_in := v_delayed

    // Delay `keep_mask` for final output.
    // `keep_mask_reg2` is valid at cycle 19.
    // `done` is at cycle 59.
    // Delay needed = 59 - 19 = 40 cycles.
    val keep_mask_final = (0 until 40).foldLeft(keep_mask_reg2)((in, _) => RegNext(in, 0.U(16.W)))

    // Final outputs
    result := normalization_unit.result_out
    keep_mask := keep_mask_final
  }
}
