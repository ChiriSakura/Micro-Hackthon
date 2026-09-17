import chisel3._
import chisel3.util._

class FindMin8 extends RawModule {
  val scores_in = IO(Input(UInt(72.W)))
  val keep_mask_out = IO(Output(UInt(8.W)))

  // Unpack the 72-bit input into a sequence of eight 9-bit signed integers.
  val scores = Seq.tabulate(8)(i => scores_in(9 * (i + 1) - 1, 9 * i).asSInt)

  // Pair each score with its original index (0-7).
  val scoresWithIndices = scores.zipWithIndex.map { case (score, i) => (score, i.U(3.W)) }

  // Helper function to find the minimum of two (score, index) pairs based on the specified tie-breaking rule.
  // The minimum is defined as the lower score, or the one with the larger index if scores are equal.
  def minSelect(a: (SInt, UInt), b: (SInt, UInt)): (SInt, UInt) = {
    val (score_a, index_a) = a
    val (score_b, index_b) = b

    val b_is_min = (score_b < score_a) || (score_b === score_a && index_b > index_a)

    val min_score = Mux(b_is_min, score_b, score_a)
    val min_index = Mux(b_is_min, index_b, index_a)

    (min_score, min_index)
  }

  // Stage 1 of the comparator tree: compare adjacent pairs.
  val min_01 = minSelect(scoresWithIndices(0), scoresWithIndices(1))
  val min_23 = minSelect(scoresWithIndices(2), scoresWithIndices(3))
  val min_45 = minSelect(scoresWithIndices(4), scoresWithIndices(5))
  val min_67 = minSelect(scoresWithIndices(6), scoresWithIndices(7))

  // Stage 2 of the comparator tree: compare results from stage 1.
  val min_0123 = minSelect(min_01, min_23)
  val min_4567 = minSelect(min_45, min_67)

  // Stage 3: Final comparison to find the overall minimum.
  val final_min = minSelect(min_0123, min_4567)

  // The index of the score to be discarded.
  val min_idx = final_min._2

  // Generate the output mask. A '0' at the position of the minimum score, '1's elsewhere.
  // This is equivalent to 255 - (1 << min_idx).
  keep_mask_out := ~(1.U(8.W) << min_idx)
}
