module ScoreLane(
  input [3:0] q0_in,
  input [3:0] q1_in,
  input [3:0] k0_in,
  input [3:0] k1_in,
  output [8:0] score_out
);

  // This module is purely combinational. It contains two 4x4-bit unsigned
  // multipliers to compute `prod0 = q0_in * k0_in` and `prod1 = q1_in * k1_in`.
  // The 8-bit results are then added together to produce the 9-bit `score_out`.
  // The maximum score is 15*15 + 15*15 = 450, which fits in 9 bits.
  // Verilog's context-determined expression width rules ensure the addition
  // is performed at the 9-bit width of the target, preventing overflow.

  assign score_out = (q0_in * k0_in) + (q1_in * k1_in);

endmodule
