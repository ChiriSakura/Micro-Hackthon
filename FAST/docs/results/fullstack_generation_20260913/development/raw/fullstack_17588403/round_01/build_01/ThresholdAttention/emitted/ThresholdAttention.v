module ScoreCalculatorBank(
  input  [7:0]  q_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 4:16]
  input  [31:0] k_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 5:16]
  output [35:0] scores_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 6:22]
);
  wire [3:0] q0 = q_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 9:16]
  wire [3:0] q1 = q_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 10:16]
  wire [3:0] k00 = k_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 14:17]
  wire [3:0] k01 = k_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 15:17]
  wire [3:0] k10 = k_in[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 17:17]
  wire [3:0] k11 = k_in[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 18:17]
  wire [3:0] k20 = k_in[19:16]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 20:17]
  wire [3:0] k21 = k_in[23:20]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 21:17]
  wire [3:0] k30 = k_in[27:24]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 23:17]
  wire [3:0] k31 = k_in[31:28]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 24:17]
  wire [7:0] _score0_T = q0 * k00; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 30:20]
  wire [7:0] _score0_T_1 = q1 * k01; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 30:33]
  wire [7:0] score0 = _score0_T + _score0_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 30:27]
  wire [7:0] _score1_T = q0 * k10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 31:20]
  wire [7:0] _score1_T_1 = q1 * k11; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 31:33]
  wire [7:0] score1 = _score1_T + _score1_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 31:27]
  wire [7:0] _score2_T = q0 * k20; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 32:20]
  wire [7:0] _score2_T_1 = q1 * k21; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 32:33]
  wire [7:0] score2 = _score2_T + _score2_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 32:27]
  wire [7:0] _score3_T = q0 * k30; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 33:20]
  wire [7:0] _score3_T_1 = q1 * k31; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 33:33]
  wire [7:0] score3 = _score3_T + _score3_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 33:27]
  wire [31:0] _scores_out_T_2 = {score3,score2,score1,score0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 37:44]
  assign scores_out = {{4'd0}, _scores_out_T_2}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ScoreCalculatorBank/ScoreCalculatorBank.scala 37:14]
endmodule
module Summer(
  input  [35:0] weights_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 4:22]
  input  [51:0] weighted_vs_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 5:26]
  output [10:0] sum_w_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 6:21]
  output [14:0] sum_wv_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 7:22]
);
  wire [8:0] w0 = weights_in[8:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 10:22]
  wire [8:0] w1 = weights_in[17:9]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 11:22]
  wire [8:0] w2 = weights_in[26:18]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 12:22]
  wire [8:0] w3 = weights_in[35:27]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 13:22]
  wire [12:0] wv0 = weighted_vs_in[12:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 16:27]
  wire [12:0] wv1 = weighted_vs_in[25:13]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 17:27]
  wire [12:0] wv2 = weighted_vs_in[38:26]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 18:27]
  wire [12:0] wv3 = weighted_vs_in[51:39]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 19:27]
  wire [8:0] sum_w_01 = w0 + w1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 23:21]
  wire [8:0] sum_w_23 = w2 + w3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 24:21]
  wire [8:0] _sum_w_out_T_1 = sum_w_01 + sum_w_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 27:25]
  wire [12:0] sum_wv_01 = wv0 + wv1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 31:23]
  wire [12:0] sum_wv_23 = wv2 + wv3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 32:23]
  wire [12:0] _sum_wv_out_T_1 = sum_wv_01 + sum_wv_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 35:27]
  assign sum_w_out = {{2'd0}, _sum_w_out_T_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 27:13]
  assign sum_wv_out = {{2'd0}, _sum_wv_out_T_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Summer/Summer.scala 35:14]
endmodule
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
module ThresholdAttention(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 7:17]
  input  [7:0]  q, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 8:13]
  input  [31:0] k, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 9:13]
  input  [15:0] v, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 10:13]
  output        done, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 11:16]
  output [3:0]  result // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 12:18]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [63:0] _RAND_5;
  reg [31:0] _RAND_6;
  reg [63:0] _RAND_7;
  reg [63:0] _RAND_8;
  reg [31:0] _RAND_9;
  reg [31:0] _RAND_10;
`endif // RANDOMIZE_REG_INIT
  wire [7:0] score_calc_q_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 15:26]
  wire [31:0] score_calc_k_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 15:26]
  wire [35:0] score_calc_scores_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 15:26]
  wire [35:0] summer_weights_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 16:22]
  wire [51:0] summer_weighted_vs_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 16:22]
  wire [10:0] summer_sum_w_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 16:22]
  wire [14:0] summer_sum_wv_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 16:22]
  wire  divider_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire  divider_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire  divider_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire [14:0] divider_numer_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire [10:0] divider_denom_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire [3:0] divider_quotient_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  wire  divider_done; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
  reg [1:0] state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 23:60]
  reg [1:0] pipe_counter_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 24:67]
  reg [7:0] q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 27:52]
  reg [31:0] k_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 28:52]
  reg [15:0] v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 29:52]
  reg [35:0] scores_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 32:57]
  reg [15:0] v_reg_p1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 33:55]
  reg [35:0] weights_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 36:58]
  reg [51:0] weighted_vs_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 37:62]
  reg [10:0] sum_w_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 40:56]
  reg [14:0] sum_wv_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 41:57]
  wire [8:0] scores_0 = scores_reg[8:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 53:28]
  wire [3:0] vs_0 = v_reg_p1[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 54:22]
  wire [8:0] weights_0 = scores_0 >= 9'h40 ? scores_0 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 55:22]
  wire [12:0] weighted_vs_0 = weights_0 * vs_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 56:34]
  wire [8:0] scores_1 = scores_reg[17:9]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 53:28]
  wire [3:0] vs_1 = v_reg_p1[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 54:22]
  wire [8:0] weights_1 = scores_1 >= 9'h40 ? scores_1 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 55:22]
  wire [12:0] weighted_vs_1 = weights_1 * vs_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 56:34]
  wire [8:0] scores_2 = scores_reg[26:18]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 53:28]
  wire [3:0] vs_2 = v_reg_p1[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 54:22]
  wire [8:0] weights_2 = scores_2 >= 9'h40 ? scores_2 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 55:22]
  wire [12:0] weighted_vs_2 = weights_2 * vs_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 56:34]
  wire [8:0] scores_3 = scores_reg[35:27]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 53:28]
  wire [3:0] vs_3 = v_reg_p1[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 54:22]
  wire [8:0] weights_3 = scores_3 >= 9'h40 ? scores_3 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 55:22]
  wire [12:0] weighted_vs_3 = weights_3 * vs_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 56:34]
  wire [35:0] weights_in_next = {weights_3,weights_2,weights_1,weights_0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 58:28]
  wire [51:0] weighted_vs_in_next = {weighted_vs_3,weighted_vs_2,weighted_vs_1,weighted_vs_0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 59:32]
  wire  _is_pipe_at_end_T = state_reg == 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 72:35]
  wire  _is_pipe_at_end_T_1 = pipe_counter_reg == 2'h3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 72:68]
  wire  is_pipe_at_end = state_reg == 2'h1 & pipe_counter_reg == 2'h3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 72:47]
  wire  _is_zero_denom_case_T = sum_w_reg == 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 73:57]
  wire  is_zero_denom_case = is_pipe_at_end & sum_w_reg == 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 73:43]
  wire  is_div_done = state_reg == 2'h2 & divider_done; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 75:48]
  wire [3:0] _GEN_0 = is_div_done ? divider_quotient_out : 4'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 82:29 83:12 85:12]
  wire [1:0] _pipe_counter_reg_T_1 = pipe_counter_reg + 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 99:46]
  wire [1:0] _GEN_4 = _is_zero_denom_case_T ? 2'h0 : 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 101:35 102:23 104:23]
  wire [1:0] _GEN_6 = divider_done ? 2'h0 : state_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 109:28 110:21 23:60]
  ScoreCalculatorBank score_calc ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 15:26]
    .q_in(score_calc_q_in),
    .k_in(score_calc_k_in),
    .scores_out(score_calc_scores_out)
  );
  Summer summer ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 16:22]
    .weights_in(summer_weights_in),
    .weighted_vs_in(summer_weighted_vs_in),
    .sum_w_out(summer_sum_w_out),
    .sum_wv_out(summer_sum_wv_out)
  );
  Divider divider ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 17:23]
    .clock(divider_clock),
    .reset(divider_reset),
    .start(divider_start),
    .numer_in(divider_numer_in),
    .denom_in(divider_denom_in),
    .quotient_out(divider_quotient_out),
    .done(divider_done)
  );
  assign done = is_zero_denom_case | is_div_done; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 78:30]
  assign result = is_zero_denom_case ? 4'h0 : _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 80:29 81:12]
  assign score_calc_q_in = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 62:19]
  assign score_calc_k_in = k_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 63:19]
  assign summer_weights_in = weights_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 64:21]
  assign summer_weighted_vs_in = weighted_vs_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 65:25]
  assign divider_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 66:17]
  assign divider_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 67:17]
  assign divider_start = is_pipe_at_end & sum_w_reg != 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 74:38]
  assign divider_numer_in = sum_wv_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 68:20]
  assign divider_denom_in = sum_w_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 69:20]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 23:60]
      state_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 23:60]
    end else if (2'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 91:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 93:21]
        state_reg <= 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 94:21]
      end
    end else if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 91:23]
      if (_is_pipe_at_end_T_1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 100:40]
        state_reg <= _GEN_4;
      end
    end else if (2'h2 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 91:23]
      state_reg <= _GEN_6;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 24:67]
      pipe_counter_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 24:67]
    end else if (2'h0 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 91:23]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 93:21]
        pipe_counter_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 95:28]
      end
    end else if (2'h1 == state_reg) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 91:23]
      pipe_counter_reg <= _pipe_counter_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 99:26]
    end
    if (state_reg == 2'h0 & start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 116:41]
      q_reg <= q; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 118:13]
    end
    if (state_reg == 2'h0 & start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 116:41]
      k_reg <= k; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 119:13]
    end
    if (state_reg == 2'h0 & start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 116:41]
      v_reg <= v; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 120:13]
    end
    if (_is_pipe_at_end_T) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 123:32]
      scores_reg <= score_calc_scores_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 125:18]
    end
    if (_is_pipe_at_end_T) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 123:32]
      v_reg_p1 <= v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 126:16]
    end
    if (_is_pipe_at_end_T) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 123:32]
      weights_reg <= weights_in_next; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 128:19]
    end
    if (_is_pipe_at_end_T) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 123:32]
      weighted_vs_reg <= weighted_vs_in_next; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 129:23]
    end
    if (_is_pipe_at_end_T) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 123:32]
      sum_w_reg <= summer_sum_w_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 131:17]
    end
    if (_is_pipe_at_end_T) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 123:32]
      sum_wv_reg <= summer_sum_wv_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/ThresholdAttention/ThresholdAttention.scala 132:18]
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
  pipe_counter_reg = _RAND_1[1:0];
  _RAND_2 = {1{`RANDOM}};
  q_reg = _RAND_2[7:0];
  _RAND_3 = {1{`RANDOM}};
  k_reg = _RAND_3[31:0];
  _RAND_4 = {1{`RANDOM}};
  v_reg = _RAND_4[15:0];
  _RAND_5 = {2{`RANDOM}};
  scores_reg = _RAND_5[35:0];
  _RAND_6 = {1{`RANDOM}};
  v_reg_p1 = _RAND_6[15:0];
  _RAND_7 = {2{`RANDOM}};
  weights_reg = _RAND_7[35:0];
  _RAND_8 = {2{`RANDOM}};
  weighted_vs_reg = _RAND_8[51:0];
  _RAND_9 = {1{`RANDOM}};
  sum_w_reg = _RAND_9[10:0];
  _RAND_10 = {1{`RANDOM}};
  sum_wv_reg = _RAND_10[14:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
