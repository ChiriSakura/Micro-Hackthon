FIRRTL version 1.2.0
circuit Divider :
  module Divider :
    input clock : Clock @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 5:17]
    input reset : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 6:17]
    input start : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 7:17]
    input numer_in : UInt<15> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 8:20]
    input denom_in : UInt<11> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 9:20]
    output quotient_out : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 10:24]
    output done : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 11:16]

    wire state_current : UInt<2> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 17:27]
    wire q_current : UInt<4> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 18:23]
    quotient_out <= q_current @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 21:16]
    node _done_T = eq(state_current, UInt<2>("h3")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 22:25]
    done <= _done_T @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 22:8]
    reg state_reg : UInt<2>, clock with :
      reset => (reset, UInt<2>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 26:28]
    reg p_reg : SInt<12>, clock with :
      reset => (UInt<1>("h0"), p_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 27:20]
    reg a_reg : UInt<15>, clock with :
      reset => (UInt<1>("h0"), a_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 28:20]
    reg d_reg : UInt<11>, clock with :
      reset => (UInt<1>("h0"), d_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 29:20]
    reg q_reg : UInt<4>, clock with :
      reset => (UInt<1>("h0"), q_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 30:20]
    reg cycle_reg : UInt<3>, clock with :
      reset => (UInt<1>("h0"), cycle_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 31:24]
    state_current <= state_reg @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 34:19]
    q_current <= q_reg @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 35:15]
    node _p_shifted_T = bits(p_reg, 10, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 39:27]
    node _p_shifted_T_1 = bits(a_reg, 14, 14) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 39:43]
    node _p_shifted_T_2 = cat(_p_shifted_T, _p_shifted_T_1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 39:35]
    node p_shifted = asSInt(_p_shifted_T_2) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 39:49]
    node a_next = shl(a_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 40:24]
    node d_ext = cvt(d_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 41:23]
    node _p_plus_d_T = add(p_shifted, d_ext) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 43:30]
    node _p_plus_d_T_1 = tail(_p_plus_d_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 43:30]
    node p_plus_d = asSInt(_p_plus_d_T_1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 43:30]
    node _p_minus_d_T = sub(p_shifted, d_ext) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 44:31]
    node _p_minus_d_T_1 = tail(_p_minus_d_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 44:31]
    node p_minus_d = asSInt(_p_minus_d_T_1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 44:31]
    node _p_next_T = bits(p_reg, 11, 11) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 45:27]
    node p_next = mux(_p_next_T, p_plus_d, p_minus_d) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 45:21]
    node _q_bit_T = bits(p_next, 11, 11) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 47:24]
    node q_bit = eq(_q_bit_T, UInt<1>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 47:17]
    node _q_next_T = shl(q_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 48:25]
    node q_next = or(_q_next_T, q_bit) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 48:31]
    node _T = eq(UInt<2>("h0"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
    when _T : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      when start : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 53:21]
        state_reg <= UInt<2>("h1") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 54:21]
    else :
      node _T_1 = eq(UInt<2>("h1"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
      when _T_1 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        state_reg <= UInt<2>("h2") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 58:19]
        p_reg <= asSInt(UInt<1>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 60:15]
        a_reg <= numer_in @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 61:15]
        d_reg <= denom_in @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 62:15]
        q_reg <= UInt<1>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 63:15]
        cycle_reg <= UInt<3>("h4") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 64:19]
      else :
        node _T_2 = eq(UInt<2>("h2"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
        when _T_2 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
          p_reg <= p_next @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 68:15]
          a_reg <= a_next @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 69:15]
          q_reg <= q_next @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 70:15]
          node _cycle_reg_T = sub(cycle_reg, UInt<1>("h1")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 71:32]
          node _cycle_reg_T_1 = tail(_cycle_reg_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 71:32]
          cycle_reg <= _cycle_reg_T_1 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 71:19]
          node _T_3 = eq(cycle_reg, UInt<1>("h1")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 74:24]
          when _T_3 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 74:33]
            state_reg <= UInt<2>("h3") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 75:21]
        else :
          node _T_4 = eq(UInt<2>("h3"), state_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
          when _T_4 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 51:23]
            state_reg <= UInt<2>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17588403/round_01/build_01/Divider/Divider.scala 80:19]


