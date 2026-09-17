module ScoreAndWeightUnit(
  input  [7:0] q_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 5:17]
  input  [7:0] k_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 6:17]
  output [8:0] weight // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 8:18]
);
  wire [3:0] q0 = q_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 11:17]
  wire [3:0] q1 = q_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 12:17]
  wire [3:0] k0 = k_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 13:17]
  wire [3:0] k1 = k_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 14:17]
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 18:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 19:18]
  wire [8:0] score = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 25:21]
  wire  score_ge_thresh = score >= 9'h40; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 28:31]
  assign weight = score_ge_thresh ? score : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ScoreAndWeightUnit.scala 33:16]
endmodule
module Divider15by11(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 7:17]
  input  [14:0] dividend, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 8:20]
  input  [10:0] divisor, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 9:19]
  output [14:0] quotient, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 10:20]
  output        valid_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 11:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
`endif // RANDOMIZE_REG_INIT
  reg [1:0] state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 16:24]
  reg [14:0] dividend_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 19:31]
  reg [10:0] divisor_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 20:30]
  reg [10:0] rem_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 21:26]
  reg [14:0] quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 22:31]
  reg [3:0] count_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 23:28]
  wire [14:0] _GEN_0 = start ? dividend : dividend_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 28:21 29:24 19:31]
  wire [10:0] _GEN_2 = start ? 11'h0 : rem_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 28:21 31:19 21:26]
  wire [14:0] _GEN_3 = start ? 15'h0 : quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 28:21 32:24 22:31]
  wire [11:0] _next_rem_val_T = {rem_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 39:37]
  wire [11:0] _GEN_21 = {{11'd0}, dividend_reg[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 39:43]
  wire [11:0] next_rem_val = _next_rem_val_T | _GEN_21; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 39:43]
  wire [15:0] _dividend_reg_T = {dividend_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 42:38]
  wire [11:0] _GEN_22 = {{1'd0}, divisor_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 45:27]
  wire [11:0] _rem_reg_T_1 = next_rem_val - _GEN_22; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 47:35]
  wire [15:0] _quotient_reg_T = {quotient_reg, 1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 48:41]
  wire [15:0] _quotient_reg_T_1 = _quotient_reg_T | 16'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 48:47]
  wire [11:0] _GEN_6 = next_rem_val >= _GEN_22 ? _rem_reg_T_1 : {{1'd0}, next_rem_val[10:0]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 45:43 47:19 51:19]
  wire [15:0] _GEN_7 = next_rem_val >= _GEN_22 ? _quotient_reg_T_1 : _quotient_reg_T; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 45:43 48:24 52:24]
  wire [3:0] _count_reg_T_1 = count_reg - 4'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 56:32]
  wire [15:0] _GEN_10 = 2'h1 == state ? _dividend_reg_T : {{1'd0}, dividend_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19 42:22 19:31]
  wire [11:0] _GEN_11 = 2'h1 == state ? _GEN_6 : {{1'd0}, rem_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19 21:26]
  wire [15:0] _GEN_12 = 2'h1 == state ? _GEN_7 : {{1'd0}, quotient_reg}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19 22:31]
  wire [15:0] _GEN_15 = 2'h0 == state ? {{1'd0}, _GEN_0} : _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
  wire [11:0] _GEN_17 = 2'h0 == state ? {{1'd0}, _GEN_2} : _GEN_11; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
  wire [15:0] _GEN_18 = 2'h0 == state ? {{1'd0}, _GEN_3} : _GEN_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
  wire [15:0] _GEN_24 = reset ? 16'h0 : _GEN_15; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 19:{31,31}]
  wire [11:0] _GEN_25 = reset ? 12'h0 : _GEN_17; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 21:{26,26}]
  wire [15:0] _GEN_26 = reset ? 16'h0 : _GEN_18; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 22:{31,31}]
  assign quotient = quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 67:14]
  assign valid_out = state == 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 68:24]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 16:24]
      state <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 16:24]
    end else if (2'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 28:21]
        state <= 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 34:17]
      end
    end else if (2'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
      if (count_reg == 4'h0) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 57:33]
        state <= 2'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 58:17]
      end
    end else if (2'h2 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
      state <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 62:15]
    end
    dividend_reg <= _GEN_24[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 19:{31,31}]
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 20:30]
      divisor_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 20:30]
    end else if (2'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 28:21]
        divisor_reg <= divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 30:23]
      end
    end
    rem_reg <= _GEN_25[10:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 21:{26,26}]
    quotient_reg <= _GEN_26[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 22:{31,31}]
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 23:28]
      count_reg <= 4'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 23:28]
    end else if (2'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 28:21]
        count_reg <= 4'he; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 33:21]
      end
    end else if (2'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 26:19]
      count_reg <= _count_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/Divider15by11.scala 56:19]
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
module ThresholdAttention(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 6:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 7:17]
  input  [7:0]  q, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 8:13]
  input  [31:0] k, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 9:13]
  input  [15:0] v, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 10:13]
  output        done, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 11:16]
  output [3:0]  result // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 12:18]
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
  wire [7:0] score_weight_unit_q_vec; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 32:35]
  wire [7:0] score_weight_unit_k_vec; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 32:35]
  wire [8:0] score_weight_unit_weight; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 32:35]
  wire  divider_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  wire  divider_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  wire  divider_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  wire [14:0] divider_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  wire [10:0] divider_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  wire [14:0] divider_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  wire  divider_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
  reg [2:0] state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 18:24]
  reg [7:0] q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 21:20]
  reg [31:0] k_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 22:20]
  reg [15:0] v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 23:20]
  reg [1:0] idx_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 26:22]
  reg [10:0] weight_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 27:33]
  reg [14:0] weighted_value_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 28:41]
  reg [14:0] final_quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 29:37]
  wire [4:0] _k_i_T = {idx_reg, 3'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 40:34]
  wire [31:0] _k_i_T_1 = k_reg >> _k_i_T; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 40:22]
  wire [3:0] _GEN_34 = {idx_reg, 2'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 41:34]
  wire [4:0] _v_i_T = {{1'd0}, _GEN_34}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 41:34]
  wire [15:0] _v_i_T_1 = v_reg >> _v_i_T; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 41:22]
  wire [3:0] v_i = _v_i_T_1[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 41:42]
  wire [10:0] _GEN_35 = {{2'd0}, score_weight_unit_weight}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 69:43]
  wire [11:0] _weight_sum_reg_T = weight_sum_reg + _GEN_35; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 69:43]
  wire [12:0] weighted_prod = score_weight_unit_weight * v_i; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 70:44]
  wire [14:0] _GEN_36 = {{2'd0}, weighted_prod}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 71:59]
  wire [15:0] _weighted_value_sum_reg_T = weighted_value_sum_reg + _GEN_36; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 71:59]
  wire [1:0] _idx_reg_T_1 = idx_reg + 2'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 73:28]
  wire [14:0] _GEN_8 = weight_sum_reg == 11'h0 ? 15'h0 : final_quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 79:38 80:30 29:37]
  wire [2:0] _GEN_9 = weight_sum_reg == 11'h0 ? 3'h4 : 3'h3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 79:38 81:17 84:17]
  wire  _GEN_10 = weight_sum_reg == 11'h0 ? 1'h0 : 1'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 50:19 79:38 83:25]
  wire [14:0] _GEN_11 = divider_valid_out ? divider_quotient : final_quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 88:33 89:30 29:37]
  wire [2:0] _GEN_12 = divider_valid_out ? 3'h4 : state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 88:33 90:17 18:24]
  wire [2:0] _GEN_13 = 3'h4 == state ? 3'h0 : state; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19 94:15 18:24]
  wire [14:0] _GEN_14 = 3'h3 == state ? _GEN_11 : final_quotient_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19 29:37]
  wire [2:0] _GEN_15 = 3'h3 == state ? _GEN_12 : _GEN_13; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
  wire  _GEN_24 = 3'h1 == state ? 1'h0 : 3'h2 == state & _GEN_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 50:19 55:19]
  ScoreAndWeightUnit score_weight_unit ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 32:35]
    .q_vec(score_weight_unit_q_vec),
    .k_vec(score_weight_unit_k_vec),
    .weight(score_weight_unit_weight)
  );
  Divider15by11 divider ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 33:25]
    .clock(divider_clock),
    .reset(divider_reset),
    .start(divider_start),
    .dividend(divider_dividend),
    .divisor(divider_divisor),
    .quotient(divider_quotient),
    .valid_out(divider_valid_out)
  );
  assign done = state == 3'h4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 99:19]
  assign result = final_quotient_reg[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 100:33]
  assign score_weight_unit_q_vec = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 44:29]
  assign score_weight_unit_k_vec = _k_i_T_1[7:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 40:42]
  assign divider_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 36:19]
  assign divider_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 37:19]
  assign divider_start = 3'h0 == state ? 1'h0 : _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 50:19 55:19]
  assign divider_dividend = weighted_value_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 51:22]
  assign divider_divisor = weight_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 52:21]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 18:24]
      state <= 3'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 18:24]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        state <= 3'h1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 64:17]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (idx_reg == 2'h3) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 74:31]
        state <= 3'h2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 75:17]
      end
    end else if (3'h2 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      state <= _GEN_9;
    end else begin
      state <= _GEN_15;
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        q_reg <= q; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 58:17]
      end
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        k_reg <= k; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 59:17]
      end
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        v_reg <= v; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 60:17]
      end
    end
    if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        idx_reg <= 2'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 63:19]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      idx_reg <= _idx_reg_T_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 73:17]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 27:33]
      weight_sum_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 27:33]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        weight_sum_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 61:26]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      weight_sum_reg <= _weight_sum_reg_T[10:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 69:24]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 28:41]
      weighted_value_sum_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 28:41]
    end else if (3'h0 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 57:21]
        weighted_value_sum_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 62:34]
      end
    end else if (3'h1 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      weighted_value_sum_reg <= _weighted_value_sum_reg_T[14:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 71:32]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 29:37]
      final_quotient_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 29:37]
    end else if (!(3'h0 == state)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
      if (!(3'h1 == state)) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
        if (3'h2 == state) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v4_chisel/ThresholdAttention.scala 55:19]
          final_quotient_reg <= _GEN_8;
        end else begin
          final_quotient_reg <= _GEN_14;
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
  idx_reg = _RAND_4[1:0];
  _RAND_5 = {1{`RANDOM}};
  weight_sum_reg = _RAND_5[10:0];
  _RAND_6 = {1{`RANDOM}};
  weighted_value_sum_reg = _RAND_6[14:0];
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
