import chisel3._
import chisel3.util._

class ThresholdAttention extends RawModule {
  // IO ports
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(32.W)))
  val v = IO(Input(UInt(16.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(4.W)))

  // Child module instantiations
  val score_units = Seq.fill(4)(Module(new ScoreUnit))
  val agg_unit = Module(new AggregationUnit)
  val div_unit = Module(new UnsignedDivider)

  // FSM state and input registers
  val busy = withClockAndReset(clock, reset) { RegInit(false.B) }
  val q_reg = withClockAndReset(clock, reset) { RegInit(0.U(8.W)) }
  val k_reg = withClockAndReset(clock, reset) { RegInit(0.U(32.W)) }
  val v_reg = withClockAndReset(clock, reset) { RegInit(0.U(16.W)) }

  // FSM and pipeline control logic
  val can_start = !busy
  val will_start = can_start && start

  // A one-cycle pulse to start the first pipeline stage. It is registered to align
  // with the cycle where the input registers (q_reg, etc.) are updated.
  val pipeline_start = withClockAndReset(clock, reset) { RegNext(will_start, false.B) }

  // FSM state transitions and input latching
  withClockAndReset(clock, reset) {
    when(will_start) {
      busy := true.B
      q_reg := q
      k_reg := k
      v_reg := v
    } .elsewhen(div_unit.valid_out) {
      // The pipeline is done, return to idle
      busy := false.B
    }
  }

  // Stage 1: Score Units
  for (i <- 0 until 4) {
    score_units(i).clock := clock
    score_units(i).reset := reset
    score_units(i).valid_in := pipeline_start
    score_units(i).q_in := q_reg
    // Unpack the 32-bit k vector into four 8-bit key vectors
    score_units(i).k_in := k_reg(8 * (i + 1) - 1, 8 * i)
  }

  // Stage 2: Aggregation Unit
  // All score units have the same valid_out, so we can just use the first one.
  val scores_valid = score_units(0).valid_out

  // Concatenate the four 9-bit scores into a single 36-bit vector
  val scores_cat = Cat(
    score_units(3).score_out,
    score_units(2).score_out,
    score_units(1).score_out,
    score_units(0).score_out
  )

  agg_unit.clock := clock
  agg_unit.reset := reset
  agg_unit.valid_in := scores_valid
  agg_unit.scores_in := scores_cat
  agg_unit.values_in := v_reg

  // Stage 3: Unsigned Divider
  div_unit.clock := clock
  div_unit.reset := reset
  div_unit.valid_in := agg_unit.valid_out
  div_unit.numerator_in := agg_unit.weighted_value_sum_out
  div_unit.denominator_in := agg_unit.weight_sum_out

  // Top-level outputs
  // The 'done' signal is the valid output of the last pipeline stage.
  done := div_unit.valid_out
  // The 'result' is the quotient from the divider.
  result := div_unit.quotient_out
}
