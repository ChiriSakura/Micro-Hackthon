module WeightLane(
  input [8:0] score_in,
  input [3:0] v_in,
  output [8:0] weight_out,
  output [12:0] wv_out
);

  localparam THRESHOLD = 9'd64;

  // Apply threshold: if score is below threshold, weight is 0.
  assign weight_out = (score_in >= THRESHOLD) ? score_in : 9'b0;

  // Compute weighted value: weight * v
  // The product of a 9-bit number and a 4-bit number requires 13 bits.
  // Max score_in is 450, max v_in is 15. Max product is 450 * 15 = 6750.
  // 2^12-1 = 4095, 2^13-1 = 8191. 13 bits are necessary and sufficient.
  assign wv_out = weight_out * v_in;

endmodule
