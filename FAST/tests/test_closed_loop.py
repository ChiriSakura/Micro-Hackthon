"""kernel -> co-design -> evaluator -> critic, end to end.

The cases here are about what the loop must refuse and what it must record, not
about the numbers: with no RTL simulation built, the numbers are a model.
"""

from __future__ import annotations

import dataclasses

import pytest

from fast.adapters import AnalyticalEvaluationAdapter
from fast.agents import (
    CompilerAgent,
    CriticAgent,
    EvaluatorAgent,
    KernelAgent,
    TemplateRecord,
    UArchAgent,
)
from fast.agents.cooptimizer import CoOptimizer
from fast.agents.templates import DYNAX_TEMPLATES, TemplateRegistry
from fast.orchestrator import FiveAgentFlow
from fast.schemas.models import (
    Budget,
    ExperimentSpec,
    KernelProfile,
    KernelResult,
    Layer,
    Status,
)
from fast.storage import ExperimentDB


def _kernel(imbalance: float = 3.4) -> KernelResult:
    return KernelResult(
        status=Status.PASSED, baseline_metric=10.0, candidate_metric=10.24,
        metric_name="wiki_perplexity", quality_loss=0.024, actual_sparsity=0.8362,
        index_entropy=0.9372, block_occupancy=0.4175, trace_uri="x",
        profile=KernelProfile(
            histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
            block_density_histogram=(1, 1, 1, 1), load_imbalance=imbalance,
            column_top1_mass=0.2, column_top5_mass=0.4, column_top10_mass=0.6,
        ),
    )


def _spec() -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="loop", candidate_id="xm-32-16-64", model="tiny",
        dataset="wikitext-2-raw-v1", sequence_length=512, sparsity_x=16,
        sparsity_m=64, epsilon=0.05, seed=1,
        budget=Budget(max_candidates=1, max_evaluations=1, max_wall_seconds=60),
    )


def _verified_registry() -> TemplateRegistry:
    """The registry as it stands: repe_array now carries simulation evidence."""
    return TemplateRegistry()


def _flow(kernel: KernelResult, registry: TemplateRegistry,
          db: ExperimentDB | None = None, template_id: str = "repe_array"):
    class Fixed:
        def evaluate(self, spec):
            return kernel

    return FiveAgentFlow(
        KernelAgent(Fixed()), CompilerAgent(),
        # The real registry, not a stub: repe_array now carries simulation
        # evidence and prepe_array does not, so the gate is exercised against
        # the repository's actual state rather than a fixture's.
        UArchAgent(DYNAX_TEMPLATES),
        EvaluatorAgent(AnalyticalEvaluationAdapter(kernel=kernel, kept_per_block=16)),
        CriticAgent(), db=db,
        # The co-optimizer picks the template the report ends up carrying, so
        # it has to be told which one the test is about.
        cooptimizer=CoOptimizer(registry, template_id=template_id, allow_unverified=True),
    )


def test_an_unverified_template_stops_the_loop_at_the_uarch_layer():
    """Every DynaX template now carries simulation evidence, so the gate is
    exercised against a template that does not exist rather than one that is
    merely untested. The behaviour under test is unchanged: nothing without
    evidence may be presented as buildable hardware."""
    report = _flow(
        _kernel(), TemplateRegistry(), template_id="not-a-template"
    ).run(_spec(), template_id="not-a-template")

    assert report.hardware.status is Status.FAILED
    assert report.hardware.verified_template is False
    assert report.evaluation.status is Status.SKIPPED
    assert report.critique.attribution is Layer.UARCH


def test_a_model_never_reports_functional_correctness():
    """Only a simulation against golden vectors can, and none has run."""
    report = _flow(_kernel(), _verified_registry()).run(_spec(), template_id="repe_array")

    assert report.hardware.status is Status.PASSED
    assert report.evaluation.status is Status.PASSED
    assert report.evaluation.functional_passed is False
    assert "no RTL simulation" in report.evaluation.error
    assert report.critique.attribution is Layer.EVALUATOR


def test_the_evaluation_admits_it_shares_the_optimizer_model():
    """Agreement between a chooser and a scorer using one model is arithmetic,
    not confirmation; the Critic must be able to see that."""
    report = _flow(_kernel(), _verified_registry()).run(_spec(), template_id="repe_array")

    assert report.evaluation.fidelity == "L1-analytical-shared-model"
    assert any("NOT INDEPENDENT" in item for item in report.evaluation.evidence)


def test_the_joint_search_stops_when_rounds_stop_reducing_edp():
    """Table II gives the Compiler Agent "Reduction or timeout"."""
    flow = _flow(_kernel(), _verified_registry())
    flow.run(_spec(), template_id="repe_array")

    codesign = flow.last_codesign
    assert codesign.rounds >= 2
    assert "no EDP reduction" in codesign.stopped_because


def test_the_schedule_and_the_array_come_from_the_same_explored_point():
    """The point of joint search: these two are not decided independently."""
    flow = _flow(_kernel(), _verified_registry())
    report = flow.run(_spec(), template_id="repe_array")
    point = flow.last_codesign.best.point

    assert report.compiler.parallelism == point.parallelism
    assert report.hardware.pe_rows == point.num_rows
    assert report.hardware.pe_cols == point.pe_per_row
    assert report.hardware.queue_depth == point.queue_depth


def test_a_skewed_kernel_gets_a_deeper_queue_than_a_balanced_one():
    """The kernel profile reaches the hardware decision, which is the whole
    reason the profile is carried."""
    skewed = _flow(_kernel(imbalance=4.0), _verified_registry())
    skewed.run(_spec(), template_id="repe_array")
    balanced = _flow(_kernel(imbalance=1.0), _verified_registry())
    balanced.run(_spec(), template_id="repe_array")

    assert (skewed.last_codesign.best.point.queue_depth
            > balanced.last_codesign.best.point.queue_depth)


def test_every_layer_lands_in_one_joinable_row(tmp_path):
    """cross_layer starts from the kernel row, so a candidate that arrived
    through run() rather than a search still has to appear there."""
    db = ExperimentDB(tmp_path / "shared.db")
    _flow(_kernel(), _verified_registry(), db).run(_spec(), template_id="repe_array")

    rows = db.cross_layer()

    assert len(rows) == 1
    row = rows[0]
    assert row["label"] == "xm-32-16-64"
    assert row["load_imbalance"] == pytest.approx(3.4)
    assert row["compiler_parallelism"] is not None
    assert row["pe_rows"] is not None
    assert row["eval_pe_utilization"] is not None
    assert row["attribution"] == "evaluator"


def test_the_loop_still_runs_without_a_co_optimizer():
    """The sequential path stays available; joint search is opt-in."""
    kernel = _kernel()

    class Fixed:
        def evaluate(self, spec):
            return kernel

    from fast.adapters import DeterministicEvaluationAdapter

    flow = FiveAgentFlow(
        KernelAgent(Fixed()), CompilerAgent(),
        UArchAgent((TemplateRecord("t", "d", "m", True),)),
        EvaluatorAgent(DeterministicEvaluationAdapter()), CriticAgent(),
    )
    report = flow.run(_spec(), template_id="t")

    assert report.compiler.status is Status.PASSED
    assert report.hardware.status is Status.PASSED
