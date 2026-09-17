FIRRTL version 1.2.0
circuit ScoreUnit :
  module ScoreUnit :
    input clock : Clock @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 4:17]
    input reset : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 5:17]
    input valid_in : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 6:20]
    input q_in : UInt<8> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 7:16]
    input k_in : UInt<8> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 8:16]
    output valid_out : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 9:21]
    output score_out : UInt<9> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 10:21]

    node q0 = bits(q_in, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 13:16]
    node q1 = bits(q_in, 7, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 14:16]
    node k0 = bits(k_in, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 15:16]
    node k1 = bits(k_in, 7, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 16:16]
    node prod0 = mul(q0, k0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 19:18]
    node prod1 = mul(q1, k1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 20:18]
    node score_comb = add(prod0, prod1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 24:26]
    reg score_out_reg : UInt<9>, clock with :
      reset => (reset, UInt<9>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 27:64]
    reg valid_out_reg : UInt<1>, clock with :
      reset => (reset, UInt<1>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 28:64]
    valid_out_reg <= valid_in @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 33:19]
    when valid_in : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 36:20]
      score_out_reg <= score_comb @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 37:21]
    score_out <= score_out_reg @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 42:13]
    valid_out <= valid_out_reg @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_02/build_01/ScoreUnit/ScoreUnit.scala 43:13]

