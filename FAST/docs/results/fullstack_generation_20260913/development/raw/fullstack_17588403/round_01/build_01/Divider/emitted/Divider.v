module Divider(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 7:17]
  input  [14:0] numer_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 8:20]
  input  [10:0] denom_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 9:20]
  output [3:0]  quotient_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 10:24]
  output        done // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 11:16]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
`endif // RANDOMIZE_REG_INIT
  reg [1:0] state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 26:28]
  reg [11:0] p_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 27:20]
  reg [14:0] a_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 28:20]
  reg [10:0] d_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 29:20]
  reg [3:0] q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 30:20]
  reg [2:0] cycle_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 31:24]
  wire [11:0] p_shifted = {p_reg[10:0],a_reg[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 39:49]
  wire [15:0] a_next = {a_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 40:24]
  wire [11:0] d_ext = {1'b0,$signed(d_reg)}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 41:23]
  wire [11:0] p_plus_d = $signed(p_shifted) + $signed(d_ext); // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 43:30]
  wire [11:0] p_minus_d = $signed(p_shifted) - $signed(d_ext); // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 44:31]
  wire [11:0] p_next = p_reg[11] ? $signed(p_plus_d) : $signed(p_minus_d); // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 45:21]
  wire  q_bit = ~p_next[11]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 47:17]
  wire [4:0] _q_next_T = {q_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 48:25]
  wire [4:0] _GEN_20 = {{4'd0}, q_bit}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 48:31]
  wire [4:0] q_next = _q_next_T | _GEN_20; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 48:31]
  wire [2:0] _cycle_reg_T_1 = cycle_reg - 3'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 71:32]
  wire [1:0] _GEN_1 = cycle_reg == 3'h1 ? 2'h3 : state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 74:33 75:21 26:28]
  wire [1:0] _GEN_2 = 2'h3 == state_reg ? 2'h0 : state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23 80:19 26:28]
  wire [15:0] _GEN_4 = 2'h2 == state_reg ? a_next : {{1'd0}, a_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23 69:15 28:20]
  wire [4:0] _GEN_5 = 2'h2 == state_reg ? q_next : {{1'd0}, q_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23 70:15 30:20]
  wire [15:0] _GEN_10 = 2'h1 == state_reg ? {{1'd0}, numer_in} : _GEN_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23 61:15]
  wire [4:0] _GEN_12 = 2'h1 == state_reg ? 5'h0 : _GEN_5; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23 63:15]
  wire [15:0] _GEN_16 = 2'h0 == state_reg ? {{1'd0}, a_reg} : _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 28:20 51:23]
  wire [4:0] _GEN_18 = 2'h0 == state_reg ? {{1'd0}, q_reg} : _GEN_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 30:20 51:23]
  assign quotient_out = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 18:23 35:15]
  assign done = state_reg == 2'h3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 22:25]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 26:28]
      state_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 26:28]
    end else if (2'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 53:21]
        state_reg <= 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 54:21]
      end
    end else if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      state_reg <= 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 58:19]
    end else if (2'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      state_reg <= _GEN_1;
    end else begin
      state_reg <= _GEN_2;
    end
    if (!(2'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        p_reg <= 12'sh0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 60:15]
      end else if (2'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        if (p_reg[11]) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 45:21]
          p_reg <= p_plus_d;
        end else begin
          p_reg <= p_minus_d;
        end
      end
    end
    a_reg <= _GEN_16[14:0];
    if (!(2'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        d_reg <= denom_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 62:15]
      end
    end
    q_reg <= _GEN_18[3:0];
    if (!(2'h0 == state_reg)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        cycle_reg <= 3'h4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 64:19]
      end else if (2'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        cycle_reg <= _cycle_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 71:19]
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
  state_reg = _RAND_0[1:0];
  _RAND_1 = {1{`RANDOM}};
  p_reg = _RAND_1[11:0];
  _RAND_2 = {1{`RANDOM}};
  a_reg = _RAND_2[14:0];
  _RAND_3 = {1{`RANDOM}};
  d_reg = _RAND_3[10:0];
  _RAND_4 = {1{`RANDOM}};
  q_reg = _RAND_4[3:0];
  _RAND_5 = {1{`RANDOM}};
  cycle_reg = _RAND_5[2:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
