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

  // Adder tree for weights (sum of four 9-bit numbers)
  // Max value: 4 * (2^9 - 1) = 2044. Requires 11 bits (2^11 - 1 = 2047).
  wire [9:0] w_sum_01;
  wire [9:0] w_sum_23;

  // Level 1 of the adder tree
  assign w_sum_01 = w_in_0 + w_in_1;
  assign w_sum_23 = w_in_2 + w_in_3;

  // Level 2 of the adder tree
  assign sum_w_out = w_sum_01 + w_sum_23;

  // Adder tree for weighted values (sum of four 13-bit numbers)
  // Max value: 4 * (2^13 - 1) = 32764. Requires 15 bits (2^15 - 1 = 32767).
  wire [13:0] wv_sum_01;
  wire [13:0] wv_sum_23;

  // Level 1 of the adder tree
  assign wv_sum_01 = wv_in_0 + wv_in_1;
  assign wv_sum_23 = wv_in_2 + wv_in_3;

  // Level 2 of the adder tree
  assign sum_wv_out = wv_sum_01 + wv_sum_23;

endmodule
