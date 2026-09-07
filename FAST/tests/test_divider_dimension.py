"""除法器进入搜索空间之后，协同优化器才可能选对。

实测（Nangate45）暴露的不是「模型不准」，是**模型看不见一个决定结果的变量**：

    执行阵列   2.23 ns   450 MHz
    除法器    14.78 ns    68 MHz   ← 时钟由它决定

而搜索空间里 9 个维度全是阵列和调度的。更根本的是代价模型里
`edp = energy * cycles`、`energy = power * cycles`——**时钟周期从来没进过
公式**，所以即使加了维度，快的除法器也不会改变任何数字。

这些测试钉住的就是「维度真的起作用」这件事。
"""

from __future__ import annotations

from fast.agents.codesign import CoDesignPoint, CoDesignSpace, estimate
from fast.agents.templates import (
    ARRAY_CRITICAL_PATH_NS,
    divider_area_um2,
    divider_critical_path_ns,
)
from fast.schemas.models import KernelProfile


class _Kernel:
    actual_sparsity = 0.9
    block_occupancy = 0.42
    profile = None


def _point(divider_stages: int) -> CoDesignPoint:
    return CoDesignPoint(
        tile_q=64, tile_k=64, tile_d=64, parallelism=8, double_buffer=False,
        num_rows=32, pe_per_row=4, reg_width=16, data_width=16,
        sram_bytes=65536, queue_depth=0, divider_stages=divider_stages,
    )


def _metrics(divider_stages: int) -> dict:
    return estimate(_point(divider_stages), _Kernel(), 512,
                    block_m=64, kept_per_block=16)


def test_edp_has_a_time_dimension():
    """EDP 必须是能量 x 时间，不是「周期² x 功率」。

    改之前 edp = (power * cycles) * cycles，量纲里没有秒。后果是时钟频率
    完全不影响 EDP——一个 68 MHz 的设计和 450 MHz 的设计看起来一样好。
    """
    metrics = _metrics(8)

    assert "seconds" in metrics
    assert "clock_period_ns" in metrics
    # edp = energy * seconds，而 energy = power * seconds
    expected = metrics["power"] * metrics["seconds"] ** 2
    assert abs(metrics["edp"] - expected) / expected < 1e-9


def test_the_clock_is_set_by_the_slower_of_array_and_divider():
    """时钟周期取数据通路上最慢的那一段，两段都是实测的。"""
    # 上游的组合除法：14.78 ns，远慢于阵列的 2.23 ns。
    assert _metrics(0)["clock_period_ns"] == divider_critical_path_ns(0)
    # 8 级之后除法器 1.98 ns，比阵列快，瓶颈交回给阵列。
    assert _metrics(8)["clock_period_ns"] == ARRAY_CRITICAL_PATH_NS


def test_pipelining_the_divider_improves_edp_by_more_than_an_order_of_magnitude():
    """这是实测逼出来的结论：0.8% 的面积换 40 倍以上的 EDP。"""
    slow = _metrics(0)
    fast = _metrics(8)

    assert fast["edp"] < slow["edp"] / 10
    # 面积代价很小——这正是为什么这个取舍毫无悬念，而在有实测之前
    # 优化器连这个选项都看不见。
    assert fast["area"] / slow["area"] < 1.02


def test_past_the_array_bottleneck_more_stages_only_cost_area():
    """8 级之后瓶颈交回执行阵列，再深的流水只剩成本。

    模型必须自己识别这个拐点，否则优化器会无脑选最深的流水。
    """
    eight = _metrics(8)
    twelve = _metrics(12)

    assert eight["clock_period_ns"] == twelve["clock_period_ns"]
    assert eight["edp"] == twelve["edp"]
    assert twelve["area"] > eight["area"]   # 更深只多花面积


def test_the_divider_area_is_charged_to_the_design():
    """不把除法器面积算进去，「换频率」就只有收益没有成本。"""
    charged = _metrics(12)["area"] - _metrics(0)["area"]
    expected = divider_area_um2(12) - divider_area_um2(0)

    assert abs(charged - expected) < 1e-6


def test_the_search_space_actually_varies_the_divider():
    """维度要真的出现在枚举出来的点里，不只是 dataclass 上多个字段。"""
    space = CoDesignSpace()

    assert 0 in space.divider_stages      # 上游的组合除法必须仍可选
    assert 8 in space.divider_stages      # 越过 500 MHz 的那个点


def test_the_measured_profile_matches_what_synthesis_reported():
    """曲线上的数字来自 slurm job 17085953，改动它就是改动结论。"""
    measured = {
        0: (2081.4, 14.780),
        4: (4160.0, 3.269),
        8: (5411.8, 1.980),
        12: (6367.5, 1.546),
    }
    for stages, (area, path) in measured.items():
        assert divider_area_um2(stages) == area
        assert divider_critical_path_ns(stages) == path
