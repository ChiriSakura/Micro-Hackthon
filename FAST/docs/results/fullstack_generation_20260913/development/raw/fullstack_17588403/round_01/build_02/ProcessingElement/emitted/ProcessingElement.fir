FIRRTL version 1.2.0
circuit ProcessingElement :
  module ProcessingElement :
    input q0 : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 5:14]
    input q1 : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 6:14]
    input k0 : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 7:14]
    input k1 : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 8:14]
    input v_in : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 9:16]
    output weight_out : UInt<9> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 10:22]
    output weighted_v_out : UInt<13> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 11:26]

    node prod0 = mul(q0, k0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 15:18]
    node prod1 = mul(q1, k1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 16:18]
    node _score_T = add(prod0, prod1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 18:21]
    node score = tail(_score_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 18:21]
    node _weight_T = geq(score, UInt<9>("h40")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:26]
    node weight = mux(_weight_T, score, UInt<9>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 23:19]
    node weighted_v = mul(weight, v_in) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 27:27]
    weight_out <= weight @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 30:14]
    weighted_v_out <= weighted_v @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/ProcessingElement/ProcessingElement.scala 31:18]

