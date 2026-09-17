"""为提高利用率而换候选，必须换到**实测更均衡**的那个。

原来 `_switch_to_next` 无条件走 `index + 1`，而候选的排序不是按不均衡度来的。
下面用的是作业 17248126 真正测出来的 tile(32) 值（同一个算法的不同配置）：

    xm:32:4:64    tile 不均衡度 1.576   稀疏度 0.8681
    xm:32:16:64                 1.425          0.8362
    xm:32:32:64                 1.336          0.7932

顺序上的下一个恰好更均衡，是运气；判据必须是实测不均衡度本身。

**这些必须是实测值，不能是回退值。** `tile_imbalance_for` 在
`tile_load_imbalance` 缺失时退回全局 `load_imbalance`，而两者差 1.9-2.5 倍、
排序也不同——本文件早先的一版就引了回退值（2.666 / 3.922 / 1.142）并把它们
写成「实测」。
"""

from __future__ import annotations

from fast.agents.critic import _switch_to_next
from fast.schemas.models import KernelMeasurement, KernelProfile, Status


def _profile(imbalance: float) -> KernelProfile:
    return KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
        block_density_histogram=(1, 1, 1, 1), load_imbalance=imbalance,
        column_top1_mass=0.1, column_top5_mass=0.3, column_top10_mass=0.5,
        tile_load_imbalance=((32, imbalance),),
    )


def _candidate(label: str, imbalance: float, sparsity: float = 0.8) -> KernelMeasurement:
    return KernelMeasurement(
        label=label, status=Status.PASSED, perplexity=10.0, quality_loss=0.02,
        actual_sparsity=sparsity, index_entropy=0.9, block_occupancy=0.5,
        row_kept_min=8.0, row_kept_max=16.0, wall_seconds=1.0,
        profile=_profile(imbalance),
    )


# 三个候选用的是真实测出来的不均衡度。
_SPARSE = _candidate("xm:32:4:64", 1.576, 0.8681)
_MID = _candidate("xm:32:16:64", 1.425, 0.8362)
_BALANCED = _candidate("xm:32:32:64", 1.336, 0.7932)


def test_utilisation_switch_picks_the_most_balanced_not_the_next():
    """顺序上的下一个恰好更好，是运气；判据必须是实测不均衡度。"""
    candidates = (_SPARSE, _MID, _BALANCED)   # 顺序上的下一个不是最均衡的
    switch = _switch_to_next(candidates, 0, for_utilisation=True)
    assert switch is not None
    assert switch.value == 2                      # 最均衡的，不是顺序上的下一个
    assert "1.336" in switch.expected_effect
    assert "1.576" in switch.expected_effect      # 对着当前值说，才可证伪


def test_no_switch_when_nothing_is_more_balanced():
    """没有更均衡的候选就不动——换过去只会让要修的那个量更差。"""
    candidates = (_BALANCED, _MID, _SPARSE)       # 当前已经是最均衡的
    assert _switch_to_next(candidates, 0, for_utilisation=True) is None


def test_non_utilisation_switch_still_advances_in_order():
    """「规划不出可行硬件」要换的是代价更低的点，不是更均衡的点。"""
    candidates = (_SPARSE, _MID, _BALANCED)
    switch = _switch_to_next(candidates, 0)
    assert switch is not None and switch.value == 1


def test_candidates_without_a_measured_profile_fall_back_to_order():
    """没测到不均衡度就不假装有：退回顺序推进，不给一个中性默认值。"""
    bare = KernelMeasurement(
        label="unmeasured", status=Status.PASSED, perplexity=10.0, quality_loss=0.02,
        actual_sparsity=0.75, index_entropy=0.9, block_occupancy=0.5,
        row_kept_min=8.0, row_kept_max=16.0, wall_seconds=1.0, profile=None,
    )
    switch = _switch_to_next((bare, bare), 0, for_utilisation=True)
    assert switch is not None and switch.value == 1
