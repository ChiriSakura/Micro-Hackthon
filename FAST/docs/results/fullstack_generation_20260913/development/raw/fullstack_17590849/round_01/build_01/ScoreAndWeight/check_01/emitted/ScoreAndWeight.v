module ScoreAndWeight(
  input  [7:0] q_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 5:17]
  input  [7:0] k_vec, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 6:17]
  output [8:0] weight // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 7:18]
);
  wire [3:0] q0 = q_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 11:17]
  wire [3:0] q1 = q_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 12:17]
  wire [3:0] k0 = k_vec[3:0]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 15:17]
  wire [3:0] k1 = k_vec[7:4]; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 16:17]
  wire [7:0] p0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 19:15]
  wire [7:0] p1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 20:15]
  wire [8:0] score = p0 + p1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 25:18]
  assign weight = score >= 9'h40 ? score : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 32:16]
endmodule
