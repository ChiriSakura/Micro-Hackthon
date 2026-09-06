"""定点算术助手：Chisel 在每次窄化赋值上的行为。

这些函数存在的理由是「参照模型必须复现 RTL 的截断，而不是复现我们希望的
算术」。`acc := acc + mul` 会把 bits+1 的和窄化回 bits，所以累加器溢出时
是回绕不是饱和；一个会饱和的参照模型会和**正确的** RTL 不一致。

被 golden/ 下所有数据通路模型引用。
"""

from __future__ import annotations

import torch


def wrap(value: int, bits: int) -> int:
    """Truncate to `bits` and reinterpret as two's complement.

    This is what Chisel does on every width-narrowing `:=`, and modelling it is
    the difference between a reference and a wish: `acc := acc + mul` narrows a
    bits+1 sum back to bits, so an overflowing accumulator wraps rather than
    saturating. A reference that saturated would disagree with correct RTL.
    """
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


def fp_mul(a: int, b: int, bits: int, point: int) -> int:
    """`mul := a * b` where mul, a and b are all FixedPoint(bits.W, point.BP).

    The product carries 2*bits and 2*point, so the assignment first realigns the
    binary point (an arithmetic shift right by `point`, flooring toward -inf)
    and then truncates the width.
    """
    return wrap((a * b) >> point, bits)


def trunc_div(numerator: int, denominator: int) -> int:
    """FIRRTL integer division: truncates toward zero, unlike Python's //."""
    if denominator == 0:
        return 0
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def quantise(values: torch.Tensor, bits: int, point: int) -> torch.Tensor:
    """Round onto the module's fixed-point grid so comparisons are exact.

    Chisel's FixedPoint(bits.W, point.BP) is a two's-complement integer scaled by
    2^-point, so the reference must live on that same grid or every comparison
    would be a floating-point near-miss.
    """
    scale = float(1 << point)
    limit = float(1 << (bits - 1))
    ticks = torch.round(values * scale).clamp(-limit, limit - 1)
    return ticks / scale
