module ProcessingElement(
  input  [3:0]  q0, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 5:14]
  input  [3:0]  q1, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 6:14]
  input  [3:0]  k0, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 7:14]
  input  [3:0]  k1, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 8:14]
  input  [3:0]  v_in, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 9:16]
  output [8:0]  weight_out, // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 10:22]
  output [12:0] weighted_v_out // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 11:26]
);
  wire [7:0] prod0 = q0 * k0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 15:18]
  wire [7:0] prod1 = q1 * k1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 16:18]
  wire [7:0] score = prod0 + prod1; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 18:21]
  wire [8:0] _GEN_0 = {{1'd0}, score}; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:26]
  wire [8:0] weight = _GEN_0 >= 9'h40 ? {{1'd0}, score} : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:19]
  assign weight_out = _GEN_0 >= 9'h40 ? {{1'd0}, score} : 9'h0; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:19]
  assign weighted_v_out = weight * v_in; // @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 27:27]
endmodule
