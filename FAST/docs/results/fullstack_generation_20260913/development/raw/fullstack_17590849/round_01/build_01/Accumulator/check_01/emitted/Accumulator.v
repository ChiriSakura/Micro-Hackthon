module Accumulator(
  input         clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 5:17]
  input         reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 6:17]
  input         in_valid, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 7:20]
  input  [35:0] weights, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 8:19]
  input  [15:0] values, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 9:18]
  output        out_valid, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 10:21]
  output [10:0] weight_sum, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 11:22]
  output [14:0] weighted_value_sum // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 12:30]
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
  wire [8:0] w_vec_0 = weights[8:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 23:26]
  wire [3:0] v_vec_0 = values[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 24:25]
  wire [8:0] w_vec_1 = weights[17:9]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 23:26]
  wire [3:0] v_vec_1 = values[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 24:25]
  wire [8:0] w_vec_2 = weights[26:18]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 23:26]
  wire [3:0] v_vec_2 = values[11:8]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 24:25]
  wire [8:0] w_vec_3 = weights[35:27]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 23:26]
  wire [3:0] v_vec_3 = values[15:12]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 24:25]
  wire [12:0] products_0 = w_vec_0 * v_vec_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 31:31]
  wire [12:0] products_1 = w_vec_1 * v_vec_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 31:31]
  wire [12:0] products_2 = w_vec_2 * v_vec_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 31:31]
  wire [12:0] products_3 = w_vec_3 * v_vec_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 31:31]
  reg  stage2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 36:31]
  reg [8:0] stage2_weights_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 37:29]
  reg [8:0] stage2_weights_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 37:29]
  reg [8:0] stage2_weights_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 37:29]
  reg [8:0] stage2_weights_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 37:29]
  reg [12:0] stage2_products_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 38:30]
  reg [12:0] stage2_products_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 38:30]
  reg [12:0] stage2_products_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 38:30]
  reg [12:0] stage2_products_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 38:30]
  wire [9:0] w_sum_01 = stage2_weights_0 + stage2_weights_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 50:38]
  wire [9:0] w_sum_23 = stage2_weights_2 + stage2_weights_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 51:38]
  wire [10:0] total_w_sum = w_sum_01 + w_sum_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 52:32]
  wire [13:0] wv_sum_01 = stage2_products_0 + stage2_products_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 55:40]
  wire [13:0] wv_sum_23 = stage2_products_2 + stage2_products_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 56:40]
  wire [14:0] total_wv_sum = wv_sum_01 + wv_sum_23; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 57:34]
  reg  out_valid_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 61:32]
  reg [10:0] weight_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 62:33]
  reg [14:0] weighted_value_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 63:41]
  assign out_valid = out_valid_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 72:15]
  assign weight_sum = weight_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 73:16]
  assign weighted_value_sum = weighted_value_sum_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 74:24]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 36:31]
      stage2_valid <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 36:31]
    end else begin
      stage2_valid <= in_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 36:31]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_weights_0 <= w_vec_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 42:22]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_weights_1 <= w_vec_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 42:22]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_weights_2 <= w_vec_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 42:22]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_weights_3 <= w_vec_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 42:22]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_products_0 <= products_0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 43:23]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_products_1 <= products_1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 43:23]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_products_2 <= products_2; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 43:23]
    end
    if (in_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 41:20]
      stage2_products_3 <= products_3; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 43:23]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 61:32]
      out_valid_reg <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 61:32]
    end else begin
      out_valid_reg <= stage2_valid; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 61:32]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 62:33]
      weight_sum_reg <= 11'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 62:33]
    end else if (stage2_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 66:24]
      weight_sum_reg <= total_w_sum; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 67:22]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 63:41]
      weighted_value_sum_reg <= 15'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 63:41]
    end else if (stage2_valid) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 66:24]
      weighted_value_sum_reg <= total_wv_sum; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/Accumulator/Accumulator.scala 68:30]
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
  stage2_valid = _RAND_0[0:0];
  _RAND_1 = {1{`RANDOM}};
  stage2_weights_0 = _RAND_1[8:0];
  _RAND_2 = {1{`RANDOM}};
  stage2_weights_1 = _RAND_2[8:0];
  _RAND_3 = {1{`RANDOM}};
  stage2_weights_2 = _RAND_3[8:0];
  _RAND_4 = {1{`RANDOM}};
  stage2_weights_3 = _RAND_4[8:0];
  _RAND_5 = {1{`RANDOM}};
  stage2_products_0 = _RAND_5[12:0];
  _RAND_6 = {1{`RANDOM}};
  stage2_products_1 = _RAND_6[12:0];
  _RAND_7 = {1{`RANDOM}};
  stage2_products_2 = _RAND_7[12:0];
  _RAND_8 = {1{`RANDOM}};
  stage2_products_3 = _RAND_8[12:0];
  _RAND_9 = {1{`RANDOM}};
  out_valid_reg = _RAND_9[0:0];
  _RAND_10 = {1{`RANDOM}};
  weight_sum_reg = _RAND_10[10:0];
  _RAND_11 = {1{`RANDOM}};
  weighted_value_sum_reg = _RAND_11[14:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
