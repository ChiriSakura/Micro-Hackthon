module Divider15by11(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 7:17]
  input  [14:0] dividend, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 8:20]
  input  [10:0] divisor, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 9:19]
  output [14:0] quotient, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 10:20]
  output        valid_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 11:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
`endif // RANDOMIZE_REG_INIT
  reg [1:0] state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 16:24]
  reg [14:0] dividend_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 19:31]
  reg [10:0] divisor_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 20:30]
  reg [10:0] rem_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 21:26]
  reg [14:0] quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 22:31]
  reg [3:0] count_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 23:28]
  wire [14:0] _GEN_0 = start ? dividend : dividend_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21 29:24 19:31]
  wire [10:0] _GEN_2 = start ? 11'h0 : rem_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21 31:19 21:26]
  wire [14:0] _GEN_3 = start ? 15'h0 : quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21 32:24 22:31]
  wire [11:0] _next_rem_val_T = {rem_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 39:37]
  wire [11:0] _GEN_21 = {{11'd0}, dividend_reg[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 39:43]
  wire [11:0] next_rem_val = _next_rem_val_T | _GEN_21; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 39:43]
  wire [15:0] _dividend_reg_T = {dividend_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 42:38]
  wire [11:0] _GEN_22 = {{1'd0}, divisor_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 45:27]
  wire [11:0] _rem_reg_T_1 = next_rem_val - _GEN_22; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 47:35]
  wire [15:0] _quotient_reg_T = {quotient_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 48:41]
  wire [15:0] _quotient_reg_T_1 = _quotient_reg_T | 16'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 48:47]
  wire [11:0] _GEN_6 = next_rem_val >= _GEN_22 ? _rem_reg_T_1 : {{1'd0}, next_rem_val[10:0]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 45:43 47:19 51:19]
  wire [15:0] _GEN_7 = next_rem_val >= _GEN_22 ? _quotient_reg_T_1 : _quotient_reg_T; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 45:43 48:24 52:24]
  wire [3:0] _count_reg_T_1 = count_reg - 4'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 56:32]
  wire [15:0] _GEN_10 = 2'h1 == state ? _dividend_reg_T : {{1'd0}, dividend_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19 42:22 19:31]
  wire [11:0] _GEN_11 = 2'h1 == state ? _GEN_6 : {{1'd0}, rem_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19 21:26]
  wire [15:0] _GEN_12 = 2'h1 == state ? _GEN_7 : {{1'd0}, quotient_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19 22:31]
  wire [15:0] _GEN_15 = 2'h0 == state ? {{1'd0}, _GEN_0} : _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
  wire [11:0] _GEN_17 = 2'h0 == state ? {{1'd0}, _GEN_2} : _GEN_11; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
  wire [15:0] _GEN_18 = 2'h0 == state ? {{1'd0}, _GEN_3} : _GEN_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
  wire [15:0] _GEN_24 = reset ? 16'h0 : _GEN_15; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 19:{31,31}]
  wire [11:0] _GEN_25 = reset ? 12'h0 : _GEN_17; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 21:{26,26}]
  wire [15:0] _GEN_26 = reset ? 16'h0 : _GEN_18; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 22:{31,31}]
  assign quotient = quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 67:14]
  assign valid_out = state == 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 68:24]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 16:24]
      state <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 16:24]
    end else if (2'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21]
        state <= 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 34:17]
      end
    end else if (2'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      if (count_reg == 4'h0) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 57:33]
        state <= 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 58:17]
      end
    end else if (2'h2 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      state <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 62:15]
    end
    dividend_reg <= _GEN_24[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 19:{31,31}]
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 20:30]
      divisor_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 20:30]
    end else if (2'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21]
        divisor_reg <= divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 30:23]
      end
    end
    rem_reg <= _GEN_25[10:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 21:{26,26}]
    quotient_reg <= _GEN_26[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 22:{31,31}]
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 23:28]
      count_reg <= 4'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 23:28]
    end else if (2'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21]
        count_reg <= 4'he; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 33:21]
      end
    end else if (2'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      count_reg <= _count_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 56:19]
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
  state = _RAND_0[1:0];
  _RAND_1 = {1{`RANDOM}};
  dividend_reg = _RAND_1[14:0];
  _RAND_2 = {1{`RANDOM}};
  divisor_reg = _RAND_2[10:0];
  _RAND_3 = {1{`RANDOM}};
  rem_reg = _RAND_3[10:0];
  _RAND_4 = {1{`RANDOM}};
  quotient_reg = _RAND_4[14:0];
  _RAND_5 = {1{`RANDOM}};
  count_reg = _RAND_5[3:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
