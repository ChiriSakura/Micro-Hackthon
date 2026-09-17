module ScoreLane(
  input [3:0] q0_in,
  input [3:0] q1_in,
  input [3:0] k0_in,
  input [3:0] k1_in,
  output [8:0] score_out
);

  wire [7:0] prod0;
  wire [7:0] prod1;

  assign prod0 = q0_in * k0_in;
  assign prod1 = q1_in * k1_in;

  // The sum of two 8-bit numbers requires a 9-bit result to avoid overflow.
  // The maximum value is (15*15) + (15*15) = 225 + 225 = 450, which fits in 9 bits (2^9-1 = 511).
  assign score_out = prod0 + prod1;

endmodule
