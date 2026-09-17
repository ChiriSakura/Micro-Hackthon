"""µArch 变异实测到的关键路径，必须回灌到目标函数。

实测撞到过（作业 17300572）：两次变异 `accepted=True`，而延迟/功耗/面积
四轮完全没动——因为目标是从 `predicted_cycles x predicted_clock_ns` 算的，
两个都来自计划的 L1 模型。**RTL 变了，模型不知道**，于是变异对目标的影响
在整条评估链上是不可见的。

门本来就量到了那个数（BlockScheduler depth 4 实测 2.760 ns，与标定表一致），
只是没接回来。
"""

from __future__ import annotations

import pytest

from fast.agents.codesign import (
    ARRAY_CRITICAL_PATH_NS,
    component_of_module,
    effective_clock_ns,
)

_SHAPE = dict(num_rows=16, pe_per_row=16, queue_depth=2, divider_stages=8)


def test_a_measured_path_replaces_only_its_own_segment():
    """时钟是 max(阵列, 除法器, 队列)。实测队列不该覆盖整体。"""
    modelled = effective_clock_ns(**_SHAPE)
    slower = effective_clock_ns(**_SHAPE, measured={"queue": 3.500})
    assert slower == pytest.approx(3.500)
    assert modelled < slower


def test_the_clock_floors_at_the_slowest_other_segment():
    """把队列缩到 2.200 也不会让时钟到 2.200——阵列的 2.230 顶着。

    这正是要按段替换而不是整体覆盖的原因：一段变快**不一定**让时钟变快。
    """
    got = effective_clock_ns(**_SHAPE, measured={"queue": 2.200})
    assert got == pytest.approx(ARRAY_CRITICAL_PATH_NS)
    assert got > 2.200


def test_a_module_outside_the_clock_model_substitutes_nothing():
    """KeyFeeder / TopK 也能被变异、门也会量它们的关键路径，但那个数替换
    不了任何一段——**报出来而不是悄悄忽略**，否则会让人以为量了就算进去了。
    """
    assert component_of_module("KeyFeeder_B32") is None
    assert component_of_module("TopK") is None
    assert component_of_module("BlockSched_S4") == "queue"
    assert component_of_module("Divider") == "divider"
    # 不在模型里的段不会改变时钟。
    assert effective_clock_ns(**_SHAPE, measured={"gather": 9.9}) == pytest.approx(
        effective_clock_ns(**_SHAPE))


def test_a_real_improvement_shows_up_in_the_clock():
    """队列从实测的 2.760 缩到 2.4，时钟应当跟着降。"""
    before = effective_clock_ns(**_SHAPE, measured={"queue": 2.760})
    after = effective_clock_ns(**_SHAPE, measured={"queue": 2.400})
    assert after < before
