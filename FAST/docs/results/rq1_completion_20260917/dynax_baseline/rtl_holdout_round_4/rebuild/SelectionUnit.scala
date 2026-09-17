import chisel3._
import chisel3.util._

class SelectionUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val scores_in = IO(Input(UInt(144.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val keep_mask_out = IO(Output(UInt(16.W)))
  val exponentials_passthru = IO(Output(UInt(256.W)))
  val valid_out = IO(Output(Bool()))

  class ScoreIndex extends Bundle {
    val score = SInt(9.W)
    val index = UInt(4.W)
  }

  withClockAndReset(clock, reset) {

    def ShiftRegister[T <: Data](in: T, cycles: Int, init: T): T = {
      (0 until cycles).foldLeft(in)((i, _) => RegNext(i, init))
    }

    // --- Global Pipelines (12 cycles) ---
    valid_out := ShiftRegister(valid_in, 12, false.B)
    exponentials_passthru := ShiftRegister(exponentials_in, 12, 0.U(256.W))

    // --- Stage 0: Input Unpacking ---
    val exponentials = VecInit(Seq.tabulate(16)(i => exponentials_in(16 * i + 15, 16 * i)))
    val scores = VecInit(Seq.tabulate(16)(i => scores_in(9 * i + 8, 9 * i).asSInt))

    // --- Summation Pipeline (Stages 1-5) ---
    val s1_sums_reg = RegNext(VecInit(Seq.tabulate(8)(i => exponentials(2*i) +& exponentials(2*i+1))))
    val s2_sums_reg = RegNext(VecInit(Seq.tabulate(4)(i => s1_sums_reg(2*i) +& s1_sums_reg(2*i+1))))
    val s3_b0_reg = RegNext(s2_sums_reg(0) +& s2_sums_reg(1))
    val s3_b1_reg = RegNext(s2_sums_reg(2) +& s2_sums_reg(3))
    val s4_b0_reg = RegNext(s3_b0_reg)
    val s4_b1_reg = RegNext(s3_b1_reg)
    val s4_s_reg = RegNext(s3_b0_reg +& s3_b1_reg)

    val s5_b0 = RegNext(s4_b0_reg)
    val s5_b1 = RegNext(s4_b1_reg)
    val s5_s = RegNext(s4_s_reg)
    val k0_s5 = Mux((s5_b0 << 2) > s5_s, 8.U(4.W), 7.U(4.W))
    val k1_s5 = Mux((s5_b1 << 2) > s5_s, 8.U(4.W), 7.U(4.W))

    // --- Sorter Input Preparation (delay scores to stage 5) ---
    val scores_s5 = ShiftRegister(scores, 5, VecInit(Seq.fill(16)(0.S(9.W))))

    def createPipelinedSorter(sorter_input: Vec[ScoreIndex]): Vec[ScoreIndex] = {
      def compareAndSwap(a: ScoreIndex, b: ScoreIndex, descending: Bool): (ScoreIndex, ScoreIndex) = {
        val a_is_greater = (a.score > b.score) || (a.score === b.score && a.index < b.index)
        val swap = a_is_greater =/= descending
        (Mux(swap, b, a), Mux(swap, a, b))
      }

      var stage_data = sorter_input

      // Stage 1 of sorter
      val s1_out = Wire(Vec(8, new ScoreIndex))
      val (s1_0, s1_1) = compareAndSwap(stage_data(0), stage_data(1), true.B); s1_out(0) := s1_0; s1_out(1) := s1_1
      val (s1_2, s1_3) = compareAndSwap(stage_data(2), stage_data(3), false.B); s1_out(2) := s1_2; s1_out(3) := s1_3
      val (s1_4, s1_5) = compareAndSwap(stage_data(4), stage_data(5), true.B); s1_out(4) := s1_4; s1_out(5) := s1_5
      val (s1_6, s1_7) = compareAndSwap(stage_data(6), stage_data(7), false.B); s1_out(6) := s1_6; s1_out(7) := s1_7
      stage_data = RegNext(s1_out)

      // Stage 2 of sorter
      val s2_out = Wire(Vec(8, new ScoreIndex))
      val (s2_0, s2_2) = compareAndSwap(stage_data(0), stage_data(2), true.B); s2_out(0) := s2_0; s2_out(2) := s2_2
      val (s2_1, s2_3) = compareAndSwap(stage_data(1), stage_data(3), true.B); s2_out(1) := s2_1; s2_out(3) := s2_3
      val (s2_4, s2_6) = compareAndSwap(stage_data(4), stage_data(6), false.B); s2_out(4) := s2_4; s2_out(6) := s2_6
      val (s2_5, s2_7) = compareAndSwap(stage_data(5), stage_data(7), false.B); s2_out(5) := s2_5; s2_out(7) := s2_7
      stage_data = RegNext(s2_out)

      // Stage 3 of sorter
      val s3_out = Wire(Vec(8, new ScoreIndex))
      val (s3_0, s3_1) = compareAndSwap(stage_data(0), stage_data(1), true.B); s3_out(0) := s3_0; s3_out(1) := s3_1
      val (s3_2, s3_3) = compareAndSwap(stage_data(2), stage_data(3), true.B); s3_out(2) := s3_2; s3_out(3) := s3_3
      val (s3_4, s3_5) = compareAndSwap(stage_data(4), stage_data(5), false.B); s3_out(4) := s3_4; s3_out(5) := s3_5
      val (s3_6, s3_7) = compareAndSwap(stage_data(6), stage_data(7), false.B); s3_out(6) := s3_6; s3_out(7) := s3_7
      stage_data = RegNext(s3_out)

      // Stage 4 of sorter
      val s4_out = Wire(Vec(8, new ScoreIndex))
      for (i <- 0 until 4) {
        val (hi, lo) = compareAndSwap(stage_data(i), stage_data(i + 4), true.B)
        s4_out(i) := hi
        s4_out(i + 4) := lo
      }
      stage_data = RegNext(s4_out)

      // Stage 5 of sorter
      val s5_out = Wire(Vec(8, new ScoreIndex))
      val (s5_0, s5_2) = compareAndSwap(stage_data(0), stage_data(2), true.B); s5_out(0) := s5_0; s5_out(2) := s5_2
      val (s5_1, s5_3) = compareAndSwap(stage_data(1), stage_data(3), true.B); s5_out(1) := s5_1; s5_out(3) := s5_3
      val (s5_4, s5_6) = compareAndSwap(stage_data(4), stage_data(6), true.B); s5_out(4) := s5_4; s5_out(6) := s5_6
      val (s5_5, s5_7) = compareAndSwap(stage_data(5), stage_data(7), true.B); s5_out(5) := s5_5; s5_out(7) := s5_7
      stage_data = RegNext(s5_out)

      // Stage 6 of sorter
      val s6_out = Wire(Vec(8, new ScoreIndex))
      for (i <- 0 until 4) {
        val (hi, lo) = compareAndSwap(stage_data(2 * i), stage_data(2 * i + 1), true.B)
        s6_out(2 * i) := hi
        s6_out(2 * i + 1) := lo
      }
      RegNext(s6_out)
    }

    val block0_s5_in = Wire(Vec(8, new ScoreIndex))
    val block1_s5_in = Wire(Vec(8, new ScoreIndex))
    for (i <- 0 until 8) {
      block0_s5_in(i).score := scores_s5(i)
      block0_s5_in(i).index := i.U(4.W)
      block1_s5_in(i).score := scores_s5(i + 8)
      block1_s5_in(i).index := (i + 8).U(4.W)
    }

    // Sorter Pipelines (6 stages, from cycle 5 to 11)
    val sorted_b0_s11 = createPipelinedSorter(block0_s5_in)
    val sorted_b1_s11 = createPipelinedSorter(block1_s5_in)

    // k-value Pipeline (6 stages, from cycle 5 to 11)
    val k0_s11 = ShiftRegister(k0_s5, 6, 7.U(4.W))
    val k1_s11 = ShiftRegister(k1_s5, 6, 7.U(4.W))

    // --- Stage 11: Mask Generation ---
    val keep_mask_bits = Wire(Vec(16, Bool()))
    keep_mask_bits.foreach(_ := false.B)

    for (i <- 0 until 8) {
      when(i.U < k0_s11) {
        keep_mask_bits(sorted_b0_s11(i).index) := true.B
      }
      when(i.U < k1_s11) {
        keep_mask_bits(sorted_b1_s11(i).index) := true.B
      }
    }

    // --- Stage 12: Output Registration ---
    keep_mask_out := RegNext(keep_mask_bits.asUInt, 0.U)
  }
}
