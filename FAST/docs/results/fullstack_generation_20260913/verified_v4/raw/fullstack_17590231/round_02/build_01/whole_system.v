module ScoreAndWeightUnit(
  input  [7:0] q_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 5:17]
  input  [7:0] k_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 6:17]
  output [8:0] weight // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 8:18]
);
  wire [3:0] q0 = q_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 11:17]
  wire [3:0] q1 = q_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 12:17]
  wire [3:0] k0 = k_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 13:17]
  wire [3:0] k1 = k_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 14:17]
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 18:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 19:18]
  wire [8:0] score = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 24:21]
  wire  score_ge_thresh = score >= 9'h40; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 27:31]
  assign weight = score_ge_thresh ? score : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 32:16]
endmodule
module Divider15by11(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 7:17]
  input  [14:0] dividend, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 8:20]
  input  [10:0] divisor, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 9:19]
  output [14:0] quotient, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 10:20]
  output        valid_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 11:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
`endif // RANDOMIZE_REG_INIT
  reg [14:0] dividend_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 15:31]
  reg [10:0] divisor_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 16:30]
  reg  valid_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 17:28]
  wire  dividend_bit = dividend_reg[14]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] temp_rem = {{11'd0}, dividend_bit}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] _GEN_2 = {{1'd0}, divisor_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire  can_subtract = temp_rem >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_1 = temp_rem - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem = can_subtract ? _next_rem_T_1 : temp_rem; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [15:0] next_quot = {{15'd0}, can_subtract}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_1 = dividend_reg[13]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_1 = {next_rem[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_4 = {{11'd0}, dividend_bit_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_1 = _temp_rem_T_1 | _GEN_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_1 = temp_rem_1 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_3 = temp_rem_1 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_1 = can_subtract_1 ? _next_rem_T_3 : temp_rem_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [16:0] _next_quot_T_1 = {next_quot, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [16:0] _GEN_7 = {{16'd0}, can_subtract_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [16:0] next_quot_1 = _next_quot_T_1 | _GEN_7; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_2 = dividend_reg[12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_2 = {next_rem_1[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_8 = {{11'd0}, dividend_bit_2}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_2 = _temp_rem_T_2 | _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_2 = temp_rem_2 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_5 = temp_rem_2 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_2 = can_subtract_2 ? _next_rem_T_5 : temp_rem_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [17:0] _next_quot_T_2 = {next_quot_1, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [17:0] _GEN_11 = {{17'd0}, can_subtract_2}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [17:0] next_quot_2 = _next_quot_T_2 | _GEN_11; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_3 = dividend_reg[11]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_3 = {next_rem_2[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_12 = {{11'd0}, dividend_bit_3}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_3 = _temp_rem_T_3 | _GEN_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_3 = temp_rem_3 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_7 = temp_rem_3 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_3 = can_subtract_3 ? _next_rem_T_7 : temp_rem_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [18:0] _next_quot_T_3 = {next_quot_2, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [18:0] _GEN_15 = {{18'd0}, can_subtract_3}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [18:0] next_quot_3 = _next_quot_T_3 | _GEN_15; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_4 = dividend_reg[10]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_4 = {next_rem_3[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_16 = {{11'd0}, dividend_bit_4}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_4 = _temp_rem_T_4 | _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_4 = temp_rem_4 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_9 = temp_rem_4 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_4 = can_subtract_4 ? _next_rem_T_9 : temp_rem_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [19:0] _next_quot_T_4 = {next_quot_3, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [19:0] _GEN_19 = {{19'd0}, can_subtract_4}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [19:0] next_quot_4 = _next_quot_T_4 | _GEN_19; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_5 = dividend_reg[9]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_5 = {next_rem_4[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_20 = {{11'd0}, dividend_bit_5}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_5 = _temp_rem_T_5 | _GEN_20; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_5 = temp_rem_5 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_11 = temp_rem_5 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_5 = can_subtract_5 ? _next_rem_T_11 : temp_rem_5; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [20:0] _next_quot_T_5 = {next_quot_4, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [20:0] _GEN_23 = {{20'd0}, can_subtract_5}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [20:0] next_quot_5 = _next_quot_T_5 | _GEN_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_6 = dividend_reg[8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_6 = {next_rem_5[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_24 = {{11'd0}, dividend_bit_6}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_6 = _temp_rem_T_6 | _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_6 = temp_rem_6 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_13 = temp_rem_6 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_6 = can_subtract_6 ? _next_rem_T_13 : temp_rem_6; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [21:0] _next_quot_T_6 = {next_quot_5, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [21:0] _GEN_27 = {{21'd0}, can_subtract_6}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [21:0] next_quot_6 = _next_quot_T_6 | _GEN_27; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_7 = dividend_reg[7]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_7 = {next_rem_6[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_28 = {{11'd0}, dividend_bit_7}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_7 = _temp_rem_T_7 | _GEN_28; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_7 = temp_rem_7 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_15 = temp_rem_7 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_7 = can_subtract_7 ? _next_rem_T_15 : temp_rem_7; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [22:0] _next_quot_T_7 = {next_quot_6, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [22:0] _GEN_31 = {{22'd0}, can_subtract_7}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [22:0] next_quot_7 = _next_quot_T_7 | _GEN_31; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_8 = dividend_reg[6]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_8 = {next_rem_7[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_32 = {{11'd0}, dividend_bit_8}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_8 = _temp_rem_T_8 | _GEN_32; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_8 = temp_rem_8 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_17 = temp_rem_8 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_8 = can_subtract_8 ? _next_rem_T_17 : temp_rem_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [23:0] _next_quot_T_8 = {next_quot_7, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [23:0] _GEN_35 = {{23'd0}, can_subtract_8}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [23:0] next_quot_8 = _next_quot_T_8 | _GEN_35; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_9 = dividend_reg[5]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_9 = {next_rem_8[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_36 = {{11'd0}, dividend_bit_9}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_9 = _temp_rem_T_9 | _GEN_36; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_9 = temp_rem_9 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_19 = temp_rem_9 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_9 = can_subtract_9 ? _next_rem_T_19 : temp_rem_9; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [24:0] _next_quot_T_9 = {next_quot_8, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [24:0] _GEN_39 = {{24'd0}, can_subtract_9}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [24:0] next_quot_9 = _next_quot_T_9 | _GEN_39; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_10 = dividend_reg[4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_10 = {next_rem_9[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_40 = {{11'd0}, dividend_bit_10}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_10 = _temp_rem_T_10 | _GEN_40; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_10 = temp_rem_10 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_21 = temp_rem_10 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_10 = can_subtract_10 ? _next_rem_T_21 : temp_rem_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [25:0] _next_quot_T_10 = {next_quot_9, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [25:0] _GEN_43 = {{25'd0}, can_subtract_10}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [25:0] next_quot_10 = _next_quot_T_10 | _GEN_43; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_11 = dividend_reg[3]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_11 = {next_rem_10[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_44 = {{11'd0}, dividend_bit_11}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_11 = _temp_rem_T_11 | _GEN_44; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_11 = temp_rem_11 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_23 = temp_rem_11 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_11 = can_subtract_11 ? _next_rem_T_23 : temp_rem_11; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [26:0] _next_quot_T_11 = {next_quot_10, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [26:0] _GEN_47 = {{26'd0}, can_subtract_11}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [26:0] next_quot_11 = _next_quot_T_11 | _GEN_47; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_12 = dividend_reg[2]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_12 = {next_rem_11[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_48 = {{11'd0}, dividend_bit_12}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_12 = _temp_rem_T_12 | _GEN_48; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_12 = temp_rem_12 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_25 = temp_rem_12 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_12 = can_subtract_12 ? _next_rem_T_25 : temp_rem_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [27:0] _next_quot_T_12 = {next_quot_11, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [27:0] _GEN_51 = {{27'd0}, can_subtract_12}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [27:0] next_quot_12 = _next_quot_T_12 | _GEN_51; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_13 = dividend_reg[1]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_13 = {next_rem_12[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_52 = {{11'd0}, dividend_bit_13}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_13 = _temp_rem_T_13 | _GEN_52; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_13 = temp_rem_13 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [11:0] _next_rem_T_27 = temp_rem_13 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:51]
  wire [11:0] next_rem_13 = can_subtract_13 ? _next_rem_T_27 : temp_rem_13; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 49:27]
  wire [28:0] _next_quot_T_13 = {next_quot_12, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [28:0] _GEN_55 = {{28'd0}, can_subtract_13}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [28:0] next_quot_13 = _next_quot_T_13 | _GEN_55; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire  dividend_bit_14 = dividend_reg[0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 38:40]
  wire [11:0] _temp_rem_T_14 = {next_rem_13[10:0], 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:29]
  wire [11:0] _GEN_56 = {{11'd0}, dividend_bit_14}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire [11:0] temp_rem_14 = _temp_rem_T_14 | _GEN_56; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 42:35]
  wire  can_subtract_14 = temp_rem_14 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 45:37]
  wire [29:0] _next_quot_T_14 = {next_quot_13, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:31]
  wire [29:0] _GEN_59 = {{29'd0}, can_subtract_14}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  wire [29:0] calculated_quotient = _next_quot_T_14 | _GEN_59; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 52:37]
  assign quotient = calculated_quotient[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 61:14]
  assign valid_out = valid_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 27:15]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 15:31]
      dividend_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 15:31]
    end else if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 20:17]
      dividend_reg <= dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 21:20]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 16:30]
      divisor_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 16:30]
    end else if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 20:17]
      divisor_reg <= divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 22:19]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 17:28]
      valid_reg <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 17:28]
    end else begin
      valid_reg <= start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/Divider15by11/Divider15by11.scala 26:15]
    end
  end
// Register and memory initialization
`ifdef RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_INVALID_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_REG_INIT
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_MEM_INIT
`define RANDOMIZE
`endif
`ifndef RANDOM
`define RANDOM $random
`endif
`ifdef RANDOMIZE_MEM_INIT
  integer initvar;
`endif
`ifndef SYNTHESIS
`ifdef FIRRTL_BEFORE_INITIAL
`FIRRTL_BEFORE_INITIAL
`endif
initial begin
  `ifdef RANDOMIZE
    `ifdef INIT_RANDOM
      `INIT_RANDOM
    `endif
    `ifndef VERILATOR
      `ifdef RANDOMIZE_DELAY
        #`RANDOMIZE_DELAY begin end
      `else
        #0.002 begin end
      `endif
    `endif
`ifdef RANDOMIZE_REG_INIT
  _RAND_0 = {1{`RANDOM}};
  dividend_reg = _RAND_0[14:0];
  _RAND_1 = {1{`RANDOM}};
  divisor_reg = _RAND_1[10:0];
  _RAND_2 = {1{`RANDOM}};
  valid_reg = _RAND_2[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
module ThresholdAttention(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 7:17]
  input  [7:0]  q, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 8:13]
  input  [31:0] k, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 9:13]
  input  [15:0] v, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 10:13]
  output        done, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 11:16]
  output [3:0]  result // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 12:18]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
  reg [31:0] _RAND_6;
  reg [31:0] _RAND_7;
`endif // RANDOMIZE_REG_INIT
  wire [7:0] score_weight_unit_q_vec; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 37:35]
  wire [7:0] score_weight_unit_k_vec; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 37:35]
  wire [8:0] score_weight_unit_weight; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 37:35]
  wire  divider_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  wire  divider_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  wire  divider_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  wire [14:0] divider_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  wire [10:0] divider_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  wire [14:0] divider_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  wire  divider_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
  reg [2:0] state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 19:24]
  reg [7:0] q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 22:20]
  reg [31:0] k_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 23:20]
  reg [15:0] v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 24:20]
  reg [10:0] weight_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 27:33]
  reg [14:0] weighted_value_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 28:41]
  reg [1:0] idx_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 31:26]
  reg [14:0] final_quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 34:33]
  wire [4:0] _k_i_T = {idx_reg, 3'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 45:34]
  wire [31:0] _k_i_T_1 = k_reg >> _k_i_T; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 45:22]
  wire [3:0] _GEN_39 = {idx_reg, 2'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 46:34]
  wire [4:0] _v_i_T = {{1'd0}, _GEN_39}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 46:34]
  wire [15:0] _v_i_T_1 = v_reg >> _v_i_T; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 46:22]
  wire [3:0] v_i = _v_i_T_1[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 46:42]
  wire [10:0] _GEN_40 = {{2'd0}, score_weight_unit_weight}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 75:45]
  wire [11:0] new_weight_sum = weight_sum_reg + _GEN_40; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 75:45]
  wire [12:0] weighted_prod = score_weight_unit_weight * v_i; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 78:44]
  wire [14:0] _GEN_41 = {{2'd0}, weighted_prod}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 79:61]
  wire [15:0] new_weighted_value_sum = weighted_value_sum_reg + _GEN_41; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 79:61]
  wire [1:0] _idx_reg_T_1 = idx_reg + 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 82:28]
  wire [2:0] _GEN_9 = weight_sum_reg == 11'h0 ? 3'h4 : 3'h3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 90:38 92:17 95:17]
  wire  _GEN_10 = weight_sum_reg == 11'h0 ? 1'h0 : 1'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 56:19 90:38 94:25]
  wire [14:0] _GEN_11 = divider_valid_out ? divider_quotient : final_quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 100:33 101:30 34:33]
  wire [2:0] _GEN_12 = divider_valid_out ? 3'h4 : state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 100:33 102:17 19:24]
  wire [2:0] _GEN_14 = 3'h4 == state ? 3'h0 : state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 108:15 61:19 19:24]
  wire [2:0] _GEN_16 = 3'h3 == state ? _GEN_12 : _GEN_14; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
  wire  _GEN_17 = 3'h3 == state ? 1'h0 : 3'h4 == state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 55:10 61:19]
  wire  _GEN_21 = 3'h2 == state ? 1'h0 : _GEN_17; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 55:10 61:19]
  wire  _GEN_27 = 3'h1 == state ? 1'h0 : 3'h2 == state & _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 56:19 61:19]
  wire  _GEN_28 = 3'h1 == state ? 1'h0 : _GEN_21; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 55:10 61:19]
  ScoreAndWeightUnit score_weight_unit ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 37:35]
    .q_vec(score_weight_unit_q_vec),
    .k_vec(score_weight_unit_k_vec),
    .weight(score_weight_unit_weight)
  );
  Divider15by11 divider ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 38:25]
    .clock(divider_clock),
    .reset(divider_reset),
    .start(divider_start),
    .dividend(divider_dividend),
    .divisor(divider_divisor),
    .quotient(divider_quotient),
    .valid_out(divider_valid_out)
  );
  assign done = 3'h0 == state ? 1'h0 : _GEN_28; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 55:10 61:19]
  assign result = final_quotient_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 112:33]
  assign score_weight_unit_q_vec = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 49:29]
  assign score_weight_unit_k_vec = _k_i_T_1[7:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 45:42]
  assign divider_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 41:19]
  assign divider_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 42:19]
  assign divider_start = 3'h0 == state ? 1'h0 : _GEN_27; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 56:19 61:19]
  assign divider_dividend = weighted_value_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 57:22]
  assign divider_divisor = weight_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 58:21]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 19:24]
      state <= 3'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 19:24]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        state <= 3'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 70:17]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (idx_reg == 2'h3) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 84:31]
        state <= 3'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 85:17]
      end
    end else if (3'h2 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      state <= _GEN_9;
    end else begin
      state <= _GEN_16;
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        q_reg <= q; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 64:17]
      end
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        k_reg <= k; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 65:17]
      end
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        v_reg <= v; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 66:17]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 27:33]
      weight_sum_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 27:33]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        weight_sum_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 67:26]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      weight_sum_reg <= new_weight_sum[10:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 76:24]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 28:41]
      weighted_value_sum_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 28:41]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        weighted_value_sum_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 68:34]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      weighted_value_sum_reg <= new_weighted_value_sum[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 80:32]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 31:26]
      idx_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 31:26]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 63:21]
        idx_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 69:19]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      idx_reg <= _idx_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 82:17]
    end
    if (!(3'h0 == state)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
      if (!(3'h1 == state)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
        if (3'h2 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
          if (weight_sum_reg == 11'h0) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 90:38]
            final_quotient_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 91:30]
          end
        end else if (3'h3 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_02/build_01/ThresholdAttention/ThresholdAttention.scala 61:19]
          final_quotient_reg <= _GEN_11;
        end
      end
    end
  end
// Register and memory initialization
`ifdef RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_INVALID_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_REG_INIT
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_MEM_INIT
`define RANDOMIZE
`endif
`ifndef RANDOM
`define RANDOM $random
`endif
`ifdef RANDOMIZE_MEM_INIT
  integer initvar;
`endif
`ifndef SYNTHESIS
`ifdef FIRRTL_BEFORE_INITIAL
`FIRRTL_BEFORE_INITIAL
`endif
initial begin
  `ifdef RANDOMIZE
    `ifdef INIT_RANDOM
      `INIT_RANDOM
    `endif
    `ifndef VERILATOR
      `ifdef RANDOMIZE_DELAY
        #`RANDOMIZE_DELAY begin end
      `else
        #0.002 begin end
      `endif
    `endif
`ifdef RANDOMIZE_REG_INIT
  _RAND_0 = {1{`RANDOM}};
  state = _RAND_0[2:0];
  _RAND_1 = {1{`RANDOM}};
  q_reg = _RAND_1[7:0];
  _RAND_2 = {1{`RANDOM}};
  k_reg = _RAND_2[31:0];
  _RAND_3 = {1{`RANDOM}};
  v_reg = _RAND_3[15:0];
  _RAND_4 = {1{`RANDOM}};
  weight_sum_reg = _RAND_4[10:0];
  _RAND_5 = {1{`RANDOM}};
  weighted_value_sum_reg = _RAND_5[14:0];
  _RAND_6 = {1{`RANDOM}};
  idx_reg = _RAND_6[1:0];
  _RAND_7 = {1{`RANDOM}};
  final_quotient_reg = _RAND_7[14:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
