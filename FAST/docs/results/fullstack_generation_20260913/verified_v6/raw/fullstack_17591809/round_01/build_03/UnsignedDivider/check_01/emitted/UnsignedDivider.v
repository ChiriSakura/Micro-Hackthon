module UnsignedDivider(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 6:17]
  input         valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 7:20]
  input  [14:0] numerator_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 8:24]
  input  [10:0] denominator_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 9:26]
  output        valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 10:21]
  output [3:0]  quotient_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 11:24]
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
  reg [31:0] _RAND_21;
  reg [31:0] _RAND_22;
  reg [31:0] _RAND_23;
  reg [31:0] _RAND_24;
  reg [31:0] _RAND_25;
  reg [31:0] _RAND_26;
  reg [31:0] _RAND_27;
  reg [31:0] _RAND_28;
  reg [31:0] _RAND_29;
  reg [31:0] _RAND_30;
  reg [31:0] _RAND_31;
  reg [31:0] _RAND_32;
  reg [31:0] _RAND_33;
  reg [31:0] _RAND_34;
  reg [31:0] _RAND_35;
  reg [31:0] _RAND_36;
  reg [31:0] _RAND_37;
  reg [31:0] _RAND_38;
  reg [31:0] _RAND_39;
  reg [31:0] _RAND_40;
  reg [31:0] _RAND_41;
  reg [31:0] _RAND_42;
  reg [31:0] _RAND_43;
  reg [31:0] _RAND_44;
  reg [31:0] _RAND_45;
  reg [31:0] _RAND_46;
  reg [31:0] _RAND_47;
  reg [31:0] _RAND_48;
  reg [31:0] _RAND_49;
  reg [31:0] _RAND_50;
  reg [31:0] _RAND_51;
  reg [31:0] _RAND_52;
  reg [31:0] _RAND_53;
  reg [31:0] _RAND_54;
  reg [31:0] _RAND_55;
  reg [31:0] _RAND_56;
  reg [31:0] _RAND_57;
  reg [31:0] _RAND_58;
  reg [31:0] _RAND_59;
  reg [31:0] _RAND_60;
  reg [31:0] _RAND_61;
  reg [31:0] _RAND_62;
  reg [31:0] _RAND_63;
  reg [31:0] _RAND_64;
  reg [31:0] _RAND_65;
  reg [31:0] _RAND_66;
  reg [31:0] _RAND_67;
  reg [31:0] _RAND_68;
  reg [31:0] _RAND_69;
  reg [31:0] _RAND_70;
  reg [31:0] _RAND_71;
  reg [31:0] _RAND_72;
  reg [31:0] _RAND_73;
  reg [31:0] _RAND_74;
  reg [31:0] _RAND_75;
  reg [31:0] _RAND_76;
  reg [31:0] _RAND_77;
  reg [31:0] _RAND_78;
  reg [31:0] _RAND_79;
  reg [31:0] _RAND_80;
  reg [31:0] _RAND_81;
  reg [31:0] _RAND_82;
  reg [31:0] _RAND_83;
  reg [31:0] _RAND_84;
  reg [31:0] _RAND_85;
  reg [31:0] _RAND_86;
`endif // RANDOMIZE_REG_INIT
  wire  initial_state_divideByZero = denominator_in == 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 67:49]
  wire [11:0] next_state_comb_shifted_rem = {11'h0,numerator_in[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_0 = {{1'd0}, denominator_in}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract = next_state_comb_shifted_rem >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_1 = next_state_comb_shifted_rem - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_quotient = {14'h0,next_state_comb_can_subtract}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_dividend = {numerator_in[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_1 = {REG_remainder[10:0],REG_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_2 = {{1'd0}, REG_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_1 = next_state_comb_shifted_rem_1 >= _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_3 = next_state_comb_shifted_rem_1 - _GEN_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_1_quotient = {REG_quotient[13:0],next_state_comb_can_subtract_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_1_dividend = {REG_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_1_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_1_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_1_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_1_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_1_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_1_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_2 = {REG_1_remainder[10:0],REG_1_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_4 = {{1'd0}, REG_1_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_2 = next_state_comb_shifted_rem_2 >= _GEN_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_5 = next_state_comb_shifted_rem_2 - _GEN_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_2_quotient = {REG_1_quotient[13:0],next_state_comb_can_subtract_2}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_2_dividend = {REG_1_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_2_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_2_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_2_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_2_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_2_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_3 = {REG_2_remainder[10:0],REG_2_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_6 = {{1'd0}, REG_2_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_3 = next_state_comb_shifted_rem_3 >= _GEN_6; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_7 = next_state_comb_shifted_rem_3 - _GEN_6; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_3_quotient = {REG_2_quotient[13:0],next_state_comb_can_subtract_3}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_3_dividend = {REG_2_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_3_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_3_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_3_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_3_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_3_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_4 = {REG_3_remainder[10:0],REG_3_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_8 = {{1'd0}, REG_3_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_4 = next_state_comb_shifted_rem_4 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_9 = next_state_comb_shifted_rem_4 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_4_quotient = {REG_3_quotient[13:0],next_state_comb_can_subtract_4}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_4_dividend = {REG_3_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_4_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_4_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_4_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_4_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_4_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_4_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_5 = {REG_4_remainder[10:0],REG_4_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_10 = {{1'd0}, REG_4_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_5 = next_state_comb_shifted_rem_5 >= _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_11 = next_state_comb_shifted_rem_5 - _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_5_quotient = {REG_4_quotient[13:0],next_state_comb_can_subtract_5}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_5_dividend = {REG_4_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_5_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_5_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_5_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_5_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_5_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_5_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_6 = {REG_5_remainder[10:0],REG_5_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_12 = {{1'd0}, REG_5_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_6 = next_state_comb_shifted_rem_6 >= _GEN_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_13 = next_state_comb_shifted_rem_6 - _GEN_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_6_quotient = {REG_5_quotient[13:0],next_state_comb_can_subtract_6}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_6_dividend = {REG_5_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_6_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_6_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_6_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_6_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_6_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_6_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_7 = {REG_6_remainder[10:0],REG_6_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_14 = {{1'd0}, REG_6_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_7 = next_state_comb_shifted_rem_7 >= _GEN_14; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_15 = next_state_comb_shifted_rem_7 - _GEN_14; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_7_quotient = {REG_6_quotient[13:0],next_state_comb_can_subtract_7}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_7_dividend = {REG_6_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_7_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_7_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_7_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_7_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_7_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_7_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_8 = {REG_7_remainder[10:0],REG_7_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_16 = {{1'd0}, REG_7_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_8 = next_state_comb_shifted_rem_8 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_17 = next_state_comb_shifted_rem_8 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_8_quotient = {REG_7_quotient[13:0],next_state_comb_can_subtract_8}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_8_dividend = {REG_7_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_8_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_8_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_8_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_8_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_8_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_8_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_9 = {REG_8_remainder[10:0],REG_8_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_18 = {{1'd0}, REG_8_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_9 = next_state_comb_shifted_rem_9 >= _GEN_18; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_19 = next_state_comb_shifted_rem_9 - _GEN_18; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_9_quotient = {REG_8_quotient[13:0],next_state_comb_can_subtract_9}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_9_dividend = {REG_8_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_9_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_9_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_9_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_9_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_9_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_9_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_10 = {REG_9_remainder[10:0],REG_9_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_20 = {{1'd0}, REG_9_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_10 = next_state_comb_shifted_rem_10 >= _GEN_20; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_21 = next_state_comb_shifted_rem_10 - _GEN_20; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_10_quotient = {REG_9_quotient[13:0],next_state_comb_can_subtract_10}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_10_dividend = {REG_9_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_10_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_10_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_10_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_10_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_10_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_10_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_11 = {REG_10_remainder[10:0],REG_10_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_22 = {{1'd0}, REG_10_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_11 = next_state_comb_shifted_rem_11 >= _GEN_22; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_23 = next_state_comb_shifted_rem_11 - _GEN_22; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_11_quotient = {REG_10_quotient[13:0],next_state_comb_can_subtract_11}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_11_dividend = {REG_10_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_11_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_11_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_11_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_11_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_11_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_11_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_12 = {REG_11_remainder[10:0],REG_11_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_24 = {{1'd0}, REG_11_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_12 = next_state_comb_shifted_rem_12 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_25 = next_state_comb_shifted_rem_12 - _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_12_quotient = {REG_11_quotient[13:0],next_state_comb_can_subtract_12}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_12_dividend = {REG_11_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_12_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_12_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_12_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_12_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_12_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_12_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_13 = {REG_12_remainder[10:0],REG_12_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_26 = {{1'd0}, REG_12_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_13 = next_state_comb_shifted_rem_13 >= _GEN_26; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [11:0] _next_state_comb_next_rem_T_27 = next_state_comb_shifted_rem_13 - _GEN_26; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:50]
  wire [14:0] next_state_comb_13_quotient = {REG_12_quotient[13:0],next_state_comb_can_subtract_13}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  wire [14:0] next_state_comb_13_dividend = {REG_12_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 49:25]
  reg [11:0] REG_13_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_13_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [14:0] REG_13_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg [10:0] REG_13_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_13_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_13_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [11:0] next_state_comb_shifted_rem_14 = {REG_13_remainder[10:0],REG_13_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 39:26]
  wire [11:0] _GEN_28 = {{1'd0}, REG_13_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire  next_state_comb_can_subtract_14 = next_state_comb_shifted_rem_14 >= _GEN_28; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 42:36]
  wire [14:0] next_state_comb_14_quotient = {REG_13_quotient[13:0],next_state_comb_can_subtract_14}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 48:25]
  reg [14:0] REG_14_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_14_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  reg  REG_14_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
  wire [14:0] full_quotient = REG_14_divideByZero ? 15'h0 : REG_14_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 84:26]
  assign valid_out = REG_14_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 87:13]
  assign quotient_out = full_quotient[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 89:32]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_remainder <= _next_state_comb_next_rem_T_1;
    end else begin
      REG_remainder <= next_state_comb_shifted_rem;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_quotient <= next_state_comb_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_dividend <= next_state_comb_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_divisor <= denominator_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_divideByZero <= initial_state_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_valid <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_1_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_1_remainder <= _next_state_comb_next_rem_T_3;
    end else begin
      REG_1_remainder <= next_state_comb_shifted_rem_1;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_1_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_1_quotient <= next_state_comb_1_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_1_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_1_dividend <= next_state_comb_1_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_1_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_1_divisor <= REG_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_1_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_1_divideByZero <= REG_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_1_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_1_valid <= REG_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_2_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_2) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_2_remainder <= _next_state_comb_next_rem_T_5;
    end else begin
      REG_2_remainder <= next_state_comb_shifted_rem_2;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_2_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_2_quotient <= next_state_comb_2_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_2_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_2_dividend <= next_state_comb_2_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_2_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_2_divisor <= REG_1_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_2_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_2_divideByZero <= REG_1_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_2_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_2_valid <= REG_1_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_3_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_3) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_3_remainder <= _next_state_comb_next_rem_T_7;
    end else begin
      REG_3_remainder <= next_state_comb_shifted_rem_3;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_3_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_3_quotient <= next_state_comb_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_3_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_3_dividend <= next_state_comb_3_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_3_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_3_divisor <= REG_2_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_3_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_3_divideByZero <= REG_2_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_3_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_3_valid <= REG_2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_4_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_4) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_4_remainder <= _next_state_comb_next_rem_T_9;
    end else begin
      REG_4_remainder <= next_state_comb_shifted_rem_4;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_4_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_4_quotient <= next_state_comb_4_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_4_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_4_dividend <= next_state_comb_4_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_4_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_4_divisor <= REG_3_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_4_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_4_divideByZero <= REG_3_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_4_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_4_valid <= REG_3_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_5_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_5) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_5_remainder <= _next_state_comb_next_rem_T_11;
    end else begin
      REG_5_remainder <= next_state_comb_shifted_rem_5;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_5_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_5_quotient <= next_state_comb_5_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_5_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_5_dividend <= next_state_comb_5_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_5_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_5_divisor <= REG_4_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_5_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_5_divideByZero <= REG_4_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_5_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_5_valid <= REG_4_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_6_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_6) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_6_remainder <= _next_state_comb_next_rem_T_13;
    end else begin
      REG_6_remainder <= next_state_comb_shifted_rem_6;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_6_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_6_quotient <= next_state_comb_6_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_6_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_6_dividend <= next_state_comb_6_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_6_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_6_divisor <= REG_5_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_6_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_6_divideByZero <= REG_5_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_6_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_6_valid <= REG_5_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_7_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_7) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_7_remainder <= _next_state_comb_next_rem_T_15;
    end else begin
      REG_7_remainder <= next_state_comb_shifted_rem_7;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_7_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_7_quotient <= next_state_comb_7_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_7_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_7_dividend <= next_state_comb_7_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_7_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_7_divisor <= REG_6_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_7_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_7_divideByZero <= REG_6_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_7_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_7_valid <= REG_6_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_8_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_8) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_8_remainder <= _next_state_comb_next_rem_T_17;
    end else begin
      REG_8_remainder <= next_state_comb_shifted_rem_8;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_8_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_8_quotient <= next_state_comb_8_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_8_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_8_dividend <= next_state_comb_8_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_8_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_8_divisor <= REG_7_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_8_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_8_divideByZero <= REG_7_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_8_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_8_valid <= REG_7_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_9_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_9) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_9_remainder <= _next_state_comb_next_rem_T_19;
    end else begin
      REG_9_remainder <= next_state_comb_shifted_rem_9;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_9_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_9_quotient <= next_state_comb_9_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_9_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_9_dividend <= next_state_comb_9_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_9_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_9_divisor <= REG_8_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_9_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_9_divideByZero <= REG_8_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_9_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_9_valid <= REG_8_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_10_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_10) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_10_remainder <= _next_state_comb_next_rem_T_21;
    end else begin
      REG_10_remainder <= next_state_comb_shifted_rem_10;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_10_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_10_quotient <= next_state_comb_10_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_10_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_10_dividend <= next_state_comb_10_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_10_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_10_divisor <= REG_9_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_10_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_10_divideByZero <= REG_9_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_10_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_10_valid <= REG_9_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_11_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_11) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_11_remainder <= _next_state_comb_next_rem_T_23;
    end else begin
      REG_11_remainder <= next_state_comb_shifted_rem_11;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_11_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_11_quotient <= next_state_comb_11_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_11_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_11_dividend <= next_state_comb_11_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_11_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_11_divisor <= REG_10_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_11_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_11_divideByZero <= REG_10_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_11_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_11_valid <= REG_10_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_12_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_12) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_12_remainder <= _next_state_comb_next_rem_T_25;
    end else begin
      REG_12_remainder <= next_state_comb_shifted_rem_12;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_12_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_12_quotient <= next_state_comb_12_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_12_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_12_dividend <= next_state_comb_12_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_12_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_12_divisor <= REG_11_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_12_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_12_divideByZero <= REG_11_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_12_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_12_valid <= REG_11_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_13_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else if (next_state_comb_can_subtract_13) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 43:23]
      REG_13_remainder <= _next_state_comb_next_rem_T_27;
    end else begin
      REG_13_remainder <= next_state_comb_shifted_rem_13;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_13_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_13_quotient <= next_state_comb_13_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_13_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_13_dividend <= next_state_comb_13_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_13_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_13_divisor <= REG_12_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_13_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_13_divideByZero <= REG_12_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_13_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_13_valid <= REG_12_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_14_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_14_quotient <= next_state_comb_14_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_14_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_14_divideByZero <= REG_13_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
      REG_14_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
    end else begin
      REG_14_valid <= REG_13_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/UnsignedDivider/UnsignedDivider.scala 76:14]
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
  REG_3_remainder = _RAND_18[11:0];
  _RAND_19 = {1{`RANDOM}};
  REG_3_quotient = _RAND_19[14:0];
  _RAND_20 = {1{`RANDOM}};
  REG_3_dividend = _RAND_20[14:0];
  _RAND_21 = {1{`RANDOM}};
  REG_3_divisor = _RAND_21[10:0];
  _RAND_22 = {1{`RANDOM}};
  REG_3_divideByZero = _RAND_22[0:0];
  _RAND_23 = {1{`RANDOM}};
  REG_3_valid = _RAND_23[0:0];
  _RAND_24 = {1{`RANDOM}};
  REG_4_remainder = _RAND_24[11:0];
  _RAND_25 = {1{`RANDOM}};
  REG_4_quotient = _RAND_25[14:0];
  _RAND_26 = {1{`RANDOM}};
  REG_4_dividend = _RAND_26[14:0];
  _RAND_27 = {1{`RANDOM}};
  REG_4_divisor = _RAND_27[10:0];
  _RAND_28 = {1{`RANDOM}};
  REG_4_divideByZero = _RAND_28[0:0];
  _RAND_29 = {1{`RANDOM}};
  REG_4_valid = _RAND_29[0:0];
  _RAND_30 = {1{`RANDOM}};
  REG_5_remainder = _RAND_30[11:0];
  _RAND_31 = {1{`RANDOM}};
  REG_5_quotient = _RAND_31[14:0];
  _RAND_32 = {1{`RANDOM}};
  REG_5_dividend = _RAND_32[14:0];
  _RAND_33 = {1{`RANDOM}};
  REG_5_divisor = _RAND_33[10:0];
  _RAND_34 = {1{`RANDOM}};
  REG_5_divideByZero = _RAND_34[0:0];
  _RAND_35 = {1{`RANDOM}};
  REG_5_valid = _RAND_35[0:0];
  _RAND_36 = {1{`RANDOM}};
  REG_6_remainder = _RAND_36[11:0];
  _RAND_37 = {1{`RANDOM}};
  REG_6_quotient = _RAND_37[14:0];
  _RAND_38 = {1{`RANDOM}};
  REG_6_dividend = _RAND_38[14:0];
  _RAND_39 = {1{`RANDOM}};
  REG_6_divisor = _RAND_39[10:0];
  _RAND_40 = {1{`RANDOM}};
  REG_6_divideByZero = _RAND_40[0:0];
  _RAND_41 = {1{`RANDOM}};
  REG_6_valid = _RAND_41[0:0];
  _RAND_42 = {1{`RANDOM}};
  REG_7_remainder = _RAND_42[11:0];
  _RAND_43 = {1{`RANDOM}};
  REG_7_quotient = _RAND_43[14:0];
  _RAND_44 = {1{`RANDOM}};
  REG_7_dividend = _RAND_44[14:0];
  _RAND_45 = {1{`RANDOM}};
  REG_7_divisor = _RAND_45[10:0];
  _RAND_46 = {1{`RANDOM}};
  REG_7_divideByZero = _RAND_46[0:0];
  _RAND_47 = {1{`RANDOM}};
  REG_7_valid = _RAND_47[0:0];
  _RAND_48 = {1{`RANDOM}};
  REG_8_remainder = _RAND_48[11:0];
  _RAND_49 = {1{`RANDOM}};
  REG_8_quotient = _RAND_49[14:0];
  _RAND_50 = {1{`RANDOM}};
  REG_8_dividend = _RAND_50[14:0];
  _RAND_51 = {1{`RANDOM}};
  REG_8_divisor = _RAND_51[10:0];
  _RAND_52 = {1{`RANDOM}};
  REG_8_divideByZero = _RAND_52[0:0];
  _RAND_53 = {1{`RANDOM}};
  REG_8_valid = _RAND_53[0:0];
  _RAND_54 = {1{`RANDOM}};
  REG_9_remainder = _RAND_54[11:0];
  _RAND_55 = {1{`RANDOM}};
  REG_9_quotient = _RAND_55[14:0];
  _RAND_56 = {1{`RANDOM}};
  REG_9_dividend = _RAND_56[14:0];
  _RAND_57 = {1{`RANDOM}};
  REG_9_divisor = _RAND_57[10:0];
  _RAND_58 = {1{`RANDOM}};
  REG_9_divideByZero = _RAND_58[0:0];
  _RAND_59 = {1{`RANDOM}};
  REG_9_valid = _RAND_59[0:0];
  _RAND_60 = {1{`RANDOM}};
  REG_10_remainder = _RAND_60[11:0];
  _RAND_61 = {1{`RANDOM}};
  REG_10_quotient = _RAND_61[14:0];
  _RAND_62 = {1{`RANDOM}};
  REG_10_dividend = _RAND_62[14:0];
  _RAND_63 = {1{`RANDOM}};
  REG_10_divisor = _RAND_63[10:0];
  _RAND_64 = {1{`RANDOM}};
  REG_10_divideByZero = _RAND_64[0:0];
  _RAND_65 = {1{`RANDOM}};
  REG_10_valid = _RAND_65[0:0];
  _RAND_66 = {1{`RANDOM}};
  REG_11_remainder = _RAND_66[11:0];
  _RAND_67 = {1{`RANDOM}};
  REG_11_quotient = _RAND_67[14:0];
  _RAND_68 = {1{`RANDOM}};
  REG_11_dividend = _RAND_68[14:0];
  _RAND_69 = {1{`RANDOM}};
  REG_11_divisor = _RAND_69[10:0];
  _RAND_70 = {1{`RANDOM}};
  REG_11_divideByZero = _RAND_70[0:0];
  _RAND_71 = {1{`RANDOM}};
  REG_11_valid = _RAND_71[0:0];
  _RAND_72 = {1{`RANDOM}};
  REG_12_remainder = _RAND_72[11:0];
  _RAND_73 = {1{`RANDOM}};
  REG_12_quotient = _RAND_73[14:0];
  _RAND_74 = {1{`RANDOM}};
  REG_12_dividend = _RAND_74[14:0];
  _RAND_75 = {1{`RANDOM}};
  REG_12_divisor = _RAND_75[10:0];
  _RAND_76 = {1{`RANDOM}};
  REG_12_divideByZero = _RAND_76[0:0];
  _RAND_77 = {1{`RANDOM}};
  REG_12_valid = _RAND_77[0:0];
  _RAND_78 = {1{`RANDOM}};
  REG_13_remainder = _RAND_78[11:0];
  _RAND_79 = {1{`RANDOM}};
  REG_13_quotient = _RAND_79[14:0];
  _RAND_80 = {1{`RANDOM}};
  REG_13_dividend = _RAND_80[14:0];
  _RAND_81 = {1{`RANDOM}};
  REG_13_divisor = _RAND_81[10:0];
  _RAND_82 = {1{`RANDOM}};
  REG_13_divideByZero = _RAND_82[0:0];
  _RAND_83 = {1{`RANDOM}};
  REG_13_valid = _RAND_83[0:0];
  _RAND_84 = {1{`RANDOM}};
  REG_14_quotient = _RAND_84[14:0];
  _RAND_85 = {1{`RANDOM}};
  REG_14_divideByZero = _RAND_85[0:0];
  _RAND_86 = {1{`RANDOM}};
  REG_14_valid = _RAND_86[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
