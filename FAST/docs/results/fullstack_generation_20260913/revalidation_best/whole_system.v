module ScoreUnit(
  input        clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 4:17]
  input        reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 5:17]
  input        valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 6:20]
  input  [7:0] q_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 7:16]
  input  [7:0] k_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 8:16]
  output       valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 9:21]
  output [8:0] score_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 10:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
`endif // RANDOMIZE_REG_INIT
  wire [3:0] q0 = q_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 13:16]
  wire [3:0] q1 = q_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 14:16]
  wire [3:0] k0 = k_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 15:16]
  wire [3:0] k1 = k_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 16:16]
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 19:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 20:18]
  wire [8:0] score_comb = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 24:26]
  reg [8:0] score_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 27:64]
  reg  valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 28:64]
  assign valid_out = valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 43:13]
  assign score_out = score_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 42:13]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 27:64]
      score_out_reg <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 27:64]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 36:20]
      score_out_reg <= score_comb; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 37:21]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 28:64]
      valid_out_reg <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 28:64]
    end else begin
      valid_out_reg <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ScoreUnit.scala 33:19]
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
  score_out_reg = _RAND_0[8:0];
  _RAND_1 = {1{`RANDOM}};
  valid_out_reg = _RAND_1[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
module AggregationUnit(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 6:17]
  input         valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 7:20]
  input  [35:0] scores_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 8:21]
  input  [15:0] values_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 9:21]
  output        valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 10:21]
  output [10:0] weight_sum_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 11:26]
  output [14:0] weighted_value_sum_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 12:34]
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
`endif // RANDOMIZE_REG_INIT
  wire [8:0] scores_0 = scores_in[8:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 17:54]
  wire [8:0] scores_1 = scores_in[17:9]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 17:54]
  wire [8:0] scores_2 = scores_in[26:18]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 17:54]
  wire [8:0] scores_3 = scores_in[35:27]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 17:54]
  wire [3:0] values_0 = values_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 18:54]
  wire [3:0] values_1 = values_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 18:54]
  wire [3:0] values_2 = values_in[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 18:54]
  wire [3:0] values_3 = values_in[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 18:54]
  wire [8:0] weights_0 = scores_0 >= 9'h40 ? scores_0 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_0 = weights_0 * values_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 28:38]
  wire [8:0] weights_1 = scores_1 >= 9'h40 ? scores_1 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_1 = weights_1 * values_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 28:38]
  wire [8:0] weights_2 = scores_2 >= 9'h40 ? scores_2 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_2 = weights_2 * values_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 28:38]
  wire [8:0] weights_3 = scores_3 >= 9'h40 ? scores_3 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_3 = weights_3 * values_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 28:38]
  reg  valid_s1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 32:59]
  reg [8:0] weights_s1_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
  reg [8:0] weights_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
  reg [8:0] weights_s1_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
  reg [8:0] weights_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
  reg [12:0] weighted_values_s1_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
  reg [12:0] weighted_values_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
  reg [12:0] weighted_values_s1_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
  reg [12:0] weighted_values_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
  wire [9:0] weight_sum_s1_01 = weights_s1_0 + weights_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 49:40]
  wire [9:0] weight_sum_s1_23 = weights_s1_2 + weights_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 50:40]
  wire [10:0] weight_sum_comb = weight_sum_s1_01 + weight_sum_s1_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 51:42]
  wire [13:0] weighted_value_sum_s1_01 = weighted_values_s1_0 + weighted_values_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 54:56]
  wire [13:0] weighted_value_sum_s1_23 = weighted_values_s1_2 + weighted_values_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 55:56]
  wire [14:0] weighted_value_sum_comb = weighted_value_sum_s1_01 + weighted_value_sum_s1_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 56:58]
  reg  valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 59:64]
  reg [10:0] weight_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 60:69]
  reg [14:0] weighted_value_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 61:77]
  assign valid_out = valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 73:13]
  assign weight_sum_out = weight_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 74:18]
  assign weighted_value_sum_out = weighted_value_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 75:26]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 32:59]
      valid_s1 <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 32:59]
    end else begin
      valid_s1 <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 38:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
      weights_s1_0 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      if (scores_0 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
        weights_s1_0 <= scores_0;
      end else begin
        weights_s1_0 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
      weights_s1_1 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      if (scores_1 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
        weights_s1_1 <= scores_1;
      end else begin
        weights_s1_1 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
      weights_s1_2 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      if (scores_2 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
        weights_s1_2 <= scores_2;
      end else begin
        weights_s1_2 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
      weights_s1_3 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      if (scores_3 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 26:22]
        weights_s1_3 <= scores_3;
      end else begin
        weights_s1_3 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
      weighted_values_s1_0 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      weighted_values_s1_0 <= weighted_values_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
      weighted_values_s1_1 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      weighted_values_s1_1 <= weighted_values_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
      weighted_values_s1_2 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      weighted_values_s1_2 <= weighted_values_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
      weighted_values_s1_3 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 39:20]
      weighted_values_s1_3 <= weighted_values_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 59:64]
      valid_out_reg <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 59:64]
    end else begin
      valid_out_reg <= valid_s1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 65:19]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 60:69]
      weight_sum_out_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 60:69]
    end else if (valid_s1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 66:20]
      weight_sum_out_reg <= weight_sum_comb; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 67:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 61:77]
      weighted_value_sum_out_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 61:77]
    end else if (valid_s1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 66:20]
      weighted_value_sum_out_reg <= weighted_value_sum_comb; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/AggregationUnit.scala 68:34]
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
  valid_s1 = _RAND_0[0:0];
  _RAND_1 = {1{`RANDOM}};
  weights_s1_0 = _RAND_1[8:0];
  _RAND_2 = {1{`RANDOM}};
  weights_s1_1 = _RAND_2[8:0];
  _RAND_3 = {1{`RANDOM}};
  weights_s1_2 = _RAND_3[8:0];
  _RAND_4 = {1{`RANDOM}};
  weights_s1_3 = _RAND_4[8:0];
  _RAND_5 = {1{`RANDOM}};
  weighted_values_s1_0 = _RAND_5[12:0];
  _RAND_6 = {1{`RANDOM}};
  weighted_values_s1_1 = _RAND_6[12:0];
  _RAND_7 = {1{`RANDOM}};
  weighted_values_s1_2 = _RAND_7[12:0];
  _RAND_8 = {1{`RANDOM}};
  weighted_values_s1_3 = _RAND_8[12:0];
  _RAND_9 = {1{`RANDOM}};
  valid_out_reg = _RAND_9[0:0];
  _RAND_10 = {1{`RANDOM}};
  weight_sum_out_reg = _RAND_10[10:0];
  _RAND_11 = {1{`RANDOM}};
  weighted_value_sum_out_reg = _RAND_11[14:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
module UnsignedDivider(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 6:17]
  input         valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 7:20]
  input  [14:0] numerator_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 8:24]
  input  [10:0] denominator_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 9:26]
  output        valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 10:21]
  output [3:0]  quotient_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 11:24]
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
  wire  initial_state_divideByZero = denominator_in == 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 71:49]
  wire [11:0] shifted_rem = {11'h0,numerator_in[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_0 = {{1'd0}, denominator_in}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire  can_subtract = shifted_rem >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_1 = shifted_rem - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem = can_subtract ? _next_rem_T_1 : shifted_rem; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_quotient = {14'h0,can_subtract}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_dividend = {numerator_in[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_1 = {next_rem[10:0],next_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_1 = shifted_rem_1 >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_3 = shifted_rem_1 - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_1 = can_subtract_1 ? _next_rem_T_3 : shifted_rem_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_1_quotient = {next_quotient[13:0],can_subtract_1}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_1_dividend = {next_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_2 = {next_rem_1[10:0],next_1_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_2 = shifted_rem_2 >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_5 = shifted_rem_2 - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_2 = can_subtract_2 ? _next_rem_T_5 : shifted_rem_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_2_quotient = {next_1_quotient[13:0],can_subtract_2}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_2_dividend = {next_1_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_3 = {next_rem_2[10:0],next_2_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_3 = shifted_rem_3 >= _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_7 = shifted_rem_3 - _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [14:0] next_3_quotient = {next_2_quotient[13:0],can_subtract_3}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_3_dividend = {next_2_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  reg [11:0] REG_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [14:0] REG_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [14:0] REG_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [10:0] REG_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  wire [11:0] shifted_rem_4 = {REG_remainder[10:0],REG_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_8 = {{1'd0}, REG_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire  can_subtract_4 = shifted_rem_4 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_9 = shifted_rem_4 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_4 = can_subtract_4 ? _next_rem_T_9 : shifted_rem_4; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_4_quotient = {REG_quotient[13:0],can_subtract_4}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_4_dividend = {REG_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_5 = {next_rem_4[10:0],next_4_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_5 = shifted_rem_5 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_11 = shifted_rem_5 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_5 = can_subtract_5 ? _next_rem_T_11 : shifted_rem_5; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_5_quotient = {next_4_quotient[13:0],can_subtract_5}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_5_dividend = {next_4_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_6 = {next_rem_5[10:0],next_5_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_6 = shifted_rem_6 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_13 = shifted_rem_6 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_6 = can_subtract_6 ? _next_rem_T_13 : shifted_rem_6; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_6_quotient = {next_5_quotient[13:0],can_subtract_6}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_6_dividend = {next_5_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_7 = {next_rem_6[10:0],next_6_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_7 = shifted_rem_7 >= _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_15 = shifted_rem_7 - _GEN_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [14:0] next_7_quotient = {next_6_quotient[13:0],can_subtract_7}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_7_dividend = {next_6_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  reg [11:0] REG_1_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [14:0] REG_1_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [14:0] REG_1_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [10:0] REG_1_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_1_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_1_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  wire [11:0] shifted_rem_8 = {REG_1_remainder[10:0],REG_1_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_16 = {{1'd0}, REG_1_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire  can_subtract_8 = shifted_rem_8 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_17 = shifted_rem_8 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_8 = can_subtract_8 ? _next_rem_T_17 : shifted_rem_8; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_8_quotient = {REG_1_quotient[13:0],can_subtract_8}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_8_dividend = {REG_1_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_9 = {next_rem_8[10:0],next_8_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_9 = shifted_rem_9 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_19 = shifted_rem_9 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_9 = can_subtract_9 ? _next_rem_T_19 : shifted_rem_9; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_9_quotient = {next_8_quotient[13:0],can_subtract_9}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_9_dividend = {next_8_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_10 = {next_rem_9[10:0],next_9_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_10 = shifted_rem_10 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_21 = shifted_rem_10 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_10 = can_subtract_10 ? _next_rem_T_21 : shifted_rem_10; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_10_quotient = {next_9_quotient[13:0],can_subtract_10}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_10_dividend = {next_9_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_11 = {next_rem_10[10:0],next_10_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_11 = shifted_rem_11 >= _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_23 = shifted_rem_11 - _GEN_16; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [14:0] next_11_quotient = {next_10_quotient[13:0],can_subtract_11}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_11_dividend = {next_10_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  reg [11:0] REG_2_remainder; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [14:0] REG_2_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [14:0] REG_2_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg [10:0] REG_2_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_2_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  wire [11:0] shifted_rem_12 = {REG_2_remainder[10:0],REG_2_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire [11:0] _GEN_24 = {{1'd0}, REG_2_divisor}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire  can_subtract_12 = shifted_rem_12 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_25 = shifted_rem_12 - _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_12 = can_subtract_12 ? _next_rem_T_25 : shifted_rem_12; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_12_quotient = {REG_2_quotient[13:0],can_subtract_12}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_12_dividend = {REG_2_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_13 = {next_rem_12[10:0],next_12_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_13 = shifted_rem_13 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [11:0] _next_rem_T_27 = shifted_rem_13 - _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:50]
  wire [11:0] next_rem_13 = can_subtract_13 ? _next_rem_T_27 : shifted_rem_13; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
  wire [14:0] next_13_quotient = {next_12_quotient[13:0],can_subtract_13}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  wire [14:0] next_13_dividend = {next_12_dividend[13:0],1'h0}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 53:25]
  wire [11:0] shifted_rem_14 = {next_rem_13[10:0],next_13_dividend[14]}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 43:26]
  wire  can_subtract_14 = shifted_rem_14 >= _GEN_24; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 46:36]
  wire [14:0] next_14_quotient = {next_13_quotient[13:0],can_subtract_14}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 52:25]
  reg [14:0] REG_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_3_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  reg  REG_3_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
  wire [14:0] full_quotient = REG_3_divideByZero ? 15'h0 : REG_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 97:26]
  assign valid_out = REG_3_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 100:13]
  assign quotient_out = full_quotient[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 102:32]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else if (can_subtract_3) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
      REG_remainder <= _next_rem_T_7;
    end else begin
      REG_remainder <= shifted_rem_3;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_quotient <= next_3_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_dividend <= next_3_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_divisor <= denominator_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_divideByZero <= initial_state_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_valid <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_1_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else if (can_subtract_7) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
      REG_1_remainder <= _next_rem_T_15;
    end else begin
      REG_1_remainder <= shifted_rem_7;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_1_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_quotient <= next_7_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_1_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_dividend <= next_7_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_1_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_divisor <= REG_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_1_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_divideByZero <= REG_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_1_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_1_valid <= REG_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_2_remainder <= 12'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else if (can_subtract_11) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 47:23]
      REG_2_remainder <= _next_rem_T_23;
    end else begin
      REG_2_remainder <= shifted_rem_11;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_2_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_quotient <= next_11_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_2_dividend <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_dividend <= next_11_dividend; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_2_divisor <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_divisor <= REG_1_divisor; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_2_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_divideByZero <= REG_1_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_2_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_2_valid <= REG_1_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_3_quotient <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_3_quotient <= next_14_quotient; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_3_divideByZero <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_3_divideByZero <= REG_2_divideByZero; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
      REG_3_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
    end else begin
      REG_3_valid <= REG_2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/UnsignedDivider.scala 89:14]
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
module ThresholdAttention(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 6:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 7:17]
  input         start, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 8:17]
  input  [7:0]  q, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 9:13]
  input  [31:0] k, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 10:13]
  input  [15:0] v, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 11:13]
  output        done, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 12:16]
  output [3:0]  result // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 13:18]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
`endif // RANDOMIZE_REG_INIT
  wire  score_units_0_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_0_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_0_valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_0_q_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_0_k_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_0_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [8:0] score_units_0_score_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_1_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_1_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_1_valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_1_q_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_1_k_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_1_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [8:0] score_units_1_score_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_2_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_2_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_2_valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_2_q_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_2_k_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_2_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [8:0] score_units_2_score_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_3_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_3_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_3_valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_3_q_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [7:0] score_units_3_k_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  score_units_3_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire [8:0] score_units_3_score_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
  wire  agg_unit_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire  agg_unit_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire  agg_unit_valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire [35:0] agg_unit_scores_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire [15:0] agg_unit_values_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire  agg_unit_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire [10:0] agg_unit_weight_sum_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire [14:0] agg_unit_weighted_value_sum_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
  wire  div_unit_clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  wire  div_unit_reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  wire  div_unit_valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  wire [14:0] div_unit_numerator_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  wire [10:0] div_unit_denominator_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  wire  div_unit_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  wire [3:0] div_unit_quotient_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
  reg  busy; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 21:55]
  reg [7:0] q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 22:56]
  reg [31:0] k_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 23:56]
  reg [15:0] v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 24:56]
  wire  can_start = ~busy; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 27:19]
  wire  will_start = can_start & start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 28:30]
  reg  pipeline_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 32:65]
  wire  _GEN_0 = div_unit_valid_out ? 1'h0 : busy; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 41:37 43:12 21:55]
  wire  _GEN_1 = will_start | _GEN_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 36:22 37:12]
  wire [17:0] scores_cat_lo = {score_units_1_score_out,score_units_0_score_out}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 62:23]
  wire [17:0] scores_cat_hi = {score_units_3_score_out,score_units_2_score_out}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 62:23]
  ScoreUnit score_units_0 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
    .clock(score_units_0_clock),
    .reset(score_units_0_reset),
    .valid_in(score_units_0_valid_in),
    .q_in(score_units_0_q_in),
    .k_in(score_units_0_k_in),
    .valid_out(score_units_0_valid_out),
    .score_out(score_units_0_score_out)
  );
  ScoreUnit score_units_1 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
    .clock(score_units_1_clock),
    .reset(score_units_1_reset),
    .valid_in(score_units_1_valid_in),
    .q_in(score_units_1_q_in),
    .k_in(score_units_1_k_in),
    .valid_out(score_units_1_valid_out),
    .score_out(score_units_1_score_out)
  );
  ScoreUnit score_units_2 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
    .clock(score_units_2_clock),
    .reset(score_units_2_reset),
    .valid_in(score_units_2_valid_in),
    .q_in(score_units_2_q_in),
    .k_in(score_units_2_k_in),
    .valid_out(score_units_2_valid_out),
    .score_out(score_units_2_score_out)
  );
  ScoreUnit score_units_3 ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 16:39]
    .clock(score_units_3_clock),
    .reset(score_units_3_reset),
    .valid_in(score_units_3_valid_in),
    .q_in(score_units_3_q_in),
    .k_in(score_units_3_k_in),
    .valid_out(score_units_3_valid_out),
    .score_out(score_units_3_score_out)
  );
  AggregationUnit agg_unit ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 17:24]
    .clock(agg_unit_clock),
    .reset(agg_unit_reset),
    .valid_in(agg_unit_valid_in),
    .scores_in(agg_unit_scores_in),
    .values_in(agg_unit_values_in),
    .valid_out(agg_unit_valid_out),
    .weight_sum_out(agg_unit_weight_sum_out),
    .weighted_value_sum_out(agg_unit_weighted_value_sum_out)
  );
  UnsignedDivider div_unit ( // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 18:24]
    .clock(div_unit_clock),
    .reset(div_unit_reset),
    .valid_in(div_unit_valid_in),
    .numerator_in(div_unit_numerator_in),
    .denominator_in(div_unit_denominator_in),
    .valid_out(div_unit_valid_out),
    .quotient_out(div_unit_quotient_out)
  );
  assign done = div_unit_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 84:8]
  assign result = div_unit_quotient_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 86:10]
  assign score_units_0_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 49:26]
  assign score_units_0_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 50:26]
  assign score_units_0_valid_in = pipeline_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 51:29]
  assign score_units_0_q_in = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 52:25]
  assign score_units_0_k_in = k_reg[7:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 54:33]
  assign score_units_1_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 49:26]
  assign score_units_1_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 50:26]
  assign score_units_1_valid_in = pipeline_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 51:29]
  assign score_units_1_q_in = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 52:25]
  assign score_units_1_k_in = k_reg[15:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 54:33]
  assign score_units_2_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 49:26]
  assign score_units_2_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 50:26]
  assign score_units_2_valid_in = pipeline_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 51:29]
  assign score_units_2_q_in = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 52:25]
  assign score_units_2_k_in = k_reg[23:16]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 54:33]
  assign score_units_3_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 49:26]
  assign score_units_3_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 50:26]
  assign score_units_3_valid_in = pipeline_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 51:29]
  assign score_units_3_q_in = q_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 52:25]
  assign score_units_3_k_in = k_reg[31:24]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 54:33]
  assign agg_unit_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 69:18]
  assign agg_unit_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 70:18]
  assign agg_unit_valid_in = score_units_0_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 71:21]
  assign agg_unit_scores_in = {scores_cat_hi,scores_cat_lo}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 62:23]
  assign agg_unit_values_in = v_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 73:22]
  assign div_unit_clock = clock; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 76:18]
  assign div_unit_reset = reset; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 77:18]
  assign div_unit_valid_in = agg_unit_valid_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 78:21]
  assign div_unit_numerator_in = agg_unit_weighted_value_sum_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 79:25]
  assign div_unit_denominator_in = agg_unit_weight_sum_out; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 80:27]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 21:55]
      busy <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 21:55]
    end else begin
      busy <= _GEN_1;
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 22:56]
      q_reg <= 8'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 22:56]
    end else if (will_start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 36:22]
      q_reg <= q; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 38:13]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 23:56]
      k_reg <= 32'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 23:56]
    end else if (will_start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 36:22]
      k_reg <= k; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 39:13]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 24:56]
      v_reg <= 16'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 24:56]
    end else if (will_start) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 36:22]
      v_reg <= v; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 40:13]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 32:65]
      pipeline_start <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 32:65]
    end else begin
      pipeline_start <= will_start; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_revalidation_v6_best/ThresholdAttention.scala 32:65]
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
  busy = _RAND_0[0:0];
  _RAND_1 = {1{`RANDOM}};
  q_reg = _RAND_1[7:0];
  _RAND_2 = {1{`RANDOM}};
  k_reg = _RAND_2[31:0];
  _RAND_3 = {1{`RANDOM}};
  v_reg = _RAND_3[15:0];
  _RAND_4 = {1{`RANDOM}};
  pipeline_start = _RAND_4[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
