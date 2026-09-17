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
