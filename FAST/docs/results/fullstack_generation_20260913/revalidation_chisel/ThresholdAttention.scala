import chisel3._
import chisel3.util._

class ThresholdAttention extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(32.W)))
  val v = IO(Input(UInt(16.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(4.W)))

  // FSM states as defined in the plan
  val sIdle :: sCompute :: sDivide :: sWaitDivide :: sDone :: Nil = Enum(5)

  withClockAndReset(clock, reset) {
    val state = RegInit(sIdle)

    // Registers for latched inputs
    val q_reg = Reg(UInt(8.W))
    val k_reg = Reg(UInt(32.W))
    val v_reg = Reg(UInt(16.W))

    // Registers for control and accumulation
    val idx_reg = Reg(UInt(2.W)) // 2 bits for 0..3
    val weight_sum_reg = RegInit(0.U(11.W))
    val weighted_value_sum_reg = RegInit(0.U(15.W))
    val final_quotient_reg = RegInit(0.U(15.W))

    // Child module instantiation
    val score_weight_unit = Module(new ScoreAndWeightUnit)
    val divider = Module(new Divider15by11)

    // Connect clock and reset to stateful child module
    divider.clock := clock
    divider.reset := reset

    // Combinational logic to extract current key/value based on index
    val k_i = (k_reg >> (idx_reg << 3.U))(7, 0)
    val v_i = (v_reg >> (idx_reg << 2.U))(3, 0)

    // Connect inputs to the ScoreAndWeightUnit
    score_weight_unit.q_vec := q_reg
    score_weight_unit.k_vec := k_i
    score_weight_unit.threshold := 64.U(9.W) // Hardcoded as per config
    val current_weight = score_weight_unit.weight

    // Default assignments for divider inputs to avoid latches
    divider.start := false.B
    divider.dividend := weighted_value_sum_reg
    divider.divisor := weight_sum_reg

    // FSM logic
    switch(state) {
      is(sIdle) {
        when(start) {
          q_reg := q
          k_reg := k
          v_reg := v
          weight_sum_reg := 0.U
          weighted_value_sum_reg := 0.U
          idx_reg := 0.U
          state := sCompute
        }
      }
      is(sCompute) {
        // Accumulate using widening add (+&) and truncate, safe due to numeric_bounds
        weight_sum_reg := (weight_sum_reg +& current_weight)(10, 0)
        val weighted_prod = current_weight * v_i // 9b * 4b -> 13b
        weighted_value_sum_reg := (weighted_value_sum_reg +& weighted_prod)(14, 0)

        idx_reg := idx_reg + 1.U
        when(idx_reg === 3.U) {
          state := sDivide
        }
      }
      is(sDivide) {
        when(weight_sum_reg === 0.U) {
          final_quotient_reg := 0.U
          state := sDone
        } .otherwise {
          divider.start := true.B
          state := sWaitDivide
        }
      }
      is(sWaitDivide) {
        when(divider.valid_out) {
          final_quotient_reg := divider.quotient
          state := sDone
        }
      }
      is(sDone) {
        state := sIdle
      }
    }

    // Output assignments
    done := state === sDone
    result := final_quotient_reg(3, 0)
  }
}
