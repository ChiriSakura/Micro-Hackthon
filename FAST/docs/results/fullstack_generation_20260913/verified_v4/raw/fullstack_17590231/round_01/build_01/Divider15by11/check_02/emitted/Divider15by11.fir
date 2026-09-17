FIRRTL version 1.2.0
circuit Divider15by11 :
  module Divider15by11 :
    input clock : Clock @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 5:17]
    input reset : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 6:17]
    input start : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 7:17]
    input dividend : UInt<15> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 8:20]
    input divisor : UInt<11> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 9:19]
    output quotient : UInt<15> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 10:20]
    output valid_out : UInt<1> @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 11:21]

    reg state : UInt<2>, clock with :
      reset => (reset, UInt<2>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 16:24]
    reg dividend_reg : UInt<15>, clock with :
      reset => (reset, UInt<15>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 19:31]
    reg divisor_reg : UInt<11>, clock with :
      reset => (reset, UInt<11>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 20:30]
    reg rem_reg : UInt<11>, clock with :
      reset => (reset, UInt<11>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 21:26]
    reg quotient_reg : UInt<15>, clock with :
      reset => (reset, UInt<15>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 22:31]
    reg count_reg : UInt<4>, clock with :
      reset => (reset, UInt<4>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 23:28]
    node _T = eq(UInt<2>("h0"), state) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
    when _T : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      when start : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 28:21]
        dividend_reg <= dividend @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 29:24]
        divisor_reg <= divisor @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 30:23]
        rem_reg <= UInt<1>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 31:19]
        quotient_reg <= UInt<1>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 32:24]
        count_reg <= UInt<4>("he") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 33:21]
        state <= UInt<2>("h1") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 34:17]
    else :
      node _T_1 = eq(UInt<2>("h1"), state) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
      when _T_1 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
        node _next_rem_val_T = shl(rem_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 39:37]
        node _next_rem_val_T_1 = bits(dividend_reg, 14, 14) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 39:57]
        node next_rem_val = or(_next_rem_val_T, _next_rem_val_T_1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 39:43]
        node _dividend_reg_T = shl(dividend_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 42:38]
        dividend_reg <= _dividend_reg_T @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 42:22]
        node _T_2 = geq(next_rem_val, divisor_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 45:27]
        when _T_2 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 45:43]
          node _rem_reg_T = sub(next_rem_val, divisor_reg) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 47:35]
          node _rem_reg_T_1 = tail(_rem_reg_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 47:35]
          rem_reg <= _rem_reg_T_1 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 47:19]
          node _quotient_reg_T = shl(quotient_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 48:41]
          node _quotient_reg_T_1 = or(_quotient_reg_T, UInt<1>("h1")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 48:47]
          quotient_reg <= _quotient_reg_T_1 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 48:24]
        else :
          node _rem_reg_T_2 = bits(next_rem_val, 10, 0) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 51:34]
          rem_reg <= _rem_reg_T_2 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 51:19]
          node _quotient_reg_T_2 = shl(quotient_reg, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 52:40]
          quotient_reg <= _quotient_reg_T_2 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 52:24]
        node _count_reg_T = sub(count_reg, UInt<1>("h1")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 56:32]
        node _count_reg_T_1 = tail(_count_reg_T, 1) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 56:32]
        count_reg <= _count_reg_T_1 @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 56:19]
        node _T_3 = eq(count_reg, UInt<1>("h0")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 57:24]
        when _T_3 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 57:33]
          state <= UInt<2>("h2") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 58:17]
      else :
        node _T_4 = eq(UInt<2>("h2"), state) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
        when _T_4 : @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 26:19]
          state <= UInt<2>("h0") @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 62:15]
    quotient <= quotient_reg @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 67:14]
    node _valid_out_T = eq(state, UInt<2>("h2")) @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 68:24]
    valid_out <= _valid_out_T @[scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17590231/round_01/build_01/Divider15by11/Divider15by11.scala 68:15]

