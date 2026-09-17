"""指数单元的参照模型。

`ExpUnitFixPoint` 是 FAST 补写的模块（DynaX 不发布它，但 5/8 个源文件
import 它），所以这里的参照是**数据通路规格的 bit-exact 镜像**，不是
`math.exp`：用容差比对真实指数会把错误的 LUT 项藏进容差里。
这个单元离 `math.exp` 有多远是另一个问题，答案写在
`chisel/src/main/scala/exp_unit/exp_unit.scala` 的文件头。
"""

from __future__ import annotations

import torch

from golden.fixedpoint import wrap

# log2(e). The unit computes e^x as 2^(x*log2 e), so this constant is what turns
# the exponential into a shift plus a small table.
LOG2E = 1.4426950408889634


def exp_unit_reference(x_ticks: int, bits: int, point: int, frac: int, guard: int) -> int:
    """Bit-exact mirror of ExpUnitFixPoint's integer datapath.

    Deliberately not math.exp: the module is a shift-and-LUT approximation, so a
    tolerance-based check would hide a wrong LUT entry or an off-by-one shift
    inside the tolerance. Accuracy against the true exponential is a separate
    question, answered in exp_unit.scala's header; this function answers
    "does the Verilog implement the datapath we specified".
    """
    shift_hi, shift_lo = bits - point - 1, -(point + 1)
    scaled = round(LOG2E * (1 << (frac + guard)))
    guarded = (x_ticks * scaled) >> point
    k = (guarded + (1 << (guard - 1))) >> guard
    ki, kf = k >> frac, k & ((1 << frac) - 1)
    mantissa = round(2.0 ** (kf / (1 << frac)) * (1 << point))
    if ki > shift_hi:
        return (1 << (bits - 1)) - 1
    return ((mantissa << bits) >> (bits - max(ki, shift_lo))) & ((1 << bits) - 1)


def exp_cases(bits: int, point: int, frac: int, guard: int, seed: int) -> list[dict]:
    """Inputs chosen to hit every branch of the datapath, not just typical ones."""
    scale = 1 << point
    limit = 1 << (bits - 1)
    named: list[tuple[str, list[int]]] = [
        # exp(0) = 1 exactly; the only input with a known exact answer.
        ("zero", [0]),
        # Both saturation edges and the values just inside them.
        ("saturate_high", [limit - 1, limit - 2, 6 * scale, 5 * scale + 128, 5 * scale]),
        ("underflow_low", [-limit, -limit + 1, -12 * scale, -9 * scale, -8 * scale]),
        # Every LUT entry: k lands on each of the 2^frac fractional slots.
        ("lut_sweep", [round(j * scale / ((1 << frac) * LOG2E)) for j in range(1 << frac)]),
        # Sign boundary: floor-toward-negative-infinity is easy to get wrong.
        ("near_zero", [-4, -3, -2, -1, 0, 1, 2, 3, 4]),
        # Integer arguments, where the answer is checkable by eye.
        ("integers", [i * scale for i in range(-8, 8)]),
    ]
    generator = torch.Generator().manual_seed(seed)
    noise = (torch.rand(64, generator=generator) * 2 - 1) * 8.0
    named.append(("random", [int(round(float(v) * scale)) for v in noise]))

    return [
        {
            "name": name,
            "input_ticks": ticks,
            "expected_value_ticks": [
                exp_unit_reference(t, bits, point, frac, guard) for t in ticks
            ],
            "expected_idx": [],
        }
        for name, ticks in named
    ]
