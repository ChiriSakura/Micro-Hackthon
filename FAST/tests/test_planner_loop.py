"""重构后的架构：planner / implementer 分工，以及闭环。

三条主张，每条都对应一个曾经出过问题的地方：

  1. **planner 决定造什么，implementer 只负责造出来。** µArch 以前自己推
     `pe_rows = min(8, parallelism)`，于是「谁决定阵列是 32x4」没有唯一答案。
  2. **K 个候选是 Critic 在算法层的动作空间**，不是用来并行评估的。
  3. **循环停下来的原因必须是具体的。** 「跑完了」会让人以为搜索收敛了。
"""

from __future__ import annotations

import pytest

from fast.adapters.analytical import AnalyticalEvaluationAdapter
from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.agents.kernel import select_candidates
from fast.agents.templates import DYNAX_TEMPLATES, TemplateRegistry
from fast.agents.uarch import UArchAgent as _UArch
from fast.orchestrator import FiveAgentFlow
from fast.schemas.models import (
    Budget,
    CompilerSchedule,
    EvaluationResult,
    ExperimentSpec,
    KernelMeasurement,
    KernelProfile,
    KernelResult,
    Layer,
    Status,
)
from tests.test_kernel_search import FakeAdapter, _spec


def _seed_kernel(sparsity: float = 0.85) -> KernelResult:
    return KernelResult(
        status=Status.PASSED, baseline_metric=10.0, candidate_metric=10.1,
        metric_name="ppl", quality_loss=0.01, actual_sparsity=sparsity,
        index_entropy=0.9, block_occupancy=0.42, trace_uri="x",
    )


def _flow(**kwargs) -> FiveAgentFlow:
    registry = TemplateRegistry()
    return FiveAgentFlow(
        KernelAgent(FakeAdapter()),
        CompilerAgent(registry, allow_unverified=True),
        UArchAgent(DYNAX_TEMPLATES, registry=registry),
        EvaluatorAgent(AnalyticalEvaluationAdapter(kernel=_seed_kernel(), kept_per_block=16)),
        CriticAgent(),
        **kwargs,
    )


def _measurement(label: str, sparsity: float, loss: float) -> KernelMeasurement:
    return KernelMeasurement(
        label=label, status=Status.PASSED, perplexity=10.0 + loss,
        quality_loss=loss, actual_sparsity=sparsity, index_entropy=0.9,
        block_occupancy=0.4, row_kept_min=1.0, row_kept_max=16.0, wall_seconds=1.0,
    )


# --- 候选选择 ---------------------------------------------------------------

def test_candidates_cover_distinct_method_families():
    """三个候选全是 xm 变体的话，给 3 个和给 1 个没有区别——硬件代价一样。

    实测：8 bank 下 nm 1.19x、sanger 1.28x、topk 1.79x、xm 2.14x，跨度 2.17x，
    而族内差异远小于族间。所以族覆盖优先于稀疏度排名。
    """
    accepted = (
        _measurement("xm:64:32:64", 0.90, 0.030),
        _measurement("xm:32:16:64", 0.88, 0.020),
        _measurement("xm:16:8:64", 0.86, 0.015),
        _measurement("nm:16:64", 0.75, 0.007),
        _measurement("topk:64", 0.79, 0.012),
    )
    picked, shortfall = select_candidates(accepted, 3)

    assert shortfall is None
    assert {item.label.split(":")[0] for item in picked} == {"xm", "nm", "topk"}


def test_a_dominated_candidate_can_still_be_picked():
    """(稀疏度, 精度损失) 的 Pareto front **可能把真正的赢家排除掉**。

    nm 在两个轴上都被 xm 支配，但它的硬件代价是 1.19x 而 xm 是 2.58x——
    算上硬件它更快。所以候选从全部通过 epsilon 的点里挑，不限于 front。
    """
    dominant = _measurement("xm:32:16:64", 0.86, 0.018)
    dominated = _measurement("nm:16:64", 0.75, 0.020)
    picked, _ = select_candidates((dominant, dominated), 2)

    assert dominated in picked


def test_a_short_frontier_says_so_instead_of_padding():
    """凑进来的点会被下游当成「Kernel 认为值得一试」的东西。"""
    picked, shortfall = select_candidates((_measurement("xm:16:8:64", 0.86, 0.01),), 3)

    assert len(picked) == 1
    assert shortfall is not None and "1 of 3" in shortfall


def test_no_candidate_clears_epsilon():
    picked, shortfall = select_candidates((), 3)

    assert picked == ()
    assert "accuracy budget" in shortfall


# --- planner / implementer 分工 ---------------------------------------------

def test_the_implementer_takes_every_parameter_from_the_plan():
    """implementer 不该有「默认阵列形状」这种东西。"""
    registry = TemplateRegistry()
    plan = CompilerSchedule(
        status=Status.PASSED, tile_q=64, tile_k=64, tile_d=32,
        loop_order=("q", "k", "d"), data_layout="blocked-qkd", parallelism=8,
        predicted_utilization=0.9, predicted_bytes=4096,
        num_rows=32, pe_per_row=4, reg_width=8, data_width=16,
        sram_bytes=65_536, queue_depth=2, divider_stages=8, bank_count=8,
    )
    from fast.agents.uarch import TemplateRecord

    hardware = _UArch(
        (TemplateRecord("repe_array", "d", "uri", True),), registry=registry
    ).run(plan, template_id="repe_array")

    assert hardware.status is Status.PASSED
    assert (hardware.pe_rows, hardware.pe_cols) == (plan.num_rows, plan.pe_per_row)
    assert hardware.queue_depth == plan.queue_depth
    assert hardware.sram_bytes == plan.sram_bytes
    assert hardware.reg_width == plan.reg_width


def test_the_plan_carries_its_own_predictions():
    """预测值要跟着计划走，否则循环发现不了自己的代价模型错了。"""
    plan = CompilerAgent(allow_unverified=True).plan(
        _seed_kernel(), sequence_length=512, budget=8, batch=8
    )

    assert plan.status is Status.PASSED
    for field in ("predicted_cycles", "predicted_area_um2",
                  "predicted_power_mw", "predicted_clock_ns"):
        assert getattr(plan, field) is not None, field


def test_an_infeasible_plan_says_which_constraint_bound():
    """「失败了」不够——Critic 要靠具体的违反项决定是放宽约束还是换候选。"""
    from fast.schemas.models import ArchSpecs

    plan = CompilerAgent(allow_unverified=True).plan(
        _seed_kernel(), sequence_length=512,
        specs=ArchSpecs(max_area_um2=1.0), budget=4, batch=4,
    )

    assert plan.status is Status.SKIPPED
    assert "area" in plan.error


# --- 闭环 -------------------------------------------------------------------

def test_the_loop_reports_why_it_stopped():
    """停下来有很多种原因，它们的下一步完全不同。"""
    report = _flow().run_loop(
        _spec(budget=8), template_id="repe_array", rounds=3, candidates=3, batch=4
    )

    assert report.rounds
    assert report.stopped_because
    assert report.stopped_because != "exhausted 3 rounds" or len(report.rounds) == 3


def test_an_analytical_evaluation_never_claims_functional_correctness():
    """L1 从不跑 RTL，它的 functional_passed 恒为 False——那是「没检查」。

    当成「检查失败」会让循环在第 0 轮就以一个从未发生过的失败停下，
    而且指向错误的层。
    """
    report = _flow().run_loop(
        _spec(budget=8), template_id="repe_array", rounds=2, candidates=3, batch=4
    )
    last = report.last

    assert last is not None
    assert last.evaluation.functional_passed is False
    assert last.critique.attribution is not Layer.UARCH


def test_the_planner_model_gap_is_not_raised_against_a_shared_model():
    """拿一个模型和它自己比、然后断言模型错了，是循环论证。

    `L1-analytical-shared-model` 就是 planner 挑设计用的那同一个代价模型。
    """
    from fast.agents.critic import _planner_model_gap

    plan = CompilerSchedule(
        status=Status.PASSED, tile_q=64, tile_k=64, tile_d=32,
        loop_order=("q",), data_layout="blocked-qkd", parallelism=8,
        predicted_utilization=0.9, predicted_bytes=1, predicted_area_um2=1000.0,
    )
    shared = EvaluationResult(
        status=Status.PASSED, fidelity="L1-analytical-shared-model",
        functional_passed=False, cycles=None, throughput=None, pe_utilization=0.9,
        area=100_000.0, power=None, edp=None, wall_seconds=0.0, cloud_cost_usd=0.0,
        log_uri="",
    )
    verdict = _planner_model_gap(plan, shared)

    # 差 100 倍也不归因到模型标定——共用模型下的分歧是实现 bug。
    assert verdict is not None
    assert verdict.attribution is Layer.INFRASTRUCTURE


def test_a_real_measurement_that_misses_the_plan_blames_the_cost_model():
    """这一类错误此前全靠人发现：SRAM 面积系数小 40 倍、EDP 缺时钟周期、
    功耗是任意单位。共同形状是「没有任何东西会报错」。"""
    from fast.agents.critic import _planner_model_gap

    plan = CompilerSchedule(
        status=Status.PASSED, tile_q=64, tile_k=64, tile_d=32,
        loop_order=("q",), data_layout="blocked-qkd", parallelism=8,
        predicted_utilization=0.9, predicted_bytes=1, predicted_area_um2=26_214.0,
    )
    measured = EvaluationResult(
        status=Status.PASSED, fidelity="L2-synthesis-nangate45",
        functional_passed=True, cycles=None, throughput=None, pe_utilization=0.9,
        area=1_049_989.0, power=None, edp=None, wall_seconds=0.0, cloud_cost_usd=0.0,
        log_uri="",
    )
    verdict = _planner_model_gap(plan, measured)

    assert verdict is not None
    assert verdict.attribution is Layer.PLANNER_MODEL
    assert verdict.mutations[0].operation == "recalibrate"


# --- LLM 接入 ---------------------------------------------------------------

def test_the_strongest_model_is_the_default_for_reasoning_roles():
    """默认从 flash 换成 pro。

    flash 是最快最便宜的一档，不是最强的。提案的预算表里 Gemini API 是
    $700 / 约 70M tokens，是单项最大的一笔——用 flash 等于把预算留着不花
    却拿不到质量。
    """
    from fast.agents.llm_models import CHEAP, STRONGEST, model_for

    for role in ("kernel", "compiler", "critic", "uarch-mutate"):
        assert model_for(role).model == STRONGEST, role
    # 组合模板基本是查表，合法性由代码校验，模型只负责选。
    assert model_for("uarch-compose").model == CHEAP
    # 未知角色不该悄悄退到便宜那档：猜错方向的代价是产出质量，不是账单。
    assert model_for("something-new").model == STRONGEST


def test_writing_rtl_is_deterministic():
    """内循环的「连续两次同类失败」判据要求同一个症状得到同一个修复。"""
    from fast.agents.llm_models import model_for

    assert model_for("uarch-mutate").temperature == 0.0


def test_an_out_of_space_field_is_rejected_by_name():
    """协同设计空间枚举不出来，所以校验逐字段做——拒绝理由要指到具体字段，
    模型下一轮才能改对地方。只说「非法」它只会重猜。"""
    from fast.agents.codesign import CoDesignSpace
    from fast.agents.plan_proposers import LLMPlanProposer
    from fast.schemas.models import ArchSpecs

    class Bad:
        def prompt(self, text):
            class R:
                result = '[{"tile_q":64,"tile_k":64,"tile_d":64,"parallelism":8,' \
                         '"double_buffer":false,"num_rows":7,"pe_per_row":4,' \
                         '"reg_width":16,"data_width":16,"sram_bytes":65536,' \
                         '"queue_depth":2,"divider_stages":8,"bank_count":8}]'
                success = True
            return R()

    proposer = LLMPlanProposer(Bad(), model_name="test")
    proposer.propose(_seed_kernel(), ArchSpecs(), CoDesignSpace(), (), 1)

    assert any("num_rows=7" in note for note in proposer.rejected)


def test_a_proposer_outage_falls_back_instead_of_ending_the_search():
    """proposer 挂掉不能让整个搜索结束——它只负责建议。"""
    from fast.agents.codesign import CoDesignSpace
    from fast.agents.plan_proposers import LLMPlanProposer
    from fast.schemas.models import ArchSpecs

    class Dead:
        def prompt(self, text):
            raise RuntimeError("vertex unavailable")

    proposer = LLMPlanProposer(Dead(), model_name="test")
    points = proposer.propose(_seed_kernel(), ArchSpecs(), CoDesignSpace(), (), 2)

    assert points, "回落必须给出候选，否则一次网络抖动就终结了整轮搜索"
    assert any("llm call failed" in note for note in proposer.rejected)


# --- 分层重入 ---------------------------------------------------------------

def _critique(layer: Layer, field_name: str, value=0):
    from fast.schemas.models import Critique, Decision, Mutation

    return Critique(
        status=Status.PASSED, attribution=layer, decision=Decision.CONTINUE,
        summary=f"attributed to {layer.value}", evidence=("x",),
        mutations=(Mutation(layer=layer, field=field_name, operation="switch",
                            value=value, expected_effect="a checkable target",
                            risk="none"),),
    )


def test_a_uarch_attribution_keeps_the_plan():
    """归因到 µArch 却顺带重新规划，下一轮就分不清改善来自 RTL 修复还是
    来自新计划——「一轮只变一层」失效。"""
    from fast.orchestrator.flow import _LoopState

    state = _LoopState(candidate_index=0, plan=object(), hardware=object())
    advanced, _ = state.apply(_critique(Layer.UARCH, "block_scheduler"), None)

    assert advanced
    assert state.replan is False        # 计划不动
    assert state.reimplement is True    # 只重新实现


def test_a_compiler_attribution_replans_but_keeps_the_candidate():
    from fast.orchestrator.flow import _LoopState

    state = _LoopState(candidate_index=1, plan=object(), hardware=object())
    advanced, _ = state.apply(_critique(Layer.COMPILER, "queue_depth"), None)

    assert advanced and state.replan is True
    assert state.candidate_index == 1


def test_switching_the_candidate_forces_a_replan():
    """换了工作负载，计划必须跟着重来——同一份硬件对不同稀疏度不是同一个取舍。"""
    from fast.orchestrator.flow import _LoopState

    state = _LoopState(candidate_index=0, plan=object(), hardware=object())
    advanced, _ = state.apply(_critique(Layer.KERNEL, "candidate_index", 2), None)

    assert advanced
    assert state.candidate_index == 2
    assert state.replan is True and state.hardware is not None  # 由 _round 清掉


def test_an_evaluator_attribution_changes_neither_plan_nor_hardware():
    """只升级保真度：计划和硬件都是同一个，测的才是同一个东西。"""
    from fast.orchestrator.flow import _LoopState

    state = _LoopState(candidate_index=0, plan=object(), hardware=object())
    advanced, _ = state.apply(_critique(Layer.EVALUATOR, "fidelity"), None)

    assert advanced
    assert state.replan is False and state.reimplement is False


def test_a_critique_without_a_mutation_stops_the_loop():
    """没有可执行的变异就不该假装还在前进。"""
    from fast.orchestrator.flow import _LoopState
    from fast.schemas.models import Critique, Decision

    state = _LoopState(candidate_index=0)
    # schema 要求至少一条证据，所以「没有变异」不等于「没有证据」。
    empty = Critique(status=Status.PASSED, attribution=Layer.COMPILER,
                     decision=Decision.CONTINUE, summary="no idea",
                     evidence=("evaluation.cycles",))
    advanced, why = state.apply(empty, None)

    assert not advanced and "no mutation" in why


# --- RTL 变异 ---------------------------------------------------------------

def test_touching_the_golden_model_kills_the_mutation_outright(tmp_path):
    """**唯一真正危险的失败模式**：Agent 改金标准让自己的 RTL 通过。

    内循环让这个风险变高，因为失败会反复回喂，而「让测试通过」是模型最自然
    会走的捷径。容忍一次就等于容忍。
    """
    from fast.agents.rtl_mutation import GateResult, RtlMutator

    module = tmp_path / "m.scala"
    module.write_text("original", encoding="utf-8")
    golden = tmp_path / "golden.py"
    golden.write_text("reference", encoding="utf-8")

    class Cheater:
        def prompt(self, text):
            golden.write_text("reference that always passes", encoding="utf-8")
            class R: result = "mutated"; success = True
            return R()

    class AlwaysPasses:
        def check(self, path, target):
            return (GateResult("simulate", True, "ok"),)

    outcome = RtlMutator(
        Cheater(), AlwaysPasses(), attempts=3, protected=(golden,)
    ).mutate(module, "M", symptom="s", target="t")

    assert not outcome.accepted
    assert "read-only" in outcome.reason
    assert module.read_text(encoding="utf-8") == "original"


def test_a_failing_mutation_restores_the_original(tmp_path):
    """次数用完要回退到未变异的版本，流水线继续跑——变异失败不该中断链路。"""
    from fast.agents.rtl_mutation import GateResult, RtlMutator

    module = tmp_path / "m.scala"
    module.write_text("original", encoding="utf-8")

    class Model:
        def prompt(self, text):
            class R: result = "broken"; success = True
            return R()

    class AlwaysFails:
        def check(self, path, target):
            return (GateResult("elaborate", False, "m.scala:12: type mismatch"),)

    outcome = RtlMutator(Model(), AlwaysFails(), attempts=2).mutate(
        module, "M", symptom="s", target="t"
    )

    assert not outcome.accepted and outcome.attempts == 2
    assert module.read_text(encoding="utf-8") == "original"
    assert "type mismatch" in outcome.diagnostics


def test_the_failure_is_fed_back_to_the_next_attempt(tmp_path):
    """诊断信息的质量决定内循环能不能收敛。只输出 FAILED 会让它退化成盲目重试。"""
    from fast.agents.rtl_mutation import GateResult, RtlMutator

    module = tmp_path / "m.scala"
    module.write_text("original", encoding="utf-8")
    prompts: list[str] = []

    class Model:
        def prompt(self, text):
            prompts.append(text)
            class R: result = "attempt"; success = True
            return R()

    class Fails:
        def check(self, path, target):
            return (GateResult("simulate", False, "slot 4: got 0x00FF, want 0x013E"),)

    RtlMutator(Model(), Fails(), attempts=2).mutate(module, "M", symptom="s", target="t")

    assert len(prompts) == 2
    assert "got 0x00FF, want 0x013E" in prompts[1]


# --- LLM Critic -------------------------------------------------------------

def test_a_mutation_without_a_checkable_target_is_rejected():
    """派发变异时说「让它更快」是没用的——内循环判不出自己成功了没有。

    XOR 散列通过了全部的门却是负收益；没有可检验目标它会被当成成功。
    """
    from fast.agents.llm_critic import LLMCriticAgent

    critic = LLMCriticAgent(object(), model_name="test")
    assert critic._as_mutation({"layer": "uarch", "field": "x", "operation": "rewrite"}) is None
    assert any("expected_effect" in note for note in critic.rejected)


def test_an_unknown_layer_is_rejected_by_name():
    from fast.agents.llm_critic import LLMCriticAgent

    critic = LLMCriticAgent(object(), model_name="test")
    verdict = critic._parse('{"attribution":"magic","decision":"continue","summary":"x"}')

    assert verdict is None
    assert any("magic" in note for note in critic.rejected)


def test_a_critique_with_no_evidence_falls_back_instead_of_crashing():
    """一次幻觉的代价应该是「回落到规则版」，不是「整轮崩掉」。"""
    from fast.agents.llm_critic import LLMCriticAgent

    critic = LLMCriticAgent(object(), model_name="test")
    verdict = critic._parse(
        '{"attribution":"compiler","decision":"continue","summary":"x","evidence":[]}'
    )

    assert verdict is None
    assert any("no evidence" in note for note in critic.rejected)


# --- 逐模块对话 -------------------------------------------------------------

def _fake_gate(results_by_module):
    from fast.agents.rtl_mutation import GateResult

    class Gate:
        def check(self, path, target):
            return results_by_module.get(target, (GateResult("synthesize", True, "ok", {"area_um2": 1000.0}),))
    return Gate()


def test_the_dialogue_stops_at_the_first_failing_module(tmp_path):
    """失败的模块不继续往下造：后面的模块依赖它，用一个已知坏掉的模块去
    验证上层，得到的失败无法归因。"""
    from fast.agents.module_dialogue import ModuleDialogue
    from fast.agents.rtl_mutation import GateResult

    source = tmp_path / "src"
    source.mkdir()
    (source / "all.scala").write_text(
        "\n".join(f"class {name}(" for name in
                  ("ExpUnitFixPoint", "PSumSoftmax", "TopK", "SRAM", "PrePE_1_2",
                   "RePE", "RePERow", "PrePEArray_1_2", "PrePEArray_1_4", "RePEArray")),
        encoding="utf-8",
    )
    gate = _fake_gate({"TopK": (GateResult("simulate", False, "ramp FAIL (0/16 lanes)"),)})

    report = ModuleDialogue(gate, source_root=source).build(None, area_budget_um2=1e9)

    # ExpUnit, PSumSoftmax 过了，TopK 挂了，后面的一个都不造。
    assert [item.module for item in report.outcomes] == ["ExpUnit", "PSumSoftmax", "TopK"]
    assert not report.complete
    assert any("TopK did not pass" in c for c in report.discovered_constraints)


def test_the_budget_is_spent_module_by_module(tmp_path):
    """一次造完的话面积只能最后统一检查，超了就整个计划作废。逐模块分摊
    则是造到哪算到哪，超了立刻停。"""
    from fast.agents.module_dialogue import ModuleDialogue

    source = tmp_path / "src"
    source.mkdir()
    (source / "all.scala").write_text(
        "\n".join(f"class {name}(" for name in
                  ("ExpUnitFixPoint", "PSumSoftmax", "TopK", "SRAM", "PrePE_1_2",
                   "RePE", "RePERow", "PrePEArray_1_2", "PrePEArray_1_4", "RePEArray")),
        encoding="utf-8",
    )
    # 每个模块 1000 um^2，预算只够 3 个。
    report = ModuleDialogue(_fake_gate({}), source_root=source).build(
        None, area_budget_um2=2500.0
    )

    assert len(report.outcomes) == 3
    assert report.area_spent_um2 == 3000.0
    assert any("area budget exhausted" in c for c in report.discovered_constraints)
    assert not report.complete


def test_mutation_only_happens_for_modules_the_critic_named(tmp_path):
    """常规搜索只组合，变异由 Critic 触发——这条要**结构上**保证，
    不靠调用方自觉。"""
    from fast.agents.module_dialogue import ModuleDialogue
    from fast.agents.rtl_mutation import GateResult

    source = tmp_path / "src"
    source.mkdir()
    (source / "all.scala").write_text("class ExpUnitFixPoint(\n", encoding="utf-8")
    called: list[str] = []

    class Mutator:
        def mutate(self, path, target, *, symptom, target_):
            called.append(target)
            raise AssertionError("should not be reached")

        def __call__(self, *a, **k):
            raise AssertionError

    class Recording:
        def mutate(self, path, module, **kwargs):
            called.append(module)
            from fast.agents.rtl_mutation import MutationOutcome
            return MutationOutcome(module, False, 1, None, (), "no")

    gate = _fake_gate({"ExpUnit": (GateResult("simulate", False, "boom"),)})
    dialogue = ModuleDialogue(gate, source_root=source, mutator=Recording(),
                              order=("ExpUnit",))

    dialogue.build(None, area_budget_um2=1e9, symptom="slow")
    assert called == [], "没被 Critic 点名就不该变异"

    dialogue.build(None, area_budget_um2=1e9, symptom="slow", mutate_only=("ExpUnit",))
    assert called == ["ExpUnit"]


def test_the_build_order_puts_the_smallest_module_first():
    """一个 PE 的数据通路 bug 在 512 个 PE 的阵列里会以完全无法诊断的形式
    出现——`Elaborate.scala` 的注释就是这么写的。"""
    from fast.agents.module_dialogue import BUILD_ORDER

    assert BUILD_ORDER.index("PrePE_1_2") < BUILD_ORDER.index("PrePEArray_T")
    assert BUILD_ORDER.index("RePE") < BUILD_ORDER.index("RePERow")
    assert BUILD_ORDER.index("RePERow") < BUILD_ORDER.index("RePEArray_T")
    # 5/8 个 DynaX 源文件 import ExpUnit，它必须最先。
    assert BUILD_ORDER[0] == "ExpUnit"
