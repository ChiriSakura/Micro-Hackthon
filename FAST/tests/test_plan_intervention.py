"""「重入某层」不等于「执行了该层的建议」。

评审 P1-2：compiler / planner_model 的变异只设 `replan=True`，field / value /
expected_effect **全被丢掉**——下一轮用同样的输入再调一次 `plan()`，规则
proposer 会确定性地给出**完全相同**的结果。

这和 µArch 那条曾经犯过的错是同一个：不把变异交给下游，「重新实现」就只是
再算一遍。

实测的干预是具体可执行的：

    {"layer":"compiler","field":"queue","value":0}
    {"layer":"compiler","field":"clock_period_ns","value":2.3}
"""

from __future__ import annotations

import pytest

from fast.agents.codesign import CoDesignSpace, plan_intervention
from fast.schemas.models import Layer, Mutation


def _mutation(field, value, layer=Layer.COMPILER) -> Mutation:
    return Mutation(layer=layer, field=field, operation="set", value=value,
                    expected_effect="e", risk="r")


@pytest.mark.parametrize("field", ["queue", "plan.queue", "queue_depth"])
def test_the_same_intervention_survives_the_models_wording(field):
    """模型的措辞每轮都不同——实测同一个干预出现过三种写法。"""
    got = plan_intervention([_mutation(field, 0)])
    assert got.pinned == {"queue_depth": (0,)}
    assert got.actionable


def test_a_pinned_dimension_actually_restricts_the_search():
    """钉住了就要真的进搜索空间，否则规则 proposer 给出同一个计划。"""
    space = plan_intervention([_mutation("queue", 0)]).restrict(CoDesignSpace())
    assert space.queue_depth == (0,)
    # 其余维度不动——一轮只变一件事。
    assert space.num_rows == CoDesignSpace().num_rows


def test_a_clock_ceiling_becomes_a_frequency_floor():
    """`clock_period_ns <= 2.3` 是一条约束，不是一个钉住的维度。"""
    got = plan_intervention([_mutation("clock_period_ns", 2.3)])
    assert got.max_clock_ns == pytest.approx(2.3)
    assert got.pinned == {}
    assert got.actionable


def test_an_unrecognised_field_is_reported_not_swallowed():
    """评审的完成条件是「每项 mutation 确实执行**或明确报不支持**」。"""
    got = plan_intervention([_mutation("wibble", "x")])
    assert not got.actionable
    assert got.unsupported and "wibble" in got.unsupported[0]


def test_a_non_numeric_value_is_reported_not_guessed():
    got = plan_intervention([_mutation("queue", "deeper")])
    assert not got.actionable
    assert "not an integer" in got.unsupported[0]


def test_other_layers_are_left_alone():
    """µArch 的变异走它自己的路径，不该被这里吞掉。"""
    got = plan_intervention([_mutation("candidate", 1, layer=Layer.UARCH)])
    assert not got.actionable and got.unsupported == ()


def test_an_unexecutable_intervention_stops_the_round():
    """假装重规划了一次比停下来更糟——下一轮会拿同样的结果继续。"""
    from fast.orchestrator.flow import _LoopState
    from fast.schemas.models import Critique, Decision, Status

    state = _LoopState(candidate_index=0, labels=("xm:64:16:64",))
    critique = Critique(status=Status.PASSED, attribution=Layer.COMPILER,
                        decision=Decision.CONTINUE, summary="s", evidence=("e",),
                        mutations=(_mutation("wibble", "x"),))
    advanced, why = state.apply(critique, None)
    assert not advanced
    assert "cannot be executed" in why and "wibble" in why


def test_an_executable_intervention_is_queued_for_the_next_plan():
    from fast.orchestrator.flow import _LoopState
    from fast.schemas.models import Critique, Decision, Status

    state = _LoopState(candidate_index=0, labels=("xm:64:16:64",))
    critique = Critique(status=Status.PASSED, attribution=Layer.COMPILER,
                        decision=Decision.CONTINUE, summary="s", evidence=("e",),
                        mutations=(_mutation("queue", 0),))
    advanced, why = state.apply(critique, None)
    assert advanced, why
    assert state.replan
    assert state.pending_plan.pinned == {"queue_depth": (0,)}


# --- 周期和频率不是一回事 -----------------------------------------------------

@pytest.mark.parametrize("field,value,expected_ns", [
    ("clock_period_ns", 2.5, 2.5),
    ("predicted.clock", 2.3, 2.3),
    # 实测出现过的第三种写法，它曾让一整轮以「unknown plan field」停掉。
    ("clock_period_constraint_ns", 2.3, 2.3),
    # **频率要换算。** 把 400 MHz 当成 400 ns 的周期会得到一个荒谬的约束，
    # 而且不会有任何东西报错——正是这个项目反复撞到的那类单位混用。
    ("max_frequency_mhz", 400.0, 2.5),
    ("target_freq", 500.0, 2.0),
])
def test_a_timing_constraint_is_read_in_its_own_unit(field, value, expected_ns):
    got = plan_intervention([_mutation(field, value)])
    assert got.max_clock_ns == pytest.approx(expected_ns)


@pytest.mark.parametrize("value", [0, -1, "fast"])
def test_a_nonsensical_timing_value_is_reported(value):
    """0 或负的周期没有意义；报出来，不要拿它去约束搜索。"""
    got = plan_intervention([_mutation("clock_period_ns", value)])
    assert got.max_clock_ns is None
    assert got.unsupported
