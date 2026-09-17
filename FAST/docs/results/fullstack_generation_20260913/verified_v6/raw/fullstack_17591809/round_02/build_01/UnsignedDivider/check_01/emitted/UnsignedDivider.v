module UnsignedDivider(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 6:17]
  input         valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 7:20]
  input  [14:0] numerator_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 8:24]
  input  [10:0] denominator_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 9:26]
  output        valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 10:21]
  output [3:0]  quotient_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 11:24]
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
  reg [31:0] _RAND_8;
  reg [31:0] _RAND_9;
  reg [31:0] _RAND_10;
  reg [31:0] _RAND_11;
  reg [31:0] _RAND_12;
  reg [31:0] _RAND_13;
  reg [31:0] _RAND_14;
  reg [31:0] _RAND_15;
  reg [31:0] _RAND_16;
  reg [31:0] _RAND_17;
  reg [31:0] _RAND_18;
  reg [31:0] _RAND_19;
  reg [31:0] _RAND_20;
`endif // RANDOMIZE_REG_INIT
  wire  initial_state_divideByZero = denominator_in == 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 71:49]
  wire [11:0] shifted_rem = {11'h0,numerator_in[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_0 = {{1'd0}, denominator_in}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire  can_subtract = shifted_rem >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_1 = shifted_rem - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem = can_subtract ? _next_rem_T_1 : shifted_rem; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_quotient = {14'h0,can_subtract}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_dividend = {numerator_in[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_1 = {next_rem[10:0],next_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_1 = shifted_rem_1 >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_3 = shifted_rem_1 - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_1 = can_subtract_1 ? _next_rem_T_3 : shifted_rem_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_1_quotient = {next_quotient[13:0],can_subtract_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_1_dividend = {next_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_2 = {next_rem_1[10:0],next_1_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_2 = shifted_rem_2 >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_5 = shifted_rem_2 - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_2 = can_subtract_2 ? _next_rem_T_5 : shifted_rem_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_2_quotient = {next_1_quotient[13:0],can_subtract_2}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_2_dividend = {next_1_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_3 = {next_rem_2[10:0],next_2_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_3 = shifted_rem_3 >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_7 = shifted_rem_3 - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [14:0] next_3_quotient = {next_2_quotient[13:0],can_subtract_3}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_3_dividend = {next_2_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  reg [11:0] REG_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [14:0] REG_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [14:0] REG_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [10:0] REG_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  wire [11:0] shifted_rem_4 = {REG_remainder[10:0],REG_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_8 = {{1'd0}, REG_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire  can_subtract_4 = shifted_rem_4 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_9 = shifted_rem_4 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_4 = can_subtract_4 ? _next_rem_T_9 : shifted_rem_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_4_quotient = {REG_quotient[13:0],can_subtract_4}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_4_dividend = {REG_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_5 = {next_rem_4[10:0],next_4_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_5 = shifted_rem_5 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_11 = shifted_rem_5 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_5 = can_subtract_5 ? _next_rem_T_11 : shifted_rem_5; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_5_quotient = {next_4_quotient[13:0],can_subtract_5}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_5_dividend = {next_4_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_6 = {next_rem_5[10:0],next_5_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_6 = shifted_rem_6 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_13 = shifted_rem_6 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_6 = can_subtract_6 ? _next_rem_T_13 : shifted_rem_6; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_6_quotient = {next_5_quotient[13:0],can_subtract_6}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_6_dividend = {next_5_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_7 = {next_rem_6[10:0],next_6_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_7 = shifted_rem_7 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_15 = shifted_rem_7 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [14:0] next_7_quotient = {next_6_quotient[13:0],can_subtract_7}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_7_dividend = {next_6_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  reg [11:0] REG_1_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [14:0] REG_1_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [14:0] REG_1_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [10:0] REG_1_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_1_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_1_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  wire [11:0] shifted_rem_8 = {REG_1_remainder[10:0],REG_1_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_16 = {{1'd0}, REG_1_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire  can_subtract_8 = shifted_rem_8 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_17 = shifted_rem_8 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_8 = can_subtract_8 ? _next_rem_T_17 : shifted_rem_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_8_quotient = {REG_1_quotient[13:0],can_subtract_8}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_8_dividend = {REG_1_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_9 = {next_rem_8[10:0],next_8_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_9 = shifted_rem_9 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_19 = shifted_rem_9 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_9 = can_subtract_9 ? _next_rem_T_19 : shifted_rem_9; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_9_quotient = {next_8_quotient[13:0],can_subtract_9}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_9_dividend = {next_8_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_10 = {next_rem_9[10:0],next_9_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_10 = shifted_rem_10 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_21 = shifted_rem_10 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_10 = can_subtract_10 ? _next_rem_T_21 : shifted_rem_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_10_quotient = {next_9_quotient[13:0],can_subtract_10}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_10_dividend = {next_9_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_11 = {next_rem_10[10:0],next_10_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_11 = shifted_rem_11 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_23 = shifted_rem_11 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [14:0] next_11_quotient = {next_10_quotient[13:0],can_subtract_11}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_11_dividend = {next_10_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  reg [11:0] REG_2_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [14:0] REG_2_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [14:0] REG_2_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg [10:0] REG_2_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_2_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  wire [11:0] shifted_rem_12 = {REG_2_remainder[10:0],REG_2_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_24 = {{1'd0}, REG_2_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire  can_subtract_12 = shifted_rem_12 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_25 = shifted_rem_12 - _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_12 = can_subtract_12 ? _next_rem_T_25 : shifted_rem_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_12_quotient = {REG_2_quotient[13:0],can_subtract_12}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_12_dividend = {REG_2_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_13 = {next_rem_12[10:0],next_12_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_13 = shifted_rem_13 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_27 = shifted_rem_13 - _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_13 = can_subtract_13 ? _next_rem_T_27 : shifted_rem_13; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
  wire [14:0] next_13_quotient = {next_12_quotient[13:0],can_subtract_13}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  wire [14:0] next_13_dividend = {next_12_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_14 = {next_rem_13[10:0],next_13_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 43:26]
  wire  can_subtract_14 = shifted_rem_14 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 46:36]
  wire [14:0] next_14_quotient = {next_13_quotient[13:0],can_subtract_14}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 52:25]
  reg [14:0] REG_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_3_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  reg  REG_3_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
  wire [14:0] full_quotient = REG_3_divideByZero ? 15'h0 : REG_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 97:26]
  assign valid_out = REG_3_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 100:13]
  assign quotient_out = full_quotient[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 102:32]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else if (can_subtract_3) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
      REG_remainder <= _next_rem_T_7;
    end else begin
      REG_remainder <= shifted_rem_3;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_quotient <= next_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_dividend <= next_3_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_divisor <= denominator_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_divideByZero <= initial_state_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_valid <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_1_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else if (can_subtract_7) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
      REG_1_remainder <= _next_rem_T_15;
    end else begin
      REG_1_remainder <= shifted_rem_7;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_1_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_quotient <= next_7_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_1_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_dividend <= next_7_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_1_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_divisor <= REG_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_1_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_divideByZero <= REG_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_1_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_valid <= REG_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_2_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else if (can_subtract_11) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 47:23]
      REG_2_remainder <= _next_rem_T_23;
    end else begin
      REG_2_remainder <= shifted_rem_11;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_2_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_quotient <= next_11_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_2_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_dividend <= next_11_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_2_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_divisor <= REG_1_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_2_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_divideByZero <= REG_1_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_2_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_valid <= REG_1_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_3_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_3_quotient <= next_14_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_3_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_3_divideByZero <= REG_2_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
      REG_3_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
    end else begin
      REG_3_valid <= REG_2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/UnsignedDivider/UnsignedDivider.scala 89:14]
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
  REG_remainder = _RAND_0[11:0];
  _RAND_1 = {1{`RANDOM}};
  REG_quotient = _RAND_1[14:0];
  _RAND_2 = {1{`RANDOM}};
  REG_dividend = _RAND_2[14:0];
  _RAND_3 = {1{`RANDOM}};
  REG_divisor = _RAND_3[10:0];
  _RAND_4 = {1{`RANDOM}};
  REG_divideByZero = _RAND_4[0:0];
  _RAND_5 = {1{`RANDOM}};
  REG_valid = _RAND_5[0:0];
  _RAND_6 = {1{`RANDOM}};
  REG_1_remainder = _RAND_6[11:0];
  _RAND_7 = {1{`RANDOM}};
  REG_1_quotient = _RAND_7[14:0];
  _RAND_8 = {1{`RANDOM}};
  REG_1_dividend = _RAND_8[14:0];
  _RAND_9 = {1{`RANDOM}};
  REG_1_divisor = _RAND_9[10:0];
  _RAND_10 = {1{`RANDOM}};
  REG_1_divideByZero = _RAND_10[0:0];
  _RAND_11 = {1{`RANDOM}};
  REG_1_valid = _RAND_11[0:0];
  _RAND_12 = {1{`RANDOM}};
  REG_2_remainder = _RAND_12[11:0];
  _RAND_13 = {1{`RANDOM}};
  REG_2_quotient = _RAND_13[14:0];
  _RAND_14 = {1{`RANDOM}};
  REG_2_dividend = _RAND_14[14:0];
  _RAND_15 = {1{`RANDOM}};
  REG_2_divisor = _RAND_15[10:0];
  _RAND_16 = {1{`RANDOM}};
  REG_2_divideByZero = _RAND_16[0:0];
  _RAND_17 = {1{`RANDOM}};
  REG_2_valid = _RAND_17[0:0];
  _RAND_18 = {1{`RANDOM}};
  REG_3_quotient = _RAND_18[14:0];
  _RAND_19 = {1{`RANDOM}};
  REG_3_divideByZero = _RAND_19[0:0];
  _RAND_20 = {1{`RANDOM}};
  REG_3_valid = _RAND_20[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
