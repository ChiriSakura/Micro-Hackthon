"""保真度阶梯：升档不能让已知的量变回未知。

各档**测的不是同一组量**。L1 的解析模型给利用率/面积/功耗，L2 跑真实 RTL
只答功能对不对。原来的实现是整体覆盖（`best = upper`），于是升到 L2 之后
`pe_utilization`/`area`/`power` 全变 None——Critic 的利用率门和代价模型偏差
检查因此在**最高保真度上静默失效**。这是「有约束但不咬人」的又一个实例，
真实的 L2 协同设计运行里表现为 `util=None` 却报 `acceptance gates passed`。
"""

from __future__ import annotations

from fast.agents.evaluator import EvaluatorAgent
from fast.schemas.models import (
    Budget,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    Status,
)


def _result(fidelity: str, *, functional: bool, util, area, power) -> EvaluationResult:
    return EvaluationResult(
        status=Status.PASSED, fidelity=fidelity, functional_passed=functional,
        cycles=None, throughput=None, pe_utilization=util, area=area, power=power,
        edp=None, wall_seconds=0.1, cloud_cost_usd=0.0, log_uri="",
        evidence=(f"{fidelity}.evidence",),
    )


class _Fixed:
    def __init__(self, result):
        self.result = result

    def evaluate(self, spec, candidate, plan=None, kernel=None):
        return self.result


def _spec() -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="ladder", candidate_id="c0", model="m", dataset="d",
        sequence_length=128, sparsity_x=8, sparsity_m=64, epsilon=0.05,
        seed=0, budget=Budget(max_candidates=1, max_evaluations=1),
    )


def _candidate() -> HardwareCandidate:
    return HardwareCandidate(
        status=Status.PASSED, template_id="repe_array", template_digest="d",
        verified_template=True, pe_rows=32, pe_cols=8, queue_depth=4,
        sram_bytes=131072, data_width=16, manifest_uri="",
    )


def test_escalation_keeps_metrics_the_upper_tier_does_not_measure():
    """L2 只答功能；利用率/面积/功耗必须留着 L1 的值。"""
    l1 = _result("L1-analytical-shared-model", functional=False,
                 util=0.62, area=2_100_000.0, power=390.0)
    l2 = _result("L2-rtl-simulation", functional=True,
                 util=None, area=None, power=None)

    agent = EvaluatorAgent(_Fixed(l1), ladder=(_Fixed(l2),))
    got = agent.run(_spec(), _candidate())

    # 功能结论和保真度归 L2——那是它唯一能答而 L1 答不了的问题。
    assert got.fidelity == "L2-rtl-simulation"
    assert got.functional_passed is True
    # 但 L1 测到的量不能因为升档而消失。
    assert got.pe_utilization == 0.62
    assert got.area == 2_100_000.0
    assert got.power == 390.0


def test_borrowed_fields_say_which_tier_they_came_from():
    """混着两档的结果必须标出来，否则等于给面积一个它没有的证据等级。"""
    l1 = _result("L1-analytical-shared-model", functional=False,
                 util=0.62, area=2_100_000.0, power=None)
    l2 = _result("L2-rtl-simulation", functional=True,
                 util=None, area=None, power=None)

    got = EvaluatorAgent(_Fixed(l1), ladder=(_Fixed(l2),)).run(_spec(), _candidate())

    assert "pe_utilization<-L1-analytical-shared-model" in got.evidence
    assert "area<-L1-analytical-shared-model" in got.evidence
    # power 两档都没测到，不该假装借到了什么。
    assert not any(item.startswith("power<-") for item in got.evidence)


def test_upper_tier_value_wins_when_it_actually_measured_it():
    """L2 真测到了就用 L2 的，不能被 L1 的旧值盖住。"""
    l1 = _result("L1-analytical-shared-model", functional=False,
                 util=0.62, area=2_100_000.0, power=390.0)
    l2 = _result("L2-rtl-simulation", functional=True,
                 util=0.48, area=None, power=None)

    got = EvaluatorAgent(_Fixed(l1), ladder=(_Fixed(l2),)).run(_spec(), _candidate())

    assert got.pe_utilization == 0.48
    assert not any(item.startswith("pe_utilization<-") for item in got.evidence)
