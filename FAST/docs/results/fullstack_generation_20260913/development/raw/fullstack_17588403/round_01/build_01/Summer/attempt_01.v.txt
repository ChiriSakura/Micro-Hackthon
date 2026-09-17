import chisel3._

class Summer extends RawModule {
  val weights_in = IO(Input(UInt(36.W)))
  val weighted_vs_in = IO(Input(UInt(52.W)))
  val sum_w_out = IO(Output(UInt(11.W)))
  val sum_wv_out = IO(Output(UInt(15.W)))

  // Unpack weights_in into four 9-bit weights (w0, w1, w2, w3)
  val w0 = weights_in(8, 0)
  val w1 = weights_in(17, 9)
  val w2 = weights_in(26, 18)
  val w3 = weights_in(35, 27)

  // Unpack weighted_vs_in into four 13-bit weighted values (wv0, wv1, wv2, wv3)
  val wv0 = weighted_vs_in(12, 0)
  val wv1 = weighted_vs_in(25, 13)
  val wv2 = weighted_vs_in(38, 26)
  val wv3 = weighted_vs_in(51, 39)

  // --- Weight Summation Adder Tree ---
  // First level of additions (9b + 9b) produces two 10-bit intermediate sums.
  val sum_w_01 = w0 + w1
  val sum_w_23 = w2 + w3

  // Second level adds the two 10-bit values to produce the final 11-bit sum.
  sum_w_out := sum_w_01 + sum_w_23

  // --- Weighted Value Summation Adder Tree ---
  // First level of additions (13b + 13b) produces two 14-bit intermediate sums.
  val sum_wv_01 = wv0 + wv1
  val sum_wv_23 = wv2 + wv3

  // Second level adds the two 14-bit values to produce the final 15-bit sum.
  sum_wv_out := sum_wv_01 + sum_wv_23
}
