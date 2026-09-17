import chisel3._
import chisel3.util._

class NormalizationUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val keep_mask_in = IO(Input(UInt(16.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val v_in = IO(Input(UInt(128.W)))
  val result_out = IO(Output(UInt(16.W)))
  val valid_out = IO(Output(Bool()))

  withClockAndReset(clock, reset) {
    // --- Constants and Type definitions ---
    val NUM_KEYS = 16
    val EXP_WIDTH = 16
    val V_WIDTH = 8
    
    // Arithmetically sound product of u16 * s8 is s25 (via u16.zext -> s17)
    val PROD_WIDTH = EXP_WIDTH + 1 + V_WIDTH 
    // Sum of 16 s25 products: 25 + log2(16) = 29
    val N_SUM_WIDTH = PROD_WIDTH + 4
    // Sum of 16 u16 exponentials: 16 + log2(16) = 20
    val D_SUM_WIDTH = EXP_WIDTH + 4

    val DIV_WIDTH = 32
    val DIVIDER_LATENCY = 33
    val PRE_DIV_LATENCY = 8

    // --- Pipeline Stages ---

    // Stage 1: Input Registers
    val valid_s1 = RegNext(valid_in, false.B)
    val exponentials_s1 = RegEnable(VecInit.tabulate(NUM_KEYS)(i => exponentials_in((i + 1) * EXP_WIDTH - 1, i * EXP_WIDTH)), valid_in)
    val vs_s1 = RegEnable(VecInit.tabulate(NUM_KEYS)(i => v_in((i + 1) * V_WIDTH - 1, i * V_WIDTH).asSInt), valid_in)
    val keep_mask_s1 = RegEnable(keep_mask_in, valid_in)

    // Stage 2: Multiplier Pipeline Register 1
    val valid_s2 = RegNext(valid_s1, false.B)
    val exponentials_s2 = RegEnable(exponentials_s1, VecInit.fill(NUM_KEYS)(0.U(EXP_WIDTH.W)), valid_s1)
    val vs_s2 = RegEnable(vs_s1, VecInit.fill(NUM_KEYS)(0.S(V_WIDTH.W)), valid_s1)
    val keep_mask_s2 = RegEnable(keep_mask_s1, 0.U(NUM_KEYS.W), valid_s1)

    // Stage 3: Multiplier Pipeline Register 2 (Products computed combinationally from S2)
    val valid_s3 = RegNext(valid_s2, false.B)
    val products_s3 = RegEnable(VecInit.tabulate(NUM_KEYS) { i => (exponentials_s2(i).zext * vs_s2(i)).asSInt }, VecInit.fill(NUM_KEYS)(0.S(PROD_WIDTH.W)), valid_s2)
    val exponentials_s3 = RegEnable(exponentials_s2, VecInit.fill(NUM_KEYS)(0.U(EXP_WIDTH.W)), valid_s2)
    val keep_mask_s3 = RegEnable(keep_mask_s2, 0.U(NUM_KEYS.W), valid_s2)

    // Stage 4: Masking and Adder Tree L1
    val valid_s4 = RegNext(valid_s3, false.B)
    val keep_mask_s3_vec = keep_mask_s3.asBools
    val masked_products = VecInit.tabulate(NUM_KEYS) { i => Mux(keep_mask_s3_vec(i), products_s3(i), 0.S(PROD_WIDTH.W)) }
    val masked_exponentials = VecInit.tabulate(NUM_KEYS) { i => Mux(keep_mask_s3_vec(i), exponentials_s3(i), 0.U(EXP_WIDTH.W)) }

    val n_sum_l1 = VecInit.tabulate(NUM_KEYS / 2)(i => (masked_products(2 * i) +& masked_products(2 * i + 1)).asSInt)
    val d_sum_l1 = VecInit.tabulate(NUM_KEYS / 2)(i => masked_exponentials(2 * i) +& masked_exponentials(2 * i + 1))
    
    val n_sum_l1_s4 = RegEnable(n_sum_l1, valid_s3)
    val d_sum_l1_s4 = RegEnable(d_sum_l1, valid_s3)

    // Stage 5: Adder Tree L2
    val valid_s5 = RegNext(valid_s4, false.B)
    val n_sum_l2 = VecInit.tabulate(NUM_KEYS / 4)(i => (n_sum_l1_s4(2 * i) +& n_sum_l1_s4(2 * i + 1)).asSInt)
    val d_sum_l2 = VecInit.tabulate(NUM_KEYS / 4)(i => d_sum_l1_s4(2 * i) +& d_sum_l1_s4(2 * i + 1))
    
    val n_sum_l2_s5 = RegEnable(n_sum_l2, valid_s4)
    val d_sum_l2_s5 = RegEnable(d_sum_l2, valid_s4)

    // Stage 6: Adder Tree L3
    val valid_s6 = RegNext(valid_s5, false.B)
    val n_sum_l3 = VecInit.tabulate(NUM_KEYS / 8)(i => (n_sum_l2_s5(2 * i) +& n_sum_l2_s5(2 * i + 1)).asSInt)
    val d_sum_l3 = VecInit.tabulate(NUM_KEYS / 8)(i => d_sum_l2_s5(2 * i) +& d_sum_l2_s5(2 * i + 1))
    
    val n_sum_l3_s6 = RegEnable(n_sum_l3, valid_s5)
    val d_sum_l3_s6 = RegEnable(d_sum_l3, valid_s5)

    // Stage 7: Adder Tree L4
    val valid_s7 = RegNext(valid_s6, false.B)
    val n_sum_l4 = (n_sum_l3_s6(0) +& n_sum_l3_s6(1)).asSInt
    val d_sum_l4 = d_sum_l3_s6(0) +& d_sum_l3_s6(1)
    
    val n_sum_s7 = RegEnable(n_sum_l4, 0.S(N_SUM_WIDTH.W), valid_s6)
    val d_sum_s7 = RegEnable(d_sum_l4, 0.U(D_SUM_WIDTH.W), valid_s6)

    // Stage 8: Divider Prep
    val valid_s8 = RegNext(valid_s7, false.B)
    val n_sum_s8 = RegEnable(n_sum_s7, 0.S(N_SUM_WIDTH.W), valid_s7)
    val d_sum_s8 = RegEnable(d_sum_s7, 0.U(D_SUM_WIDTH.W), valid_s7)

    // --- Divider (Stages 9-41, 33 cycles) ---
    class DivState extends Bundle {
      val remainder = UInt((DIV_WIDTH + 1).W)
      val quotient = UInt(DIV_WIDTH.W)
      val dividend = UInt(DIV_WIDTH.W)
      val divisor = UInt(DIV_WIDTH.W)
      val negative = Bool()
      val divideByZero = Bool()
      val valid = Bool()
    }

    val n_shifted = (n_sum_s8 << 4)(DIV_WIDTH - 1, 0).asSInt
    
    val initial_state = Wire(new DivState)
    initial_state.remainder := 0.U
    initial_state.quotient := 0.U
    initial_state.dividend := n_shifted.abs.asUInt
    initial_state.divisor := d_sum_s8
    initial_state.negative := n_shifted < 0.S
    initial_state.divideByZero := d_sum_s8 === 0.U
    initial_state.valid := valid_s8

    def step(state: DivState): DivState = {
      val next = Wire(new DivState)
      next := state
      
      val shifted_rem = Cat(state.remainder(DIV_WIDTH - 1, 0), state.dividend(DIV_WIDTH - 1))
      val trial = shifted_rem.asUInt -& state.divisor
      val fits = shifted_rem.asUInt >= state.divisor
      
      next.remainder := Mux(fits, trial(DIV_WIDTH, 0), shifted_rem)
      next.quotient := Cat(state.quotient(DIV_WIDTH - 2, 0), fits)
      next.dividend := Cat(state.dividend(DIV_WIDTH - 2, 0), 0.U(1.W))
      next
    }

    var carried = initial_state
    for (i <- 0 until DIVIDER_LATENCY) {
      val next_iter_state = if (i < DIV_WIDTH) step(carried) else carried
      carried = RegNext(next_iter_state, 0.U.asTypeOf(new DivState))
    }
    val final_state = carried

    // --- Output Stage ---
    val magnitude = final_state.quotient
    val signed_quotient = Mux(final_state.negative, -magnitude.asSInt, magnitude.asSInt)
    val result_s32 = Mux(final_state.divideByZero, 0.S(DIV_WIDTH.W), signed_quotient)

    result_out := result_s32(15, 0).asUInt
    valid_out := final_state.valid
  }
}
