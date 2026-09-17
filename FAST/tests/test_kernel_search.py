"""The Kernel Agent spends a measurement budget; the proposer only suggests.

These tests pin the boundary that makes the rule-vs-LLM comparison meaningful:
the agent owns measurement, the epsilon gate and the frontier, and a proposer
can never smuggle a configuration past the search space.
"""

from __future__ import annotations

import pytest

from fast.agents.kernel import KernelAgent, pareto_front
from fast.agents.proposers import LLMProposer, SweepProposer
from fast.schemas.models import (
    Budget,
    ExperimentSpec,
    KernelCandidate,
    KernelMeasurement,
    KernelSearchSpace,
    Status,
)


def _spec(budget: int = 6, epsilon: float = 0.05) -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="kernel-search-test",
        candidate_id="unit",
        model="tiny",
        dataset="wikitext-2-raw-v1",
        sequence_length=512,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=epsilon,
        seed=1,
        budget=Budget(max_candidates=budget, max_evaluations=budget, max_wall_seconds=60),
    )


def _measurement(label, loss, sparsity, occupancy=0.4, by="test"):
    return KernelMeasurement(
        label=label, status=Status.PASSED, perplexity=10 * (1 + loss),
        quality_loss=loss, actual_sparsity=sparsity, index_entropy=0.9,
        block_occupancy=occupancy, row_kept_min=8, row_kept_max=16,
        wall_seconds=1.0, proposed_by=by,
    )


class FakeAdapter:
    """Measures a label from a fixed table; records the batches it was given."""

    def __init__(self, table=None):
        self.table = table or {}
        self.batches: list[tuple[str, ...]] = []

    def measure(self, spec, candidates):
        self.batches.append(tuple(item.label for item in candidates))
        out = []
        for candidate in candidates:
            loss, sparsity = self.table.get(candidate.label, (0.02, 0.80))
            out.append(_measurement(candidate.label, loss, sparsity, by=candidate.proposed_by))
        return tuple(out), 10.0

    def evaluate(self, spec):  # unused here
        raise NotImplementedError


class ScriptedLLM:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts: list[str] = []

    def prompt(self, user_message, tools=None):
        self.prompts.append(user_message)
        text = self.replies.pop(0) if self.replies else "[]"
        if isinstance(text, Exception):
            raise text

        class R:
            result = text
            success = True
            stderr = ""

        return R()


# --- the space -------------------------------------------------------------

def test_the_space_never_offers_a_low_budget_above_the_high_one():
    """X:M keeps `high` in dense blocks and `low` in sparse ones; low > high is
    not a configuration, it is a typo."""
    for label in KernelSearchSpace().labels():
        if label.startswith("xm:"):
            _, high, low, block = label.split(":")
            assert int(low) <= int(high) <= int(block)


def test_topk_never_exceeds_the_sequence_length():
    space = KernelSearchSpace(max_sequence_length=64)

    for label in space.labels():
        if label.startswith("topk:"):
            assert int(label.split(":")[1]) <= 64


# --- the agent -------------------------------------------------------------

def test_the_search_stops_at_the_measurement_budget():
    adapter = FakeAdapter()
    report = KernelAgent(adapter).search(_spec(budget=5), batch=2)

    assert len(report.measurements) == 5
    assert sum(len(batch) for batch in adapter.batches) == 5


def test_a_round_is_measured_in_one_batch():
    """Loading the model dominates the cost, so rounds must not be split up."""
    adapter = FakeAdapter()
    KernelAgent(adapter).search(_spec(budget=4), batch=4)

    assert adapter.batches[0] == tuple(sorted(adapter.batches[0], key=adapter.batches[0].index))
    assert len(adapter.batches[0]) == 4


def test_only_configurations_inside_epsilon_can_be_best():
    adapter = FakeAdapter({
        "a": (0.20, 0.99),   # sparsest, but far outside the budget
        "b": (0.01, 0.80),
    })
    agent = KernelAgent(adapter)

    class Fixed:
        name = "fixed"

        def propose(self, spec, space, history, count):
            remaining = [l for l in ("a", "b") if l not in {m.label for m in history}]
            return tuple(KernelCandidate(label=l, proposed_by="fixed") for l in remaining[:count])

    report = agent.search(_spec(budget=2, epsilon=0.05), proposer=Fixed(), batch=2)

    assert report.best is not None
    assert report.best.label == "b"


def test_a_budget_of_zero_measurements_is_rejected_at_construction():
    """The invariant belongs to Budget, so the agent needs no second guard."""
    with pytest.raises(ValueError, match="must be positive"):
        _spec(budget=0)


def test_the_frontier_excludes_dominated_and_failed_configurations():
    history = (
        _measurement("sparse", 0.10, 0.95),
        _measurement("cheap", 0.01, 0.80),
        _measurement("dominated", 0.05, 0.70),
        KernelMeasurement(
            label="broken", status=Status.FAILED, perplexity=None, quality_loss=None,
            actual_sparsity=0.0, index_entropy=0.0, block_occupancy=0.0,
            row_kept_min=None, row_kept_max=None, wall_seconds=None, error="boom",
        ),
    )

    assert set(pareto_front(history)) == {"sparse", "cheap"}


def test_measurements_carry_the_proposer_that_asked_for_them():
    report = KernelAgent(FakeAdapter()).search(_spec(budget=2), batch=2)

    assert {item.proposed_by for item in report.measurements} == {"sweep"}
    assert report.proposer == "sweep"


# --- the proposers ---------------------------------------------------------

def test_the_sweep_never_repeats_a_measured_configuration():
    adapter = FakeAdapter()
    report = KernelAgent(adapter).search(_spec(budget=8), batch=2)

    labels = [item.label for item in report.measurements]
    assert len(labels) == len(set(labels))


def test_the_sweep_cites_the_frontier_it_is_bisecting():
    space = KernelSearchSpace(max_sequence_length=512)
    history = (_measurement("xm:32:16:64", 0.02, 0.84), _measurement("xm:8:4:64", 0.30, 0.96))

    proposed = SweepProposer().propose(_spec(), space, history, 1)

    assert proposed
    assert any("xm:32:16:64" in line for line in proposed[0].rationale)


def test_the_llm_may_not_invent_a_configuration():
    space = KernelSearchSpace(max_sequence_length=512)
    llm = ScriptedLLM('[{"label": "xm:999:1:64", "rationale": ["made up"]}]')
    proposer = LLMProposer(llm, model_name="scripted", fallback=SweepProposer())

    proposed = proposer.propose(_spec(), space, (), 1)

    assert proposed[0].proposed_by == "sweep"          # fell back
    assert any("outside the search space" in note for note in proposer.rejected)


def test_the_llm_may_not_re_measure_what_is_already_known():
    space = KernelSearchSpace(max_sequence_length=512)
    history = (_measurement("xm:32:16:64", 0.02, 0.84),)
    llm = ScriptedLLM('[{"label": "xm:32:16:64", "rationale": ["again"]}]')
    proposer = LLMProposer(llm, model_name="scripted", fallback=SweepProposer())

    proposer.propose(_spec(), space, history, 1)

    assert any("already measured" in note for note in proposer.rejected)


def test_a_fenced_reply_is_still_parsed():
    space = KernelSearchSpace(algorithm="topk", max_sequence_length=512)
    llm = ScriptedLLM('Sure!\n```json\n[{"label": "topk:64", "rationale": ["unmeasured"]}]\n```')
    proposer = LLMProposer(llm, model_name="scripted")

    proposed = proposer.propose(_spec(), space, (), 1)

    assert [item.label for item in proposed] == ["topk:64"]
    assert proposed[0].proposed_by == "llm:scripted"


def test_an_llm_outage_does_not_end_the_search():
    space = KernelSearchSpace(max_sequence_length=512)
    llm = ScriptedLLM(RuntimeError("vertex is down"))
    proposer = LLMProposer(llm, model_name="scripted", fallback=SweepProposer())

    proposed = proposer.propose(_spec(), space, (), 2)

    assert len(proposed) == 2
    assert all(item.proposed_by == "sweep" for item in proposed)
    assert any("llm call failed" in note for note in proposer.rejected)


def test_the_prompt_shows_the_hardware_metrics_not_just_accuracy():
    """Block occupancy is the whole point of the kernel/uarch conversation; a
    proposer that never sees it cannot reason about it."""
    space = KernelSearchSpace(max_sequence_length=512)
    llm = ScriptedLLM("[]")
    LLMProposer(llm, model_name="scripted").propose(
        _spec(), space, (_measurement("xm:32:16:64", 0.02, 0.84, occupancy=0.41),), 1
    )

    prompt = llm.prompts[0]
    assert "block_occupancy" in prompt
    assert "0.4100" in prompt
    assert "xm:32:16:64" in prompt


# --- the sparse-index profile (proposal Table II: Kernel outputs) ------------

def test_the_profile_separates_balanced_from_skewed_load():
    """PE underutilisation is the problem the proposal opens with, so the number
    that expresses it must survive into the typed output."""
    from fast.schemas.models import KernelProfile

    balanced = KernelProfile(
        histogram_bins=4, row_density_histogram=(0, 8, 0, 0),
        block_density_histogram=(0, 8, 0, 0), load_imbalance=1.05,
        column_top1_mass=0.1, column_top5_mass=0.3, column_top10_mass=0.5,
    )
    skewed = KernelProfile(
        histogram_bins=4, row_density_histogram=(6, 0, 0, 2),
        block_density_histogram=(6, 0, 0, 2), load_imbalance=3.8,
        column_top1_mass=0.6, column_top5_mass=0.8, column_top10_mass=0.9,
    )

    assert balanced.balanced
    assert not skewed.balanced


def test_a_run_without_distribution_data_reports_no_profile():
    """None must mean "not measured", never a zero-filled profile that reads as
    a perfectly balanced workload."""
    from fast.adapters.dynax import _profile

    assert _profile({"mean_sparsity": 0.9}) is None
    assert _profile({
        "row_density_histogram": [1, 2], "block_density_histogram": [1, 2],
        "histogram_bins": 2, "mean_load_imbalance": 1.4,
        "column_top1_mass": 0.1, "column_top5_mass": 0.2, "column_top10_mass": 0.3,
        "per_layer_mean_kept_ratio": {"1": 0.2, "0": 0.1, "10": 0.3},
    }).per_layer_kept_ratio == (0.1, 0.2, 0.3)   # numeric order, not string order


# --- ranking from measurements, not from a hand-written prior ----------------

def test_ranking_interpolates_from_what_this_run_measured():
    from fast.agents.proposers import rank_by_measured_sparsity

    history = (
        _measurement("xm:8:4:64", 0.30, 0.956),
        _measurement("xm:32:16:64", 0.02, 0.836),
    )
    labels = ["xm:16:8:64", "xm:8:8:64"]

    # 0.90 sits between the two measured points, nearest the 12-per-block label.
    assert rank_by_measured_sparsity(labels, history, 0.90)[0] == "xm:16:8:64"


def test_an_unmeasured_family_is_explored_before_an_interpolated_guess():
    from fast.agents.proposers import rank_by_measured_sparsity

    history = (_measurement("xm:32:16:64", 0.02, 0.836),)

    ranked = rank_by_measured_sparsity(["xm:16:8:64", "nm:8:64"], history, 0.836)

    assert ranked[0] == "nm:8:64"


def test_ranking_never_claims_to_predict_absolute_sparsity():
    """The old prior guessed sparsity and was wrong by 0.35 on X:M; the
    replacement only orders, and orders using measured points."""
    from fast.agents.proposers import rank_by_measured_sparsity

    history = (_measurement("nm:8:64", 0.10, 0.875),)
    ranked = rank_by_measured_sparsity(["nm:4:64", "nm:16:64"], history, 0.875)

    # One measured point cannot distinguish them, so the order is stable, not invented.
    assert set(ranked) == {"nm:4:64", "nm:16:64"}


# --- search feeding the rest of the loop ------------------------------------

def test_the_winner_reaches_the_compiler_carrying_its_profile():
    """The proposal makes the sparse-index profile the Kernel Agent's output and
    the Compiler Agent's input, so it must survive the hand-off."""
    from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, TemplateRecord, UArchAgent
    from fast.adapters import DeterministicEvaluationAdapter
    from fast.orchestrator import FiveAgentFlow
    from fast.schemas.models import KernelProfile

    profile = KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
        block_density_histogram=(1, 1, 1, 1), load_imbalance=4.0,
        column_top1_mass=0.2, column_top5_mass=0.7, column_top10_mass=0.8,
    )

    class ProfiledAdapter(FakeAdapter):
        def measure(self, spec, candidates):
            measured, baseline = super().measure(spec, candidates)
            return tuple(
                KernelMeasurement(**{**m.__dict__, "profile": profile}) for m in measured
            ), baseline

    # planner 现在要在真注册表里查模板做可行性检查，所以用真的 id。
    template = TemplateRecord("repe_array", "sha256:t", "memory://t", True)
    flow = FiveAgentFlow(
        KernelAgent(ProfiledAdapter()),
        CompilerAgent(allow_unverified=True),
        UArchAgent((template,)),
        EvaluatorAgent(DeterministicEvaluationAdapter()), CriticAgent(),
    )

    search, report = flow.search_then_build(
        _spec(budget=2), template_id="repe_array", batch=2
    )

    assert report is not None
    # profile 一路带到规划里，这是它存在的理由。
    assert report.kernel.profile is profile
    # 报的是 tile 内的量（规划真正用的那个），同时也把全局量列出来对照。
    assert any("tile_load_imbalance=4.0000" in line for line in report.compiler.rationale)
    assert any("global_load_imbalance=4.0000" in line for line in report.compiler.rationale)
    # 列质量集中时，那些列会被 tile 里每一行重复读，值得只搬一次。
    assert "broadcast" in report.compiler.data_layout
    # 不均衡度 4.0 意味着利用率明显低于 1，规划要如实反映而不是假装满载。
    assert report.compiler.predicted_utilization < 1.0

    # 注：旧版本在这里断言「不均衡就窄化 lane」。那是个没有测量支撑的启发式
    # ——实测显示对付不均衡的手段是**工作队列**（`queue_depth` 的实测曲线），
    # 窄化 lane 只是少干活。这条断言随那个启发式一起去掉了。


def test_a_search_that_finds_nothing_inside_epsilon_builds_nothing():
    from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, TemplateRecord, UArchAgent
    from fast.adapters import DeterministicEvaluationAdapter
    from fast.orchestrator import FiveAgentFlow

    adapter = FakeAdapter()
    adapter.table = {}
    flow = FiveAgentFlow(
        KernelAgent(FakeAdapter({label: (0.5, 0.9) for label in
                                 KernelSearchSpace(max_sequence_length=512).labels()})),
        CompilerAgent(), UArchAgent((TemplateRecord("t", "d", "m", True),)),
        EvaluatorAgent(DeterministicEvaluationAdapter()), CriticAgent(),
    )

    search, report = flow.search_then_build(_spec(budget=2, epsilon=0.01), template_id="t", batch=2)

    assert search.best is None
    assert report is None


def test_the_planner_still_produces_a_plan_without_a_kernel_profile():
    """没有 profile 时利用率退回一个保守常数，规划照样要出得来。

    「模型没有说法」和「模型说错了」是两件事——退回值必须是保守的，而且
    要能在 rationale 里看出来它是退回来的。
    """
    from fast.agents import CompilerAgent
    from fast.schemas.models import KernelResult, Status as S

    kernel = KernelResult(
        status=S.PASSED, baseline_metric=10.0, candidate_metric=10.1,
        metric_name="ppl", quality_loss=0.01, actual_sparsity=0.86,
        index_entropy=0.9, block_occupancy=0.42, trace_uri="x", profile=None,
    )

    plan = CompilerAgent(allow_unverified=True).plan(kernel, sequence_length=512)

    assert plan.status is S.PASSED
    assert plan.num_rows > 0 and plan.pe_per_row > 0
    assert plan.predicted_clock_ns is not None


def test_a_search_records_measurements_and_rejections_to_the_shared_db(tmp_path):
    from fast.storage import ExperimentDB

    db = ExperimentDB(tmp_path / "shared.db")
    report = KernelAgent(FakeAdapter()).search(_spec(budget=4), batch=2, db=db)

    rows = db.cross_layer()
    assert {row["label"] for row in rows} == {m.label for m in report.measurements}
    assert all(row["load_imbalance"] is None for row in rows)  # FakeAdapter has no profile
