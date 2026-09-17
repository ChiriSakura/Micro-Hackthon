import chisel3._
import chisel3.util._

class rq1_global_topk extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(128.W)))
  val v = IO(Input(UInt(128.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(UInt(16.W)))
  val keep_mask = IO(Output(UInt(16.W)))

  // Child module instantiation
  val score_calc = Module(new ScoreCalculator)
  val exp_lut = Module(new ExpLut)
  val divider = Module(new FinalDivider)

  // Connect clock and reset for sequential child modules
  divider.clock := clock
  divider.reset := reset

  // FSM states
  val s_idle :: s_calc_scores :: s_find_h_and_loser :: s_accumulate :: s_divide_start :: s_divide_wait :: s_done :: Nil = Enum(7)
  val state = withClockAndReset(clock, reset) { RegInit(s_idle) }

  // Storage Registers
  val q_reg = withClockAndReset(clock, reset) { Reg(UInt(8.W)) }
  val k_reg = withClockAndReset(clock, reset) { Reg(UInt(128.W)) }
  val v_reg = withClockAndReset(clock, reset) { Reg(UInt(128.W)) }
  
  val score_regs = withClockAndReset(clock, reset) { Reg(Vec(16, SInt(9.W))) }
  val h_reg = withClockAndReset(clock, reset) { Reg(SInt(9.W)) }
  val min_score_reg = withClockAndReset(clock, reset) { Reg(SInt(9.W)) }
  val loser_idx_reg = withClockAndReset(clock, reset) { Reg(UInt(4.W)) }
  
  val N_reg = withClockAndReset(clock, reset) { Reg(SInt(28.W)) }
  val D_reg = withClockAndReset(clock, reset) { Reg(UInt(20.W)) }
  
  val cycle_counter = withClockAndReset(clock, reset) { Reg(UInt(4.W)) }
  
  // Output registers
  val result_reg = withClockAndReset(clock, reset) { Reg(UInt(16.W)) }
  val keep_mask_reg = withClockAndReset(clock, reset) { Reg(UInt(16.W)) }
  val done_reg = withClockAndReset(clock, reset) { RegInit(false.B) }

  // Connect outputs
  done := done_reg
  result := result_reg
  keep_mask := keep_mask_reg

  // --- Default assignments ---
  divider.valid_in := false.B
  
  // --- Combinational Logic for connecting to child modules ---
  val k_vec = k_reg.asTypeOf(Vec(16, UInt(8.W)))
  val v_vec = v_reg.asTypeOf(Vec(16, SInt(8.W)))

  score_calc.q_in := q_reg
  score_calc.k_in := k_vec(cycle_counter)

  val delta = (h_reg - score_regs(cycle_counter)).asUInt
  exp_lut.delta := delta(7, 0)

  divider.numer := N_reg.asUInt
  divider.denom := D_reg

  // --- FSM Logic ---
  // The done signal is a one-cycle pulse. It is set to true in s_done, 
  // and the FSM immediately transitions to s_idle where it is set to false again by default.
  done_reg := false.B

  switch(state) {
    is(s_idle) {
      when(start) {
        state := s_calc_scores
        q_reg := q
        k_reg := k
        v_reg := v
        cycle_counter := 0.U
        N_reg := 0.S
        D_reg := 0.U
        // Initialize h_reg to SInt 9-bit minimum (-256)
        h_reg := (-256).S(9.W)
        // Initialize min_score_reg to SInt 9-bit maximum (255)
        min_score_reg := 255.S(9.W)
        loser_idx_reg := 0.U // Will be overwritten
      }
    }

    is(s_calc_scores) {
      score_regs(cycle_counter) := score_calc.score_out
      val next_counter = cycle_counter + 1.U
      cycle_counter := next_counter
      when(cycle_counter === 15.U) {
        state := s_find_h_and_loser
        cycle_counter := 0.U
      }
    }

    is(s_find_h_and_loser) {
      val current_score = score_regs(cycle_counter)
      
      when(current_score > h_reg) { 
        h_reg := current_score 
      }
      
      // Tie-break for loser by picking LARGER index
      when(current_score <= min_score_reg) {
        min_score_reg := current_score
        loser_idx_reg := cycle_counter
      }
      
      val next_counter = cycle_counter + 1.U
      cycle_counter := next_counter
      when(cycle_counter === 15.U) {
        state := s_accumulate
        cycle_counter := 0.U
      }
    }

    is(s_accumulate) {
      val e_i = exp_lut.exp_val
      val current_v = v_vec(cycle_counter)
      // e_i is UInt(16), current_v is SInt(8).
      // e_i.zext returns SInt(17). Product is SInt(25).
      val product = e_i.zext * current_v

      when(cycle_counter =/= loser_idx_reg) {
        // N_reg is SInt(28). Chisel's '+' operator automatically sign-extends 'product'.
        N_reg := N_reg + product
        D_reg := D_reg + e_i
      }
      
      val next_counter = cycle_counter + 1.U
      cycle_counter := next_counter
      when(cycle_counter === 15.U) {
        state := s_divide_start
      }
    }

    is(s_divide_start) {
      divider.valid_in := true.B
      state := s_divide_wait
    }

    is(s_divide_wait) {
      when(divider.valid_out) {
        state := s_done
        result_reg := divider.quotient
        keep_mask_reg := ~(1.U(16.W) << loser_idx_reg)
      }
    }

    is(s_done) {
      done_reg := true.B
      state := s_idle
    }
  }
}
