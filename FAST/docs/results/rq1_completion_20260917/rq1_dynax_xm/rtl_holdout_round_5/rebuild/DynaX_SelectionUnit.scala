import chisel3._
import chisel3.util._

class DynaX_SelectionUnit extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_in = IO(Input(Bool()))
  val scores_in = IO(Input(UInt(144.W)))
  val exponentials_in = IO(Input(UInt(256.W)))
  val keep_mask_out = IO(Output(UInt(16.W)))
  val valid_out = IO(Output(Bool()))

  // Internal Record for sorting (score, index) pairs
  class ScoreIndexPair extends Bundle {
    val score = SInt(9.W)
    val index = UInt(4.W)
  }

  // Comparator function for two pairs, implementing descending score sort with smaller index as tie-breaker
  def compareAndSwap(a: ScoreIndexPair, b: ScoreIndexPair): (ScoreIndexPair, ScoreIndexPair) = {
    val greater = (a.score > b.score) || (a.score === b.score && a.index < b.index)
    val high = Mux(greater, a, b)
    val low = Mux(greater, b, a)
    (high, low)
  }

  // Combinational logic for one stage of a sorting network
  def applySorterStage(inputs: Vec[ScoreIndexPair], comparisons: Seq[(Int, Int)]): Vec[ScoreIndexPair] = {
    val outputs = Wire(Vec(inputs.length, new ScoreIndexPair))
    val connected = Array.fill(inputs.length)(false)

    for ((i, j) <- comparisons) {
      val (h, l) = compareAndSwap(inputs(i), inputs(j))
      outputs(i) := h
      outputs(j) := l
      connected(i) = true
      connected(j) = true
    }

    for (i <- inputs.indices) {
      if (!connected(i)) {
        outputs(i) := inputs(i)
      }
    }
    outputs
  }

  withClockAndReset(clock, reset) {
    val N1 = 7.U(4.W)
    val N2 = 4.U(4.W)
    val NUM_BLOCK_ITEMS = 8

    // --- Valid Pipeline (7 stages) ---
    val valid_pipe = RegInit(VecInit(Seq.fill(7)(false.B)))
    valid_pipe(0) := valid_in
    for (i <- 0 until 6) {
      valid_pipe(i + 1) := valid_pipe(i)
    }
    valid_out := valid_pipe(6)

    // --- Stage 0: Input Unpacking (Combinational) ---
    val scores = scores_in.asTypeOf(Vec(16, SInt(9.W)))
    val exponentials = exponentials_in.asTypeOf(Vec(16, UInt(16.W)))

    val block0_in = Wire(Vec(NUM_BLOCK_ITEMS, new ScoreIndexPair))
    val block1_in = Wire(Vec(NUM_BLOCK_ITEMS, new ScoreIndexPair))
    for (i <- 0 until NUM_BLOCK_ITEMS) {
      block0_in(i).score := scores(i)
      block0_in(i).index := i.U(4.W)
      block1_in(i).score := scores(i + NUM_BLOCK_ITEMS)
      block1_in(i).index := (i + NUM_BLOCK_ITEMS).U(4.W)
    }

    // --- Thresholding Pipeline (7 stages of registers) ---
    // Stage 1
    val exp_b0_s1 = RegNext(VecInit(Seq.tabulate(4)(i => exponentials(2 * i) +& exponentials(2 * i + 1))))
    val exp_b1_s1 = RegNext(VecInit(Seq.tabulate(4)(i => exponentials(8 + 2 * i) +& exponentials(8 + 2 * i + 1))))
    // Stage 2
    val exp_b0_s2 = RegNext(VecInit(Seq.tabulate(2)(i => exp_b0_s1(2 * i) +& exp_b0_s1(2 * i + 1))))
    val exp_b1_s2 = RegNext(VecInit(Seq.tabulate(2)(i => exp_b1_s1(2 * i) +& exp_b1_s1(2 * i + 1))))
    // Stage 3
    val b0_s3 = RegNext(exp_b0_s2(0) +& exp_b0_s2(1), 0.U(20.W))
    val b1_s3 = RegNext(exp_b1_s2(0) +& exp_b1_s2(1), 0.U(20.W))
    // Stage 4
    val s_s4 = RegNext(b0_s3 +& b1_s3, 0.U(21.W))
    val b0_s4 = RegNext(b0_s3, 0.U(20.W))
    val b1_s4 = RegNext(b1_s3, 0.U(20.W))
    // Stage 5
    val k0_s5 = RegNext(Mux((b0_s4 << 2) > s_s4, N1, N2), 0.U(4.W))
    val k1_s5 = RegNext(Mux((b1_s4 << 2) > s_s4, N1, N2), 0.U(4.W))
    // Stage 6
    val k0_s6 = RegNext(k0_s5, 0.U(4.W))
    val k1_s6 = RegNext(k1_s5, 0.U(4.W))
    // Stage 7
    val final_k0 = RegNext(k0_s6, 0.U(4.W))
    val final_k1 = RegNext(k1_s6, 0.U(4.W))

    // --- Sorter Pipeline (7 stages of registers) ---
    val comparisons = Seq(
      Seq((0, 1), (2, 3), (4, 5), (6, 7)), // Stage 1
      Seq((0, 2), (1, 3), (4, 6), (5, 7)), // Stage 2
      Seq((1, 2), (5, 6)),                 // Stage 3
      Seq((0, 4), (1, 5), (2, 6), (3, 7)), // Stage 4
      Seq((2, 4), (3, 5)),                 // Stage 5
      Seq((1, 2), (3, 4), (5, 6))          // Stage 6
    )

    // FIX: The Wire Vecs should be size 6, not 7.
    val s0_pipe = Wire(Vec(6, Vec(NUM_BLOCK_ITEMS, new ScoreIndexPair)))
    val s1_pipe = Wire(Vec(6, Vec(NUM_BLOCK_ITEMS, new ScoreIndexPair)))

    val defaultPair = 0.U.asTypeOf(new ScoreIndexPair)
    val defaultVec = VecInit(Seq.fill(NUM_BLOCK_ITEMS)(defaultPair))

    s0_pipe(0) := RegNext(applySorterStage(block0_in, comparisons(0)), defaultVec)
    s1_pipe(0) := RegNext(applySorterStage(block1_in, comparisons(0)), defaultVec)

    for (stage <- 1 until 6) {
      s0_pipe(stage) := RegNext(applySorterStage(s0_pipe(stage - 1), comparisons(stage)), defaultVec)
      s1_pipe(stage) := RegNext(applySorterStage(s1_pipe(stage - 1), comparisons(stage)), defaultVec)
    }

    val final_sorted_b0 = RegNext(s0_pipe(5), defaultVec)
    val final_sorted_b1 = RegNext(s1_pipe(5), defaultVec)

    // --- Final Stage (Combinational Output Logic) ---
    val mask_b0 = (0 until NUM_BLOCK_ITEMS).map { i =>
      Mux(i.U < final_k0, 1.U << final_sorted_b0(i).index, 0.U)
    }.reduce(_ | _)

    val mask_b1 = (0 until NUM_BLOCK_ITEMS).map { i =>
      Mux(i.U < final_k1, 1.U << final_sorted_b1(i).index, 0.U)
    }.reduce(_ | _)

    keep_mask_out := Mux(valid_out, mask_b0 | mask_b1, 0.U)
  }
}
