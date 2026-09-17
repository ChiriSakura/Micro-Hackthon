"""收敛判据：循环该知道自己什么时候不再变好。

在此之前只有一条停止条件——轮数用完。14 次真实运行里大半是那么停的，而
「跑完了」会被读成「收敛了」。实测那一轮 6 轮全部 RTL 验证、功能全过，但
从第 1 轮起目标值就没动过，Critic 在 uarch↔compiler 之间来回打转，同一组
证据 `['predicted.clock', 'plan.queue']` 被指认了 5 次。
"""

from __future__ import annotations

import pytest

from fast.orchestrator.flow import (
    _BOTTLENECK_PATIENCE,
    _LoopState,
    _bottleneck_key,
    _objective_of_report,
)
from fast.schemas.models import Critique, Decision, Layer, Mutation, Status


class _Plan:
    # `banks` 只是为了让每轮的指纹不同：空转检测（计划和测量逐字节相同）
    # 否则会抢在收敛判据前面触发。真实运行里计划确实每轮都在变
    # （实测 16x8 <-> 16x16），而目标值不变——那正是收敛判据要抓的情形。
    def __init__(self, rows=16, pes=16, clock=2.528, area=1_465_644.0, banks=32,
                 cycles=5838.9):
        self.num_rows, self.pe_per_row = rows, pes
        self.predicted_clock_ns, self.predicted_area_um2 = clock, area
        self.predicted_cycles = cycles
        self.predicted_power_mw = 400.0
        self.queue_depth, self.divider_stages, self.bank_count = 2, 8, banks
        self.sram_bytes = 131072


class _Eval:
    def __init__(self, util=0.850, fidelity="L2-rtl-simulation"):
        self.pe_utilization, self.fidelity = util, fidelity
        self.functional_passed, self.cycles, self.area = True, 1000, None


class _Report:
    def __init__(self, plan=None, evaluation=None, mutation=None):
        self.compiler = plan or _Plan()
        self.evaluation = evaluation or _Eval()
        self.mutation = mutation


def _critique(layer: Layer, evidence: tuple[str, ...]) -> Critique:
    # compiler / planner_model 的干预现在**必须可执行**——否则这一轮会以
    # 「intervention cannot be executed」停下，测不到收敛判据本身。
    value = 0 if layer in (Layer.COMPILER, Layer.PLANNER_MODEL) else "v"
    return Critique(status=Status.PASSED, attribution=layer,
                    decision=Decision.CONTINUE, summary="s", evidence=evidence,
                    mutations=(Mutation(layer=layer, field="queue", operation="rewrite",
                                        value=value, expected_effect="e", risk="r"),))


def _state() -> _LoopState:
    return _LoopState(candidate_index=0, labels=("xm:64:16:64",))


# --- 目标值只认验证过的轮次 --------------------------------------------------

def test_the_objective_is_latency():
    """统一成一个定义：延迟 = cycles x 时钟周期，**越小越好**。

    这里曾经用吞吐，而内层按 edp 排、报告用 (延迟, 功耗) 帕累托——
    三处对"变好"的定义都不同。
    """
    got = _objective_of_report(_Report(_Plan(clock=2.528, cycles=5838.9)))
    assert got == pytest.approx(5838.9 * 2.528)


def test_a_failed_l2_round_is_not_progress():
    """原来只查 fidelity 字符串——一个 L2 **失败**的轮次照样被当成进展。

    "跑过 RTL"不等于"结果是对的"。
    """
    failed = _Eval()
    failed.functional_passed = False
    assert _objective_of_report(_Report(evaluation=failed)) is None


def test_an_unverified_round_has_no_objective():
    """L1 的利用率是 planner 自己代价模型算的。

    拿它当进展，循环会在自己的模型里「收敛」。
    """
    assert _objective_of_report(
        _Report(evaluation=_Eval(0.99, "L1-analytical-shared-model"))) is None


# --- 判据①：瓶颈耗尽 --------------------------------------------------------

def test_the_same_bottleneck_named_repeatedly_stops_the_loop():
    """实测那一轮 `['predicted.clock', 'plan.queue']` 连续出现 5 次，
    而 predicted.clock 六轮全是 396 MHz，一次没动过。"""
    state = _state()
    critique = _critique(Layer.UARCH, ("predicted.clock", "plan.queue"))

    for index in range(_BOTTLENECK_PATIENCE - 1):
        advanced, why = state.apply(critique, _Report(_Plan(banks=8 << index)))
        assert advanced, why

    advanced, why = state.apply(critique, _Report(_Plan(banks=256)))
    assert not advanced
    assert "瓶颈耗尽" in why and "predicted.clock" in why


def test_evidence_order_does_not_hide_a_repeat():
    """模型每轮的证据顺序会变（实测 `['predicted.clock','plan.queue']` 和
    `['plan.queue','predicted.clock']` 都出现过）——那是同一个瓶颈。"""
    a = _critique(Layer.UARCH, ("predicted.clock", "plan.queue"))
    b = _critique(Layer.UARCH, ("plan.queue", "predicted.clock"))
    assert _bottleneck_key(a) == _bottleneck_key(b)


def test_a_different_layer_resets_the_streak():
    """换了一层就不是同一个瓶颈了，重新计数。"""
    state = _state()
    report = _Report()
    state.apply(_critique(Layer.UARCH, ("predicted.clock",)), report)
    state.apply(_critique(Layer.COMPILER, ("predicted.clock",)), report)
    assert state.bottleneck_streak == 1


def test_real_improvement_keeps_the_loop_going():
    """目标值真的变好了就不该停，哪怕归因指向同一层。"""
    state = _state()
    critique = _critique(Layer.UARCH, ("predicted.clock", "plan.queue"))
    for cycles in (6000.0, 5000.0, 4000.0, 3000.0):   # 延迟持续下降
        advanced, why = state.apply(critique, _Report(_Plan(cycles=cycles)))
        assert advanced, why


# --- 判据②：无进展 ----------------------------------------------------------

def test_no_progress_across_verified_rounds_stops_the_loop():
    """归因每轮都换层，所以瓶颈判据不触发——但目标值一直没动。"""
    state = _state()
    # 避开 kernel：它的变异要解析到一个候选标签，会先以别的理由停下，
    # 那样测的就不是「无进展」这条判据了。
    layers = [Layer.UARCH, Layer.COMPILER, Layer.EVALUATOR, Layer.UARCH]
    stopped = ""
    for i, layer in enumerate(layers):
        advanced, why = state.apply(_critique(layer, (f"field.{i}",)),
                                    _Report(_Plan(banks=8 << i)))
        if not advanced:
            stopped = why
            break
    assert "无进展" in stopped


def test_a_tie_is_not_progress():
    """5 轮的利用率相同到 16 位小数——用 `>` 会把浮点尾数差当成改进。"""
    state = _state()
    state.apply(_critique(Layer.UARCH, ("a",)), _Report(_Plan(banks=16, cycles=5838.9)))
    before = state.best_objective
    state.apply(_critique(Layer.COMPILER, ("b",)),
                _Report(_Plan(banks=32, cycles=5838.9000001)))
    assert state.best_objective == before
    assert state.rounds_without_progress == 1
