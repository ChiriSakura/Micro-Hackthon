import chisel3._
import chisel3.util._

class SangerThresholdTop extends RawModule {
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
  val scoreArray = Module(new ScoreArray)
  val maxExpAndThreshold = Module(new MaxExpAndThreshold)
  val accumulator = Module(new Accumulator)
  val normalizer = Module(new Normalizer)

  // Connect clocks and resets to all children
  scoreArray.clock := clock
  scoreArray.reset := reset
  maxExpAndThreshold.clock := clock
  maxExpAndThreshold.reset := reset
  accumulator.clock := clock
  accumulator.reset := reset
  normalizer.clock := clock
  normalizer.reset := reset

  withClockAndReset(clock, reset) {
    // --- Control Logic ---

    // State machine for start/done handshaking
    val sIdle :: sBusy :: Nil = Enum(2)
    val state = RegInit(sIdle)

    // A 22-bit shift register to track the valid pulse through the 21-stage pipeline.
    // The total latency is 22 cycles from start assertion.
    val valid_sr = RegInit(0.U(22.W))
    val pipeline_done = valid_sr(21)

    // Input registers, latched on start
    val q_reg = Reg(UInt(8.W))
    val k_reg = Reg(UInt(128.W))
    val v_reg = Reg(UInt(128.W))

    // State machine logic
    switch(state) {
      is(sIdle) {
        when(start) {
          state := sBusy
          // Latch inputs
          q_reg := q
          k_reg := k
          v_reg := v
          // Inject a valid pulse into the pipeline tracker
          valid_sr := 1.U
        }
      }
      is(sBusy) {
        // Propagate the valid pulse
        valid_sr := valid_sr << 1
        when(pipeline_done) {
          state := sIdle
          // The shift register will naturally clear itself after one more shift
        }
      }
    }

    // --- Datapath and Pipeline Connections ---

    // Stage 1: ScoreArray (Latency 1 cycle)
    // Valid pulse at cycle 1 (relative to start at cycle 0)
    scoreArray.valid_input := valid_sr(0)
    scoreArray.q_in := q_reg
    scoreArray.k_in := k_reg

    // Stage 2: MaxExpAndThreshold (Latency 7 cycles)
    // Valid pulse at cycle 1 (SA input) + 1 (SA latency) = 2
    maxExpAndThreshold.valid_input := valid_sr(1)
    maxExpAndThreshold.scores_in := scoreArray.scores_out

    // Stage 3: Accumulator (Latency 5 cycles)
    // Valid pulse at cycle 2 (MET input) + 7 (MET latency) = 9
    accumulator.valid_input := valid_sr(8)
    accumulator.exponentials_in := maxExpAndThreshold.exponentials_out
    accumulator.keep_mask_in := maxExpAndThreshold.keep_mask_out
    
    // The 'v' input was latched at cycle 0 and is needed at cycle 9.
    // It must be delayed by 8 cycles relative to the start of the pipeline.
    val v_delayed = ShiftRegister(v_reg, 8)
    accumulator.v_in := v_delayed

    // Stage 4: Normalizer (Latency 8 cycles)
    // Valid pulse at cycle 9 (ACC input) + 5 (ACC latency) = 14
    normalizer.valid_input := valid_sr(13)
    normalizer.N_in := accumulator.N_out.asUInt
    normalizer.D_in := accumulator.D_out

    // --- Output Connections ---

    // The 'done' pulse is asserted when the pipeline completes.
    // Valid pulse at cycle 14 (NORM input) + 8 (NORM latency) = 22
    done := pipeline_done

    // The 'result' is available from the Normalizer at the end of the pipeline.
    // The Normalizer output is SInt, top-level port is UInt. Cast as needed.
    result := normalizer.result_out.asUInt

    // The 'keep_mask' is available from MaxExpAndThreshold at cycle 9.
    // It must be delayed to align with the 'result' and 'done' at cycle 22.
    // Delay needed = 22 - 9 = 13 cycles.
    val keep_mask_delayed = ShiftRegister(maxExpAndThreshold.keep_mask_out, 13)
    keep_mask := keep_mask_delayed
  }
}
