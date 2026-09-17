module AggregationUnit(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 6:17]
  input         valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 7:20]
  input  [35:0] scores_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 8:21]
  input  [15:0] values_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 9:21]
  output        valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 10:21]
  output [10:0] weight_sum_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 11:26]
  output [14:0] weighted_value_sum_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 12:34]
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
  wire [8:0] scores_0 = scores_in[8:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 17:54]
  wire [8:0] scores_1 = scores_in[17:9]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 17:54]
  wire [8:0] scores_2 = scores_in[26:18]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 17:54]
  wire [8:0] scores_3 = scores_in[35:27]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 17:54]
  wire [3:0] values_0 = values_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 18:54]
  wire [3:0] values_1 = values_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 18:54]
  wire [3:0] values_2 = values_in[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 18:54]
  wire [3:0] values_3 = values_in[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 18:54]
  wire [8:0] weights_0 = scores_0 >= 9'h40 ? scores_0 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_0 = weights_0 * values_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 28:38]
  wire [8:0] weights_1 = scores_1 >= 9'h40 ? scores_1 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_1 = weights_1 * values_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 28:38]
  wire [8:0] weights_2 = scores_2 >= 9'h40 ? scores_2 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_2 = weights_2 * values_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 28:38]
  wire [8:0] weights_3 = scores_3 >= 9'h40 ? scores_3 : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
  wire [12:0] weighted_values_3 = weights_3 * values_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 28:38]
  reg  valid_s1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 32:59]
  reg [8:0] weights_s1_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
  reg [8:0] weights_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
  reg [8:0] weights_s1_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
  reg [8:0] weights_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
  reg [12:0] weighted_values_s1_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
  reg [12:0] weighted_values_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
  reg [12:0] weighted_values_s1_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
  reg [12:0] weighted_values_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
  wire [9:0] weight_sum_s1_01 = weights_s1_0 + weights_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 48:40]
  wire [9:0] weight_sum_s1_23 = weights_s1_2 + weights_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 49:40]
  wire [10:0] weight_sum_comb = weight_sum_s1_01 + weight_sum_s1_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 50:42]
  wire [13:0] weighted_value_sum_s1_01 = weighted_values_s1_0 + weighted_values_s1_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 52:56]
  wire [13:0] weighted_value_sum_s1_23 = weighted_values_s1_2 + weighted_values_s1_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 53:56]
  wire [14:0] weighted_value_sum_comb = weighted_value_sum_s1_01 + weighted_value_sum_s1_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 54:58]
  reg  valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 57:64]
  reg [10:0] weight_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 58:69]
  reg [14:0] weighted_value_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 59:77]
  assign valid_out = valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 71:13]
  assign weight_sum_out = weight_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 72:18]
  assign weighted_value_sum_out = weighted_value_sum_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 73:26]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 32:59]
      valid_s1 <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 32:59]
    end else begin
      valid_s1 <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 38:14]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
      weights_s1_0 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      if (scores_0 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
        weights_s1_0 <= scores_0;
      end else begin
        weights_s1_0 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
      weights_s1_1 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      if (scores_1 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
        weights_s1_1 <= scores_1;
      end else begin
        weights_s1_1 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
      weights_s1_2 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      if (scores_2 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
        weights_s1_2 <= scores_2;
      end else begin
        weights_s1_2 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
      weights_s1_3 <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 33:61]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      if (scores_3 >= 9'h40) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 26:22]
        weights_s1_3 <= scores_3;
      end else begin
        weights_s1_3 <= 9'h0;
      end
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
      weighted_values_s1_0 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      weighted_values_s1_0 <= weighted_values_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
      weighted_values_s1_1 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      weighted_values_s1_1 <= weighted_values_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
      weighted_values_s1_2 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      weighted_values_s1_2 <= weighted_values_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
      weighted_values_s1_3 <= 13'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 34:69]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 39:20]
      weighted_values_s1_3 <= weighted_values_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 41:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 57:64]
      valid_out_reg <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 57:64]
    end else begin
      valid_out_reg <= valid_s1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 63:19]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 58:69]
      weight_sum_out_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 58:69]
    end else if (valid_s1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 64:20]
      weight_sum_out_reg <= weight_sum_comb; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 65:26]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 59:77]
      weighted_value_sum_out_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 59:77]
    end else if (valid_s1) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 64:20]
      weighted_value_sum_out_reg <= weighted_value_sum_comb; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/AggregationUnit/AggregationUnit.scala 66:34]
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
