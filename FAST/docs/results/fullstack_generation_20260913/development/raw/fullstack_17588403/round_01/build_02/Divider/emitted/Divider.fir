FIRRTL version 1.2.0
circuit Divider :
  module Divider :
    input clock : Clock @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 5:17]
    input reset : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 6:17]
    input start : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 7:17]
    input numer_in : UInt<15> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 8:20]
    input denom_in : UInt<11> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 9:20]
    output quotient_out : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 10:24]
    output done : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 11:16]

    reg state_reg : UInt<2>, clock with :
      reset => (reset, UInt<2>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 17:28]
    reg remainder_reg : UInt<15>, clock with :
      reset => (reset, UInt<15>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 18:32]
    reg divisor_reg : UInt<11>, clock with :
      reset => (reset, UInt<11>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 19:30]
    reg quotient_reg : UInt<4>, clock with :
      reset => (reset, UInt<4>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 20:31]
    reg cycle_counter_reg : UInt<3>, clock with :
      reset => (reset, UInt<3>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 21:36]
    done <= UInt<1>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 24:10]
    node _T = eq(UInt<2>("h0"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
    when _T : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      when start : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 29:21]
        remainder_reg <= numer_in @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 30:25]
        divisor_reg <= denom_in @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 31:23]
        quotient_reg <= UInt<1>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 32:24]
        cycle_counter_reg <= UInt<3>("h4") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 33:29]
        state_reg <= UInt<2>("h1") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 34:21]
    else :
      node _T_1 = eq(UInt<2>("h1"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
      when _T_1 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
        node rem_shifted_left = shl(remainder_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 39:46]
        node quot_shifted_left = shl(quotient_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 40:46]
        node rem_msbs = bits(rem_shifted_left, 14, 4) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 43:40]
        node _trial_sub_ext_T = cat(UInt<1>("h0"), rem_msbs) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:32]
        node _trial_sub_ext_T_1 = cat(UInt<1>("h0"), divisor_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:58]
        node _trial_sub_ext_T_2 = sub(_trial_sub_ext_T, _trial_sub_ext_T_1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:53]
        node trial_sub_ext = tail(_trial_sub_ext_T_2, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 46:53]
        node _sub_successful_T = bits(trial_sub_ext, 11, 11) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 47:44]
        node sub_successful = eq(_sub_successful_T, UInt<1>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 47:30]
        when sub_successful : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 49:30]
          node _remainder_reg_T = bits(trial_sub_ext, 10, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 51:45]
          node _remainder_reg_T_1 = bits(rem_shifted_left, 3, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 51:70]
          node _remainder_reg_T_2 = cat(_remainder_reg_T, _remainder_reg_T_1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 51:31]
          remainder_reg <= _remainder_reg_T_2 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 51:25]
        else :
          remainder_reg <= rem_shifted_left @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 54:25]
        node _quotient_reg_T = or(quot_shifted_left, sub_successful) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 57:43]
        quotient_reg <= _quotient_reg_T @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 57:22]
        node _cycle_counter_reg_T = sub(cycle_counter_reg, UInt<1>("h1")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 59:48]
        node _cycle_counter_reg_T_1 = tail(_cycle_counter_reg_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 59:48]
        cycle_counter_reg <= _cycle_counter_reg_T_1 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 59:27]
        node _T_2 = eq(cycle_counter_reg, UInt<1>("h1")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 60:32]
        when _T_2 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 60:41]
          state_reg <= UInt<2>("h2") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 61:21]
      else :
        node _T_3 = eq(UInt<2>("h2"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
        when _T_3 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 27:23]
          done <= UInt<1>("h1") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 66:14]
          state_reg <= UInt<2>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 67:19]
    quotient_out <= quotient_reg @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_02/Divider/Divider.scala 72:18]

