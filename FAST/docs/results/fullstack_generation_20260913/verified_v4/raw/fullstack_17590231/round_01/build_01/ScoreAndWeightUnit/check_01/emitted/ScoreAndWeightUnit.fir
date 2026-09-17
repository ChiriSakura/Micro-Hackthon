FIRRTL version 1.2.0
circuit ScoreAndWeightUnit :
  module ScoreAndWeightUnit :
    input q_vec : UInt<8> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 5:17]
    input k_vec : UInt<8> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 6:17]
    input threshold : UInt<9> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 7:21]
    output weight : UInt<9> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 8:18]

    node q0 = bits(q_vec, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 11:17]
    node q1 = bits(q_vec, 7, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 12:17]
    node k0 = bits(k_vec, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 13:17]
    node k1 = bits(k_vec, 7, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 14:17]
    node prod0 = mul(q0, k0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 18:18]
    node prod1 = mul(q1, k1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 19:18]
    node score = add(prod0, prod1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 25:21]
    node score_ge_thresh = geq(score, threshold) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 28:31]
    node _weight_T = mux(score_ge_thresh, score, UInt<9>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 33:16]
    weight <= _weight_T @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/ScoreAndWeightUnit/ScoreAndWeightUnit.scala 33:10]

