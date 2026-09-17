module ScoreUnit(
  input        clock, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 4:17]
  input        reset, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 5:17]
  input        valid_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 6:20]
  input  [7:0] q_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 7:16]
  input  [7:0] k_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 8:16]
  output       valid_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 9:21]
  output [8:0] score_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 10:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
`endif // RANDOMIZE_REG_INIT
  wire [3:0] q0 = q_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 13:16]
  wire [3:0] q1 = q_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 14:16]
  wire [3:0] k0 = k_in[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 15:16]
  wire [3:0] k1 = k_in[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 16:16]
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 18:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 19:18]
  wire [8:0] score_comb = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 21:26]
  reg [8:0] score_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 24:64]
  reg  valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 25:64]
  assign valid_out = valid_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 37:13]
  assign score_out = score_out_reg; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 36:13]
  always @(posedge clock) begin
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 24:64]
      score_out_reg <= 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 24:64]
    end else if (valid_in) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 30:20]
      score_out_reg <= score_comb; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 31:21]
    end
    if (reset) begin // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 25:64]
      valid_out_reg <= 1'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 25:64]
    end else begin
      valid_out_reg <= valid_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/ScoreUnit/ScoreUnit.scala 29:19]
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
