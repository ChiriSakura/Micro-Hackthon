FIRRTL version 1.2.0
circuit ScoreAndWeight :
  module ScoreAndWeight :
    input q_vec : UInt<8> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 5:17]
    input k_vec : UInt<8> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 6:17]
    output weight : UInt<9> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 7:18]

    node q0 = bits(q_vec, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 11:17]
    node q1 = bits(q_vec, 7, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 12:17]
    node k0 = bits(k_vec, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 15:17]
    node k1 = bits(k_vec, 7, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 16:17]
    node p0 = mul(q0, k0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 19:15]
    node p1 = mul(q1, k1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 20:15]
    node score = add(p0, p1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 25:18]
    node _weight_T = geq(score, UInt<9>("h40")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 32:23]
    node _weight_T_1 = mux(_weight_T, score, UInt<9>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 32:16]
    weight <= _weight_T_1 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590849/round_01/build_01/ScoreAndWeight/ScoreAndWeight.scala 32:10]

