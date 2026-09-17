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
    queue_critical_path_ns,
    ARRAY_CRITICAL_PATH_NS,
    divider_area_um2,
    divider_critical_path_ns,
)
from fast.schemas.models import KernelProfile


class _Kernel:
    actual_sparsity = 0.9
    block_occupancy = 0.42
    profile = None
    # 硬件侧要靠它查取数引擎的 bank 冲突表：冲突取决于索引分布，
    # 而分布由稀疏方法决定。
    sparse_method = "xm"


def _point(divider_stages: int) -> CoDesignPoint:
    return CoDesignPoint(
        tile_q=64, tile_k=64, tile_d=64, parallelism=8, double_buffer=False,
        num_rows=32, pe_per_row=4, reg_width=16, data_width=16,
        sram_bytes=65536, queue_depth=0, divider_stages=divider_stages,
    )


def _metrics(divider_stages: int) -> dict:
    return estimate(_point(divider_stages), _Kernel(), 512, head_dim=64,
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
    expected = metrics["power"] * 1e-3 * metrics["seconds"] ** 2  # mW -> W
    assert abs(metrics["edp"] - expected) / expected < 1e-9


def test_the_clock_is_set_by_the_slowest_stage_on_the_datapath():
    """时钟周期取数据通路上最慢的那一段，每一段都是实测的。

    参与竞争的有三个：执行阵列 2.23 ns、除法器（随级数变）、工作队列
    （随深度变）。三个都实测过，而且**三个都真的当过瓶颈**——这不是
    防御性的 max，是三条实测曲线交叉的结果。
    """
    # 上游的组合除法：14.78 ns，远慢于其它两段。
    assert _metrics(0)["clock_period_ns"] == divider_critical_path_ns(0)
    # 8 级之后除法器 1.98 ns，不再是瓶颈；剩下阵列 2.23 ns 和队列。
    period = _metrics(8)["clock_period_ns"]
    assert period > divider_critical_path_ns(8)
    assert period >= ARRAY_CRITICAL_PATH_NS


def test_a_deep_queue_takes_the_clock_away_from_the_array():
    """深度 8 起，决定系统频率的不再是阵列而是调度器。

    这是实测才看得见的：队列的关键路径从 2.27 ns（深度 0）涨到 3.14 ns
    （深度 8），而阵列是 2.23 ns。没有这条曲线，深度看起来只有好处。
    """
    assert queue_critical_path_ns(32, 4, 0) < queue_critical_path_ns(32, 4, 8)
    assert queue_critical_path_ns(32, 4, 8) > ARRAY_CRITICAL_PATH_NS
    # 41% 的时钟惩罚，换来的利用率是 0.864 -> 0.867。
    penalty = queue_critical_path_ns(32, 4, 8) / ARRAY_CRITICAL_PATH_NS
    assert penalty > 1.35


def test_pipelining_the_divider_improves_edp_by_more_than_an_order_of_magnitude():
    """这是实测逼出来的结论：整设计 6.4% 的面积换 40 倍以上的 EDP。"""
    slow = _metrics(0)
    fast = _metrics(8)

    assert fast["edp"] < slow["edp"] / 10
    # 面积代价：**每个 query 行一个除法器**，所以 32 行的设计要付 32 份。
    #
    # 早先记的「0.8% 的面积」是拿一个除法器对一个执行阵列比出来的；整设计
    # 尺度上是 6.4%（1,775,479 / 1,668,906）。结论不变——6.4% 换 40 倍 EDP
    # 仍然毫无悬念——但那个 0.8% 是错的，不该靠放宽阈值糊过去。
    assert fast["area"] / slow["area"] < 1.08


def test_past_the_array_bottleneck_more_stages_only_cost_area():
    """8 级之后瓶颈交回执行阵列，再深的流水只剩成本。

    模型必须自己识别这个拐点，否则优化器会无脑选最深的流水。
    """
    eight = _metrics(8)
    twelve = _metrics(12)

    assert eight["clock_period_ns"] == twelve["clock_period_ns"]
    assert eight["edp"] == twelve["edp"]
    assert twelve["area"] > eight["area"]   # 更深只多花面积


def test_the_divider_area_is_charged_once_per_query_row():
    """不把除法器面积算进去，「换频率」就只有收益没有成本。

    **而且要按 query 行数计。** `attention_tile.scala` 是
    `Seq.fill(tileQ)(Module(new FixedPointDivPipelined(...)))`——每行一个
    归一化器。模型此前只算一个，32 行的设计因此少算 168k um^2。

    这个缺陷是整设计综合实测发现的：模型预测 1,072,094 um^2 而实测
    2,124,822。逐模块综合看不出来——单个除法器的面积一直是对的，错的是数量。
    """
    point = _point(0)
    rows = point.num_rows
    charged = _metrics(12)["area"] - _metrics(0)["area"]
    expected = rows * (divider_area_um2(12) - divider_area_um2(0))

    assert abs(charged - expected) < 1e-6, (
        f"每行一个除法器：{rows} 行应计 {expected:,.0f} um^2，实际计了 {charged:,.0f}"
    )


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
