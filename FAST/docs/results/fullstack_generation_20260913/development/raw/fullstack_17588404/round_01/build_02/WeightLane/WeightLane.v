module WeightLane(
  input [8:0] score_in,
  input [3:0] v_in,
  output [8:0] weight_out,
  output [12:0] wv_out
);

  // This module is purely combinational. It has a local parameter `THRESHOLD`
  // set to 64. It compares `score_in` with `THRESHOLD`. If `score_in` is
  // greater than or equal to `THRESHOLD`, `weight_out` is assigned `score_in`;
  // otherwise, it is assigned 0. This 9-bit `weight_out` is then multiplied
  // by the 4-bit `v_in` using a 9x4-bit unsigned multiplier to produce the
  // 13-bit `wv_out`. The maximum product is 450 * 15 = 6750, which fits in 13 bits.

  localparam THRESHOLD = 9'd64;

  // Apply threshold to get the weight.
  assign weight_out = (score_in >= THRESHOLD) ? score_in : 9'b0;

  // Compute the weighted value.
  // The product of a 9-bit and a 4-bit number results in a 13-bit number.
  assign wv_out = weight_out * v_in;

endmodule
