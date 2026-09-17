"""归因之后重入哪一层，以及「换候选」的两种说法都要能落地。

两个都对应真实运行里发生过的事：

  1. `run_codesign.py` 曾经手写了一个只认「换 kernel 候选」的循环。两次真实
     LLM 运行分别归因到 compiler 和 uarch，都被报成「该层的变异本脚本不施加」
     然后停在第 0 轮——看起来像 Critic 给不出可执行动作，实际上
     `_LoopState.apply` 一直支持这四层，是接收端少了三层。
  2. 确定性 Critic 发 `candidate_index=<int>`，LLM Critic 发
     `candidate="sanger"`。同一个动作的两种词汇，只认一种等于听不懂一半。
"""

from __future__ import annotations

import pytest

from fast.orchestrator.flow import _LoopState
from fast.schemas.models import Critique, Decision, Layer, Mutation, Status


def _critique(*mutations: Mutation) -> Critique:
    return Critique(
        status=Status.PASSED, attribution=Layer.KERNEL,
        decision=Decision.CONTINUE, summary="t", evidence=("evaluation.pe_utilization",),
        mutations=mutations,
    )


def _mutation(layer: Layer, field: str, value) -> Mutation:
    return Mutation(layer=layer, field=field, operation="switch", value=value,
                    expected_effect="e", risk="r")


def test_kernel_switch_by_label_resolves_to_an_index():
    """LLM Critic 用名字指定候选，也要能换过去。"""
    state = _LoopState(candidate_index=0, labels=("xm:32:16:64", "topk:128", "sanger"))
    advanced, why = state.apply(_critique(_mutation(Layer.KERNEL, "candidate", "sanger")), None)
    assert advanced, why
    assert state.candidate_index == 2
    # 换了工作负载，计划必须跟着重来。
    assert state.replan is True


def test_kernel_switch_by_index_still_works():
    state = _LoopState(candidate_index=0, labels=("a", "b", "c"))
    advanced, _ = state.apply(_critique(_mutation(Layer.KERNEL, "candidate_index", 1)), None)
    assert advanced and state.candidate_index == 1


def test_any_field_name_works_when_the_value_names_a_candidate():
    """字段名是模型自由发挥的部分，值不是。

    同一个模型在一次运行里就用了两个名字：第 0 轮 `candidate`、第 2 轮
    `kernel_candidate`。字段名白名单会把后者丢掉——而那是一个完全正确的
    动作（换到 topk:128，实测不均衡度最低）。
    """
    state = _LoopState(candidate_index=0, labels=("xm:32:8:64", "topk:128", "sanger"))
    for field in ("kernel_candidate", "sparse_method", "label", "whatever"):
        fresh = _LoopState(candidate_index=0, labels=state.labels)
        advanced, why = fresh.apply(
            _critique(_mutation(Layer.KERNEL, field, "topk:128")), None)
        assert advanced, f"{field}: {why}"
        assert fresh.candidate_index == 1


def test_index_survives_a_json_round_trip_as_a_string():
    state = _LoopState(candidate_index=0, labels=("a", "b", "c"))
    advanced, _ = state.apply(_critique(_mutation(Layer.KERNEL, "candidate_index", "2")), None)
    assert advanced and state.candidate_index == 2


def test_unknown_label_does_not_silently_pick_something():
    """解析不出来就不前进——换错候选会让下一轮的测量对不上归因的预期。"""
    state = _LoopState(candidate_index=0, labels=("a", "b"))
    advanced, why = state.apply(_critique(_mutation(Layer.KERNEL, "candidate", "nope")), None)
    assert not advanced
    assert "no mutation to act on" in why


def test_uarch_attribution_keeps_the_plan_and_only_reimplements():
    """归因到 µArch 时计划不动：这一轮只验证 RTL 改动有没有用。"""
    state = _LoopState(candidate_index=0, labels=("a",))
    advanced, _ = state.apply(
        _critique(_mutation(Layer.UARCH, "queue_depth", 2)), None)
    assert advanced
    assert state.reimplement is True
    assert state.replan is False


def test_compiler_attribution_replans():
    state = _LoopState(candidate_index=0, labels=("a",))
    advanced, _ = state.apply(
        _critique(_mutation(Layer.COMPILER, "queue_depth", 2)), None)
    assert advanced and state.replan is True


def test_evaluator_attribution_changes_neither():
    """只换保真度，计划和硬件都保。"""
    state = _LoopState(candidate_index=0, labels=("a",))
    advanced, _ = state.apply(
        _critique(_mutation(Layer.EVALUATOR, "fidelity", "L2")), None)
    assert advanced
    assert state.replan is False and state.reimplement is False


def test_a_candidate_already_tried_stops_the_loop():
    state = _LoopState(candidate_index=0, labels=("a", "b"))
    state.apply(_critique(_mutation(Layer.KERNEL, "candidate_index", 1)), None)
    advanced, why = state.apply(_critique(_mutation(Layer.KERNEL, "candidate_index", 0)), None)
    assert not advanced and "already tried" in why


# --- 变异什么都没改，要就地停下 ---------------------------------------------

class _FakePlan:
    def __init__(self, queue_depth):
        self.num_rows, self.pe_per_row = 16, 16
        self.queue_depth, self.divider_stages, self.bank_count = queue_depth, 8, 16
        self.sram_bytes = 131072


class _FakeEval:
    def __init__(self, util):
        self.functional_passed, self.pe_utilization = True, util
        self.cycles, self.area = 1000, 1_450_474.0


class _FakeReport:
    def __init__(self, queue_depth=2, util=0.8503):
        self.compiler, self.evaluation = _FakePlan(queue_depth), _FakeEval(util)


def test_a_mutation_that_changed_nothing_stops_the_loop():
    """`UArchAgent.run(plan, template_id)` 是计划的纯函数。

    保计划重新实现，得到的必然是逐字节相同的硬件和测量。实测撞到过：Critic
    连续两轮发 `uarch.queue rewrite`，三轮的计划和 util 完全一样，循环照常
    跑完，没有任何东西说这两轮白跑了。
    """
    state = _LoopState(candidate_index=0, labels=("xm:64:16:64",))
    mutation = _critique(_mutation(Layer.UARCH, "queue", "reduce critical path"))

    advanced, _ = state.apply(mutation, _FakeReport())
    assert advanced, "第一轮还没有可比的前一轮"

    advanced, why = state.apply(mutation, _FakeReport())   # 完全相同的结果
    assert not advanced
    assert "没有改变任何东西" in why


def test_a_mutation_that_did_change_something_continues():
    state = _LoopState(candidate_index=0, labels=("xm:64:16:64",))
    mutation = _critique(_mutation(Layer.UARCH, "queue", "reduce critical path"))

    state.apply(mutation, _FakeReport(queue_depth=2, util=0.8503))
    advanced, why = state.apply(mutation, _FakeReport(queue_depth=4, util=0.8712))
    assert advanced, why


# --- 对格式宽容，对含义严格 ---------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("xm:64:16:64", 1),                     # 干净的标签
    ("#1 xm:64:16:64", 1),                  # 实测：模型按 menu 的显示格式回写
    ("candidate #2", 2),                    # 只给序号
    ("#2", 2),
    (2, 2),                                 # 直接给整数
    ("2", 2),                               # JSON 往返变成字符串
    ("switch to xm:32:32:64 please", 2),    # 裹在一句话里
])
def test_a_candidate_switch_survives_the_models_formatting(value, expected):
    """模型会按它在候选清单里看到的样子回写。

    实测发过 `"#1 xm:64:16:64"`——精确相等把一个完全正确的动作丢掉，报成
    「归因了但没有可施加的变异」，循环第 1 轮就停。这是同一类问题的第三个
    变体：先是字段名，然后是值的装饰。
    """
    state = _LoopState(candidate_index=0,
                       labels=("xm:32:4:64", "xm:64:16:64", "xm:32:32:64"))
    advanced, why = state.apply(
        _critique(_mutation(Layer.KERNEL, "candidate", value)), None)
    assert advanced, why
    assert state.candidate_index == expected


def test_a_value_naming_nothing_still_refuses():
    """宽容不等于乱猜：认不出目标就不前进——换错候选会让下一轮的测量对不上
    归因的预期，那种错很难从结果里看出来。"""
    state = _LoopState(candidate_index=0, labels=("xm:32:4:64", "xm:64:16:64"))
    advanced, why = state.apply(
        _critique(_mutation(Layer.KERNEL, "candidate", "something better")), None)
    assert not advanced and "no mutation to act on" in why
