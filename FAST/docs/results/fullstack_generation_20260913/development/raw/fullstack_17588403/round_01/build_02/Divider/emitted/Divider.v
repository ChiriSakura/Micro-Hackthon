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
