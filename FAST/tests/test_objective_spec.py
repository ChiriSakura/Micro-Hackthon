"""「变好」只能有一个定义。

评审 P1-3：内层 `CoOptimizer` 按 `edp` 挑最优，外层收敛用「面积约束下的
吞吐」，最终报告给 (延迟, 功耗) 的帕累托前沿——**三处各说各话**。后果是
内层选出来的点未必是外层想要的点，而稀疏度带来的收益可能在某一层被忽略。
"""

from __future__ import annotations

import pytest

from fast.agents.codesign import DEFAULT_OBJECTIVE, ObjectiveSpec


def test_the_primary_must_be_one_of_the_pareto_axes():
    """否则内层会朝一个不在最终判据里的方向优化——那正是修掉的那个错。"""
    with pytest.raises(ValueError, match="不在 pareto_axes"):
        ObjectiveSpec(primary="edp", pareto_axes=("seconds", "power"))


def test_the_default_objective_minimises_latency():
    """按约定的 formulation：min L(x) s.t. 约束。"""
    assert DEFAULT_OBJECTIVE.primary == "seconds"
    assert "seconds" in DEFAULT_OBJECTIVE.pareto_axes


def test_energy_and_latency_are_axes_even_while_estimates_are_partial():
    from fast.agents.codesign import POWER_COVERAGE
    assert DEFAULT_OBJECTIVE.pareto_axes == ("seconds", "energy_j")
    assert POWER_COVERAGE["status"] == "partial"
    assert "predict-array" in POWER_COVERAGE["excluded"]


def test_a_lower_score_is_better():
    faster = DEFAULT_OBJECTIVE.score({"seconds": 1e-5, "power": 400.0})
    slower = DEFAULT_OBJECTIVE.score({"seconds": 2e-5, "power": 400.0})
    assert faster < slower


def test_a_point_missing_the_metric_sorts_last():
    """返回 0 会让一个缺数据的点看起来最好。"""
    assert DEFAULT_OBJECTIVE.score({}) == float("inf")
    assert DEFAULT_OBJECTIVE.score({"seconds": None}) == float("inf")


def test_the_inner_search_ranks_by_the_same_objective():
    """内层的 `best` 必须用同一个 score，而不是它自己的 edp。"""
    import inspect

    from fast.agents.cooptimizer import CoOptimizer

    source = inspect.getsource(CoOptimizer.run)
    assert 'item.metrics["edp"]' not in source, "内层还在按 edp 排"
    assert "objective.score(item.metrics)" in source
