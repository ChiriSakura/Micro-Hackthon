from __future__ import annotations

from dataclasses import replace

import pytest

from fast.adapters import DeterministicEvaluationAdapter, DeterministicKernelAdapter
from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, TemplateRecord, UArchAgent
from fast.orchestrator import FiveAgentFlow
from fast.schemas.models import Budget, Decision, ExperimentSpec, Layer, Status
from fast.storage import ExperimentStore


def spec(**changes) -> ExperimentSpec:
    base = ExperimentSpec(
        experiment_id="test",
        candidate_id="x8-m64",
        model="tiny-llama",
        dataset="wikitext-2-raw-v1",
        sequence_length=64,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=0.01,
        seed=20260903,
        budget=Budget(),
    )
    return replace(base, **changes)


def flow(tmp_path, *, verified=True, kernel_adapter=None) -> FiveAgentFlow:
    template = TemplateRecord(
        "sparse-pe", "sha256:test", "memory://sparse-pe", verified
    )
    return FiveAgentFlow(
        KernelAgent(kernel_adapter or DeterministicKernelAdapter()),
        CompilerAgent(),
        UArchAgent((template,)),
        EvaluatorAgent(DeterministicEvaluationAdapter()),
        CriticAgent(),
        store=ExperimentStore(tmp_path / "fast.db"),
    )


def test_all_five_agents_complete_a_candidate(tmp_path):
    report = flow(tmp_path).run(spec(), template_id="sparse-pe")
    assert report.kernel.status is Status.PASSED
    assert report.compiler and report.compiler.status is Status.PASSED
    assert report.hardware and report.hardware.verified_template
    assert report.evaluation and report.evaluation.functional_passed
    assert report.critique.evidence


def test_unverified_template_is_blocked(tmp_path):
    report = flow(tmp_path, verified=False).run(spec(), template_id="sparse-pe")
    assert report.hardware and report.hardware.status is Status.FAILED
    assert report.evaluation and report.evaluation.status is Status.SKIPPED
    assert report.critique.attribution is Layer.UARCH
    assert report.critique.decision is Decision.REVERT


def test_quality_gate_stops_downstream_work(tmp_path):
    report = flow(tmp_path).run(spec(epsilon=0.001), template_id="sparse-pe")
    assert report.kernel.status is Status.FAILED
    assert report.compiler and report.compiler.status is Status.SKIPPED
    assert report.critique.attribution is Layer.KERNEL


def test_complete_report_cache_avoids_expensive_rerun(tmp_path):
    class CountingAdapter(DeterministicKernelAdapter):
        def __init__(self):
            self.calls = 0

        def evaluate(self, experiment_spec):
            self.calls += 1
            return super().evaluate(experiment_spec)

    adapter = CountingAdapter()
    pipeline = flow(tmp_path, kernel_adapter=adapter)
    first = pipeline.run(spec(), template_id="sparse-pe")
    second = pipeline.run(spec(), template_id="sparse-pe")
    assert not first.cache_hits
    assert adapter.calls == 1
    assert second.cache_hits == ("kernel", "compiler", "uarch", "evaluator", "critic")


@pytest.mark.parametrize(
    "changes",
    [
        {"sequence_length": 0},
        {"sparsity_x": 0},
        {"sparsity_x": 65},
        {"epsilon": -0.1},
    ],
)
def test_invalid_experiment_specs_fail_closed(changes):
    with pytest.raises(ValueError):
        spec(**changes)
