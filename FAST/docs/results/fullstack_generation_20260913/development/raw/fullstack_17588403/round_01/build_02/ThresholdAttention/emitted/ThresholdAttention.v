module ProcessingElement(
  input  [3:0]  q0, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 5:14]
  input  [3:0]  q1, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 6:14]
  input  [3:0]  k0, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 7:14]
  input  [3:0]  k1, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 8:14]
  input  [3:0]  v_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 9:16]
  output [8:0]  weight_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 10:22]
  output [12:0] weighted_v_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 11:26]
);
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 15:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 16:18]
  wire [7:0] score = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 18:21]
  wire [8:0] _GEN_0 = {{1'd0}, score}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:26]
  wire [8:0] weight = _GEN_0 >= 9'h40 ? {{1'd0}, score} : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:19]
  assign weight_out = _GEN_0 >= 9'h40 ? {{1'd0}, score} : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:19]
  assign weighted_v_out = weight * v_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 27:27]
endmodule
module Divider(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 7:17]
  input  [14:0] numer_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 8:20]
  input  [10:0] denom_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 9:20]
  output [3:0]  quotient_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 10:24]
  output        done // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 11:16]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
`endif // RANDOMIZE_REG_INIT
  reg [1:0] state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 17:28]
  reg [14:0] remainder_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 18:32]
  reg [10:0] divisor_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 19:30]
  reg [3:0] quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 20:31]
  reg [2:0] cycle_counter_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 21:36]
  wire [14:0] _GEN_0 = start ? numer_in : remainder_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 29:21 30:25 18:32]
  wire [3:0] _GEN_2 = start ? 4'h0 : quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 29:21 32:24 20:31]
  wire [15:0] rem_shifted_left = {remainder_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 39:46]
  wire [4:0] quot_shifted_left = {quotient_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 40:46]
  wire [10:0] rem_msbs = rem_shifted_left[14:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 43:40]
  wire [11:0] _trial_sub_ext_T = {1'h0,rem_msbs}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:32]
  wire [11:0] _trial_sub_ext_T_1 = {1'h0,divisor_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:58]
  wire [11:0] trial_sub_ext = _trial_sub_ext_T - _trial_sub_ext_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:53]
  wire  sub_successful = ~trial_sub_ext[11]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 47:30]
  wire [14:0] _remainder_reg_T_2 = {trial_sub_ext[10:0],rem_shifted_left[3:0]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 51:31]
  wire [15:0] _GEN_5 = sub_successful ? {{1'd0}, _remainder_reg_T_2} : rem_shifted_left; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 49:30 51:25 54:25]
  wire [4:0] _GEN_20 = {{4'd0}, sub_successful}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 57:43]
  wire [4:0] _quotient_reg_T = quot_shifted_left | _GEN_20; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 57:43]
  wire [2:0] _cycle_counter_reg_T_1 = cycle_counter_reg - 3'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 59:48]
  wire [15:0] _GEN_9 = 2'h1 == state_reg ? _GEN_5 : {{1'd0}, remainder_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23 18:32]
  wire [4:0] _GEN_10 = 2'h1 == state_reg ? _quotient_reg_T : {{1'd0}, quotient_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23 57:22 20:31]
  wire  _GEN_13 = 2'h1 == state_reg ? 1'h0 : 2'h2 == state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 24:10 27:23]
  wire [15:0] _GEN_14 = 2'h0 == state_reg ? {{1'd0}, _GEN_0} : _GEN_9; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
  wire [4:0] _GEN_16 = 2'h0 == state_reg ? {{1'd0}, _GEN_2} : _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
  wire [15:0] _GEN_21 = reset ? 16'h0 : _GEN_14; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 18:{32,32}]
  wire [4:0] _GEN_22 = reset ? 5'h0 : _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 20:{31,31}]
  assign quotient_out = quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 72:18]
  assign done = 2'h0 == state_reg ? 1'h0 : _GEN_13; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 24:10 27:23]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 17:28]
      state_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 17:28]
    end else if (2'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 29:21]
        state_reg <= 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 34:21]
      end
    end else if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      if (cycle_counter_reg == 3'h1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 60:41]
        state_reg <= 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 61:21]
      end
    end else if (2'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      state_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 67:19]
    end
    remainder_reg <= _GEN_21[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 18:{32,32}]
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 19:30]
      divisor_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 19:30]
    end else if (2'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 29:21]
        divisor_reg <= denom_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 31:23]
      end
    end
    quotient_reg <= _GEN_22[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 20:{31,31}]
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 21:36]
      cycle_counter_reg <= 3'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 21:36]
    end else if (2'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 29:21]
        cycle_counter_reg <= 3'h4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 33:29]
      end
    end else if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      cycle_counter_reg <= _cycle_counter_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 59:27]
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
  state_reg = _RAND_0[1:0];
  _RAND_1 = {1{`RANDOM}};
  remainder_reg = _RAND_1[14:0];
  _RAND_2 = {1{`RANDOM}};
  divisor_reg = _RAND_2[10:0];
  _RAND_3 = {1{`RANDOM}};
  quotient_reg = _RAND_3[3:0];
  _RAND_4 = {1{`RANDOM}};
  cycle_counter_reg = _RAND_4[2:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
module ThresholdAttention(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 7:17]
  input  [7:0]  q, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 8:13]
  input  [31:0] k, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 9:13]
  input  [15:0] v, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 10:13]
  output        done, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 11:16]
  output [3:0]  result // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 12:18]
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
`endif // RANDOMIZE_REG_INIT
  wire [3:0] pes_0_q0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_0_q1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_0_k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_0_k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_0_v_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [8:0] pes_0_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [12:0] pes_0_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_1_q0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_1_q1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_1_k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_1_k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_1_v_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [8:0] pes_1_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [12:0] pes_1_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_2_q0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_2_q1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_2_k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_2_k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_2_v_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [8:0] pes_2_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [12:0] pes_2_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_3_q0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_3_q1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_3_k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_3_k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [3:0] pes_3_v_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [8:0] pes_3_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire [12:0] pes_3_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
  wire  divider_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire  divider_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire  divider_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire [14:0] divider_numer_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire [10:0] divider_denom_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire [3:0] divider_quotient_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire  divider_done; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
  reg [2:0] state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 24:28]
  reg [7:0] q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 25:24]
  reg [31:0] k_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 26:24]
  reg [15:0] v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 27:24]
  reg [8:0] pe_weights_reg_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
  reg [8:0] pe_weights_reg_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
  reg [8:0] pe_weights_reg_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
  reg [8:0] pe_weights_reg_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
  reg [12:0] pe_weighted_vs_reg_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
  reg [12:0] pe_weighted_vs_reg_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
  reg [12:0] pe_weighted_vs_reg_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
  reg [12:0] pe_weighted_vs_reg_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
  reg [10:0] sum_w_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 30:28]
  reg [14:0] sum_wv_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 31:29]
  reg [3:0] result_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 32:29]
  wire [8:0] sum_w_stage1_0 = pe_weights_reg_0 + pe_weights_reg_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 46:44]
  wire [8:0] sum_w_stage1_1 = pe_weights_reg_2 + pe_weights_reg_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 47:44]
  wire [8:0] sum_w_comb = sum_w_stage1_0 + sum_w_stage1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 48:37]
  wire [12:0] sum_wv_stage1_0 = pe_weighted_vs_reg_0 + pe_weighted_vs_reg_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 50:49]
  wire [12:0] sum_wv_stage1_1 = pe_weighted_vs_reg_2 + pe_weighted_vs_reg_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 51:49]
  wire [12:0] sum_wv_comb = sum_wv_stage1_0 + sum_wv_stage1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 52:39]
  wire [3:0] _GEN_4 = sum_w_reg == 11'h0 ? 4'h0 : result_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 82:33 83:22 32:29]
  wire [2:0] _GEN_5 = sum_w_reg == 11'h0 ? 3'h5 : 3'h4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 82:33 84:21 86:21]
  wire [3:0] _GEN_6 = divider_done ? divider_quotient_out : result_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 90:28 91:22 32:29]
  wire [2:0] _GEN_7 = divider_done ? 3'h5 : state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 90:28 92:21 24:28]
  wire [2:0] _GEN_8 = 3'h5 == state_reg ? 3'h0 : state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23 96:19 24:28]
  wire [3:0] _GEN_9 = 3'h4 == state_reg ? _GEN_6 : result_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23 32:29]
  wire [2:0] _GEN_10 = 3'h4 == state_reg ? _GEN_7 : _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
  wire [3:0] _GEN_11 = 3'h3 == state_reg ? _GEN_4 : _GEN_9; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
  wire [2:0] _GEN_12 = 3'h3 == state_reg ? _GEN_5 : _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
  ProcessingElement pes_0 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
    .q0(pes_0_q0),
    .q1(pes_0_q1),
    .k0(pes_0_k0),
    .k1(pes_0_k1),
    .v_in(pes_0_v_in),
    .weight_out(pes_0_weight_out),
    .weighted_v_out(pes_0_weighted_v_out)
  );
  ProcessingElement pes_1 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
    .q0(pes_1_q0),
    .q1(pes_1_q1),
    .k0(pes_1_k0),
    .k1(pes_1_k1),
    .v_in(pes_1_v_in),
    .weight_out(pes_1_weight_out),
    .weighted_v_out(pes_1_weighted_v_out)
  );
  ProcessingElement pes_2 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
    .q0(pes_2_q0),
    .q1(pes_2_q1),
    .k0(pes_2_k0),
    .k1(pes_2_k1),
    .v_in(pes_2_v_in),
    .weight_out(pes_2_weight_out),
    .weighted_v_out(pes_2_weighted_v_out)
  );
  ProcessingElement pes_3 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 16:31]
    .q0(pes_3_q0),
    .q1(pes_3_q1),
    .k0(pes_3_k0),
    .k1(pes_3_k1),
    .v_in(pes_3_v_in),
    .weight_out(pes_3_weight_out),
    .weighted_v_out(pes_3_weighted_v_out)
  );
  Divider divider ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 17:23]
    .clock(divider_clock),
    .reset(divider_reset),
    .start(divider_start),
    .numer_in(divider_numer_in),
    .denom_in(divider_denom_in),
    .quotient_out(divider_quotient_out),
    .done(divider_done)
  );
  assign done = state_reg == 3'h5; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 101:23]
  assign result = result_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 102:12]
  assign pes_0_q0 = q_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 35:19]
  assign pes_0_q1 = q_reg[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 36:19]
  assign pes_0_k0 = k_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 40:25]
  assign pes_0_k1 = k_reg[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 41:25]
  assign pes_0_v_in = v_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 42:27]
  assign pes_1_q0 = q_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 35:19]
  assign pes_1_q1 = q_reg[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 36:19]
  assign pes_1_k0 = k_reg[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 40:25]
  assign pes_1_k1 = k_reg[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 41:25]
  assign pes_1_v_in = v_reg[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 42:27]
  assign pes_2_q0 = q_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 35:19]
  assign pes_2_q1 = q_reg[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 36:19]
  assign pes_2_k0 = k_reg[19:16]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 40:25]
  assign pes_2_k1 = k_reg[23:20]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 41:25]
  assign pes_2_v_in = v_reg[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 42:27]
  assign pes_3_q0 = q_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 35:19]
  assign pes_3_q1 = q_reg[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 36:19]
  assign pes_3_k0 = k_reg[27:24]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 40:25]
  assign pes_3_k1 = k_reg[31:28]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 41:25]
  assign pes_3_v_in = v_reg[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 42:27]
  assign divider_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 19:17]
  assign divider_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 20:17]
  assign divider_start = state_reg == 3'h3 & sum_w_reg != 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 57:50]
  assign divider_numer_in = sum_wv_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 55:22]
  assign divider_denom_in = sum_w_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 56:22]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 24:28]
      state_reg <= 3'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 24:28]
    end else if (3'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 62:21]
        state_reg <= 3'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 66:21]
      end
    end else if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      state_reg <= 3'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 74:19]
    end else if (3'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      state_reg <= 3'h3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 79:19]
    end else begin
      state_reg <= _GEN_12;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 25:24]
      q_reg <= 8'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 25:24]
    end else if (3'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 62:21]
        q_reg <= q; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 63:17]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 26:24]
      k_reg <= 32'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 26:24]
    end else if (3'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 62:21]
        k_reg <= k; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 64:17]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 27:24]
      v_reg <= 16'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 27:24]
    end else if (3'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 62:21]
        v_reg <= v; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 65:17]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
      pe_weights_reg_0 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weights_reg_0 <= pes_0_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 71:29]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
      pe_weights_reg_1 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weights_reg_1 <= pes_1_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 71:29]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
      pe_weights_reg_2 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weights_reg_2 <= pes_2_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 71:29]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
      pe_weights_reg_3 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 28:33]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weights_reg_3 <= pes_3_weight_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 71:29]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
      pe_weighted_vs_reg_0 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weighted_vs_reg_0 <= pes_0_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 72:33]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
      pe_weighted_vs_reg_1 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weighted_vs_reg_1 <= pes_1_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 72:33]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
      pe_weighted_vs_reg_2 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weighted_vs_reg_2 <= pes_2_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 72:33]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
      pe_weighted_vs_reg_3 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 29:37]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (3'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        pe_weighted_vs_reg_3 <= pes_3_weighted_v_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 72:33]
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 30:28]
      sum_w_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 30:28]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (!(3'h1 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        if (3'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
          sum_w_reg <= {{2'd0}, sum_w_comb}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 77:19]
        end
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 31:29]
      sum_wv_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 31:29]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (!(3'h1 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        if (3'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
          sum_wv_reg <= {{2'd0}, sum_wv_comb}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 78:20]
        end
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 32:29]
      result_reg <= 4'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 32:29]
    end else if (!(3'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
      if (!(3'h1 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
        if (!(3'h2 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ThresholdAttention/ThresholdAttention.scala 60:23]
          result_reg <= _GEN_11;
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
  state_reg = _RAND_0[2:0];
  _RAND_1 = {1{`RANDOM}};
  q_reg = _RAND_1[7:0];
  _RAND_2 = {1{`RANDOM}};
  k_reg = _RAND_2[31:0];
  _RAND_3 = {1{`RANDOM}};
  v_reg = _RAND_3[15:0];
  _RAND_4 = {1{`RANDOM}};
  pe_weights_reg_0 = _RAND_4[8:0];
  _RAND_5 = {1{`RANDOM}};
  pe_weights_reg_1 = _RAND_5[8:0];
  _RAND_6 = {1{`RANDOM}};
  pe_weights_reg_2 = _RAND_6[8:0];
  _RAND_7 = {1{`RANDOM}};
  pe_weights_reg_3 = _RAND_7[8:0];
  _RAND_8 = {1{`RANDOM}};
  pe_weighted_vs_reg_0 = _RAND_8[12:0];
  _RAND_9 = {1{`RANDOM}};
  pe_weighted_vs_reg_1 = _RAND_9[12:0];
  _RAND_10 = {1{`RANDOM}};
  pe_weighted_vs_reg_2 = _RAND_10[12:0];
  _RAND_11 = {1{`RANDOM}};
  pe_weighted_vs_reg_3 = _RAND_11[12:0];
  _RAND_12 = {1{`RANDOM}};
  sum_w_reg = _RAND_12[10:0];
  _RAND_13 = {1{`RANDOM}};
  sum_wv_reg = _RAND_13[14:0];
  _RAND_14 = {1{`RANDOM}};
  result_reg = _RAND_14[3:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
