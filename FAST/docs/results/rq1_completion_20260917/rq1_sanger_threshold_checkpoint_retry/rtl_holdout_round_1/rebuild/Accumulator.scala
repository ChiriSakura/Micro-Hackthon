import chisel3._
import chisel3.util._

class Accumulator extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_input = IO(Input(Bool()))
  val v_in = IO(Input(UInt(128.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val keep_mask_in = IO(Input(UInt(16.W)))
  val valid_output = IO(Output(Bool()))
  val N_out = IO(Output(SInt(28.W)))
  val D_out = IO(Output(UInt(20.W)))

  withClockAndReset(clock, reset) {
    // --- Pipeline Valid Signals (5 stages) ---
    val s1_valid = RegNext(valid_input, false.B)
    val s2_valid = RegNext(s1_valid, false.B)
    val s3_valid = RegNext(s2_valid, false.B)
    val s4_valid = RegNext(s3_valid, false.B)
    val s5_valid = RegNext(s4_valid, false.B)
    valid_output := s5_valid

    // --- Stage 1: Masking and Input Registering ---
    val v_vec_in = v_in.asTypeOf(Vec(16, SInt(8.W)))
    val e_vec_in = exponentials_in.asTypeOf(Vec(16, UInt(16.W)))
    val keep_vec_in = keep_mask_in.asBools

    val s1_masked_e_wire = Wire(Vec(16, UInt(16.W)))
    for (i <- 0 until 16) {
      // Bit i of keep_mask_in corresponds to index i
      s1_masked_e_wire(i) := Mux(keep_vec_in(i), e_vec_in(i), 0.U)
    }
    
    val s1_v_reg = RegEnable(v_vec_in, VecInit(Seq.fill(16)(0.S(8.W))), valid_input)
    val s1_masked_e_reg = RegEnable(s1_masked_e_wire, VecInit(Seq.fill(16)(0.U(16.W))), valid_input)

    // --- Stage 2: Multiplier Input Register (1st stage of 2-stage multiplier) ---
    val s2_v_reg = RegEnable(s1_v_reg, VecInit(Seq.fill(16)(0.S(8.W))), s1_valid)
    val s2_masked_e_reg = RegEnable(s1_masked_e_reg, VecInit(Seq.fill(16)(0.U(16.W))), s1_valid)

    // --- Stage 3: Multiplication (2nd stage of 2-stage multiplier) ---
    val s3_prods_wire = Wire(Vec(16, SInt(25.W)))
    for (i <- 0 until 16) {
      // U16 (as positive S17) * S8 -> S25
      s3_prods_wire(i) := (Cat(0.U(1.W), s2_masked_e_reg(i)).asSInt * s2_v_reg(i))
    }
    
    val s3_prods_reg = RegEnable(s3_prods_wire, VecInit(Seq.fill(16)(0.S(25.W))), s2_valid)
    // Also delay the masked_e values for the D-path adder tree
    val s3_masked_e_reg = RegEnable(s2_masked_e_reg, VecInit(Seq.fill(16)(0.U(16.W))), s2_valid)

    // --- Stage 4: Adder Tree Level 1 (1st stage of 2-stage adder) ---
    // This stage reduces 16 inputs to 4 sums for both N and D paths.
    val n_sums_level1 = Wire(Vec(8, SInt(26.W)))
    for (i <- 0 until 8) { n_sums_level1(i) := s3_prods_reg(2*i) +& s3_prods_reg(2*i + 1) }
    val n_sums_level2 = Wire(Vec(4, SInt(27.W)))
    for (i <- 0 until 4) { n_sums_level2(i) := n_sums_level1(2*i) +& n_sums_level1(2*i + 1) }

    val d_sums_level1 = Wire(Vec(8, UInt(17.W)))
    for (i <- 0 until 8) { d_sums_level1(i) := s3_masked_e_reg(2*i) +& s3_masked_e_reg(2*i + 1) }
    val d_sums_level2 = Wire(Vec(4, UInt(18.W)))
    for (i <- 0 until 4) { d_sums_level2(i) := d_sums_level1(2*i) +& d_sums_level1(2*i + 1) }

    val s4_n_sums_reg = RegEnable(n_sums_level2, VecInit(Seq.fill(4)(0.S(27.W))), s3_valid)
    val s4_d_sums_reg = RegEnable(d_sums_level2, VecInit(Seq.fill(4)(0.U(18.W))), s3_valid)

    // --- Stage 5: Adder Tree Level 2 (2nd stage of 2-stage adder) ---
    // This stage reduces 4 inputs to the final sum.
    val n_sums_level3 = Wire(Vec(2, SInt(28.W)))
    for (i <- 0 until 2) { n_sums_level3(i) := s4_n_sums_reg(2*i) +& s4_n_sums_reg(2*i + 1) }
    val final_N_wire = n_sums_level3(0) +& n_sums_level3(1) // S29

    val d_sums_level3 = Wire(Vec(2, UInt(19.W)))
    for (i <- 0 until 2) { d_sums_level3(i) := s4_d_sums_reg(2*i) +& s4_d_sums_reg(2*i + 1) }
    val final_D_wire = d_sums_level3(0) +& d_sums_level3(1) // U20

    // Register the final outputs. For N, we take the lower 28 bits of the S29 result.
    // This is safe due to the `abs_weighted_value_sum_max` numeric bound.
    N_out := RegEnable(final_N_wire(27,0).asSInt, 0.S(28.W), s4_valid)
    D_out := RegEnable(final_D_wire, 0.U(20.W), s4_valid)
  }
}
