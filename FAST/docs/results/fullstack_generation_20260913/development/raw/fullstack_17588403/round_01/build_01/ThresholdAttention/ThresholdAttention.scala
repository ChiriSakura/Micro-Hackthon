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

  // Child modules
  val score_calc = Module(new ScoreCalculatorBank)
  val summer = Module(new Summer)
  val divider = Module(new Divider)

  // FSM states
  val s_idle :: s_pipe :: s_div_wait :: Nil = Enum(3)

  // Control and data registers
  val state_reg = withClockAndReset(clock, reset) { RegInit(s_idle) }
  val pipe_counter_reg = withClockAndReset(clock, reset) { RegInit(0.U(2.W)) }

  // Pipeline Stage 0 -> 1 (Input Registers)
  val q_reg = withClockAndReset(clock, reset) { Reg(UInt(8.W)) }
  val k_reg = withClockAndReset(clock, reset) { Reg(UInt(32.W)) }
  val v_reg = withClockAndReset(clock, reset) { Reg(UInt(16.W)) }

  // Pipeline Stage 1 -> 2
  val scores_reg = withClockAndReset(clock, reset) { Reg(UInt(36.W)) }
  val v_reg_p1 = withClockAndReset(clock, reset) { Reg(UInt(16.W)) }

  // Pipeline Stage 2 -> 3
  val weights_reg = withClockAndReset(clock, reset) { Reg(UInt(36.W)) }
  val weighted_vs_reg = withClockAndReset(clock, reset) { Reg(UInt(52.W)) }

  // Pipeline Stage 3 -> 4
  val sum_w_reg = withClockAndReset(clock, reset) { Reg(UInt(11.W)) }
  val sum_wv_reg = withClockAndReset(clock, reset) { Reg(UInt(15.W)) }

  // --- Combinational Logic ---

  // Stage 2: Thresholding and Multiplication
  val threshold = 64.U(9.W)
  val scores = Wire(Vec(4, UInt(9.W)))
  val vs = Wire(Vec(4, UInt(4.W)))
  val weights = Wire(Vec(4, UInt(9.W)))
  val weighted_vs = Wire(Vec(4, UInt(13.W)))

  for (i <- 0 until 4) {
    scores(i) := scores_reg(i * 9 + 8, i * 9)
    vs(i) := v_reg_p1(i * 4 + 3, i * 4)
    weights(i) := Mux(scores(i) >= threshold, scores(i), 0.U)
    weighted_vs(i) := weights(i) * vs(i)
  }
  val weights_in_next = Cat(weights(3), weights(2), weights(1), weights(0))
  val weighted_vs_in_next = Cat(weighted_vs(3), weighted_vs(2), weighted_vs(1), weighted_vs(0))

  // Connect child module inputs
  score_calc.q_in := q_reg
  score_calc.k_in := k_reg
  summer.weights_in := weights_reg
  summer.weighted_vs_in := weighted_vs_reg
  divider.clock := clock
  divider.reset := reset
  divider.numer_in := sum_wv_reg
  divider.denom_in := sum_w_reg

  // Control signals for FSM and outputs
  val is_pipe_at_end = (state_reg === s_pipe) && (pipe_counter_reg === 3.U)
  val is_zero_denom_case = is_pipe_at_end && (sum_w_reg === 0.U)
  val start_divider = is_pipe_at_end && (sum_w_reg =/= 0.U)
  val is_div_done = (state_reg === s_div_wait) && divider.done

  divider.start := start_divider
  done := is_zero_denom_case || is_div_done

  when (is_zero_denom_case) {
    result := 0.U
  } .elsewhen (is_div_done) {
    result := divider.quotient_out
  } .otherwise {
    result := 0.U
  }

  // --- Sequential Logic ---
  withClockAndReset(clock, reset) {
    // FSM state transitions and control register updates
    switch(state_reg) {
      is(s_idle) {
        when(start) {
          state_reg := s_pipe
          pipe_counter_reg := 0.U
        }
      }
      is(s_pipe) {
        pipe_counter_reg := pipe_counter_reg + 1.U
        when(pipe_counter_reg === 3.U) {
          when(sum_w_reg === 0.U) {
            state_reg := s_idle
          } .otherwise {
            state_reg := s_div_wait
          }
        }
      }
      is(s_div_wait) {
        when(divider.done) {
          state_reg := s_idle
        }
      }
    }

    // Pipeline register updates
    when(state_reg === s_idle && start) {
      // Stage 0: Latch inputs on start
      q_reg := q
      k_reg := k
      v_reg := v
    }

    when(state_reg === s_pipe) {
      // Stage 1 -> 2
      scores_reg := score_calc.scores_out
      v_reg_p1 := v_reg
      // Stage 2 -> 3
      weights_reg := weights_in_next
      weighted_vs_reg := weighted_vs_in_next
      // Stage 3 -> 4
      sum_w_reg := summer.sum_w_out
      sum_wv_reg := summer.sum_wv_out
    }
  }
}
