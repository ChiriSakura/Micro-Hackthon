module ScoreAndWeightUnit(
  input  [7:0] q_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 5:17]
  input  [7:0] k_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 6:17]
  input  [8:0] threshold, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 7:21]
  output [8:0] weight // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 8:18]
);
  wire [3:0] q0 = q_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 11:17]
  wire [3:0] q1 = q_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 12:17]
  wire [3:0] k0 = k_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 13:17]
  wire [3:0] k1 = k_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 14:17]
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 18:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 19:18]
  wire [8:0] score = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 25:21]
  wire  score_ge_thresh = score >= threshold; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 28:31]
  assign weight = score_ge_thresh ? score : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 33:16]
endmodule
