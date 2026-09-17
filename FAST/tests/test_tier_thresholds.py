"""阈值换算：硬件比的量和软件比的量不是同一个。

Chisel 里那句「缩放放在软件侧算阈值时做」原来只是注释。注释里的**声称**
和代码里的**行为**是两回事——这个测试把声称变成可证伪的。
"""

from __future__ import annotations

import pytest

from fast.schemas.tier_thresholds import (
    SOFTWARE_THRESHOLD_HIGH,
    SOFTWARE_THRESHOLD_LOW,
    keep_for_mass,
    thresholds_for,
)


def test_the_scaling_folds_the_block_count_into_the_threshold():
    """软件 `sum_m = sum(block) * token_len / m`，硬件不做那个放大。

    所以阈值要除以「一行有几个 block」。
    """
    got = thresholds_for(token_len=512, block_m=64)
    assert got.blocks_per_row == 8
    assert got.hardware_high == pytest.approx(SOFTWARE_THRESHOLD_HIGH / 8)
    assert got.hardware_low == pytest.approx(SOFTWARE_THRESHOLD_LOW / 8)


def test_a_sequence_not_divisible_by_the_block_is_refused():
    """软件侧同样拒绝——reshape 会失败。不要在这里悄悄取整。"""
    with pytest.raises(ValueError, match="整除"):
        thresholds_for(token_len=500, block_m=64)


def test_the_high_tier_wins_over_the_discard_tier():
    """软件是两次 `torch.where` 叠加，等价于 hi 优先。

    写反了会让一个质量很高的块在 lo 那一步被判丢弃之后再也回不来。
    """
    t = thresholds_for(token_len=512, block_m=64)
    # 构造一个同时 > hi 的质量（必然也 > lo）。
    assert keep_for_mass(t.hardware_high * 2, t, n1=32, n2=4) == 32


@pytest.mark.parametrize("mass_factor,expected", [
    (2.0, "high"),     # > hi
    (0.5, "mid"),      # 在 lo 和 hi 之间
    (0.01, "drop"),    # < lo
])
def test_the_three_tiers(mass_factor, expected):
    t = thresholds_for(token_len=512, block_m=64)
    got = keep_for_mass(t.hardware_high * mass_factor, t, n1=32, n2=4)
    assert got == {"high": 32, "mid": 4, "drop": 0}[expected]


def test_the_hardware_comparison_is_not_claimed_to_be_exact():
    """硬件在分档那一刻还没有整行的 exp 总和，比的是**未归一化**的量。

    严格对齐需要两趟。这个测试锁住「不要让『换算过了』看起来像『对齐了』」。
    """
    t = thresholds_for(token_len=512, block_m=64)
    assert not t.hardware_is_exact()
