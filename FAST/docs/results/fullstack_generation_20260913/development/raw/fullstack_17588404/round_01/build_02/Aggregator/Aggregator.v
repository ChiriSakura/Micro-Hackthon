module Aggregator(
  input [8:0] w_in_0,
  input [8:0] w_in_1,
  input [8:0] w_in_2,
  input [8:0] w_in_3,
  input [12:0] wv_in_0,
  input [12:0] wv_in_1,
  input [12:0] wv_in_2,
  input [12:0] wv_in_3,
  output [10:0] sum_w_out,
  output [14:0] sum_wv_out
);

  // This module is purely combinational and implements two parallel 4-input
  // adder trees as described in the system plan.

  // Adder tree for weights (w_in)
  // Max w_in is 450 (9 bits). Max sum is 4 * 450 = 1800, which fits in 11 bits.
  // Stage 1: Two parallel 2-input additions. Sum of two 9-bit numbers needs 10 bits.
  wire [9:0] w_sum_01;
  wire [9:0] w_sum_23;
  assign w_sum_01 = w_in_0 + w_in_1;
  assign w_sum_23 = w_in_2 + w_in_3;

  // Stage 2: Add the intermediate sums. Sum of two 10-bit numbers needs 11 bits.
  assign sum_w_out = w_sum_01 + w_sum_23;

  // Adder tree for weighted values (wv_in)
  // Max wv_in is 6750 (13 bits). Max sum is 4 * 6750 = 27000, which fits in 15 bits.
  // Stage 1: Two parallel 2-input additions. Sum of two 13-bit numbers needs 14 bits.
  wire [13:0] wv_sum_01;
  wire [13:0] wv_sum_23;
  assign wv_sum_01 = wv_in_0 + wv_in_1;
  assign wv_sum_23 = wv_in_2 + wv_in_3;

  // Stage 2: Add the intermediate sums. Sum of two 14-bit numbers needs 15 bits.
  assign sum_wv_out = wv_sum_01 + wv_sum_23;

endmodule
