"""The L2 backend's contract: it reports what a simulation found, or nothing.

The point of this adapter is that it CAN disagree - unlike the analytical one,
which shares the co-optimizer's cost model and whose functional_passed is a
constant. So the tests that matter are the ones about disagreement surviving:
a mismatch must not become a passing result, an unbuildable module must not
become a passing result, and a template with no reference must be skipped rather
than assumed correct.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from fast.adapters.verilator import (
    DEFAULT_BENCHES,
    SimulationOutcome,
    TemplateBench,
    VerilatorEvaluationAdapter,
)
from fast.agents.templates import TemplateRegistry
from fast.schemas.models import EvaluationResult, ExperimentSpec, HardwareCandidate, Status


def _spec() -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="e", candidate_id="c", model="llama", dataset="wikitext",
        sequence_length=512, sparsity_x=8, sparsity_m=64, epsilon=0.02, seed=0,
    )


def _candidate(status: Status = Status.PASSED) -> HardwareCandidate:
    return HardwareCandidate(
        status=status, template_id="topk", template_digest="d",
        verified_template=True, pe_rows=32, pe_cols=4, queue_depth=0,
        sram_bytes=65536, data_width=16, manifest_uri="file://x",
        error=None if status is Status.PASSED else "gate failed",
    )


class _StubAdapter(VerilatorEvaluationAdapter):
    """Substitutes a recorded outcome for the Slurm round trip."""

    def __init__(self, outcome: SimulationOutcome, **kwargs) -> None:
        super().__init__(repo_root=Path("/nonexistent"), **kwargs)
        self._outcome = outcome
        self.calls = 0

    def simulate(self, bench: TemplateBench) -> SimulationOutcome:
        self.calls += 1
        return self._outcome


def test_a_clean_simulation_makes_functional_passed_a_measurement():
    adapter = _StubAdapter(SimulationOutcome(True, 0, 128, 4.0, "file:///run"))

    result = adapter.evaluate(
        _spec(), _candidate(), template=TemplateRegistry().by_id("topk")
    )

    assert result.status is Status.PASSED
    assert result.functional_passed is True
    assert result.fidelity == "L2-rtl-simulation"
    assert any("mismatches=0 across 128" in item for item in result.evidence)


def test_a_mismatch_fails_the_evaluation_rather_than_flagging_it():
    """A design whose arithmetic is wrong has no meaningful cycle count."""
    adapter = _StubAdapter(SimulationOutcome(False, 59, 128, 4.0, "file:///run"))

    result = adapter.evaluate(
        _spec(), _candidate(), template=TemplateRegistry().by_id("topk")
    )

    assert result.status is Status.FAILED
    assert result.functional_passed is False
    assert "59 functional mismatches" in result.error


def test_a_build_that_never_reached_the_simulator_is_not_a_pass():
    adapter = _StubAdapter(
        SimulationOutcome(False, -1, 0, 1.0, "", error="no simulation verdict: ...")
    )

    result = adapter.evaluate(
        _spec(), _candidate(), template=TemplateRegistry().by_id("topk")
    )

    assert result.status is Status.FAILED
    assert result.functional_passed is False
    assert result.cycles is None


def test_a_template_without_a_reference_is_skipped_not_assumed_correct():
    """Every DynaX template now has a bench, so this uses a record that does not.

    The behaviour is what matters and it has to survive the next template added:
    L2 reports what a simulation found, and where no simulation is possible it
    reports nothing rather than a pass.
    """
    adapter = _StubAdapter(SimulationOutcome(True, 0, 128, 4.0, ""))
    benchless = dataclasses.replace(
        TemplateRegistry().by_id("topk"), template_id="future-module"
    )

    result = adapter.evaluate(_spec(), _candidate(), template=benchless)

    assert result.status is Status.SKIPPED
    assert result.functional_passed is False
    assert "no golden testbench" in result.error
    assert adapter.calls == 0


def test_a_failed_hardware_candidate_is_never_simulated():
    adapter = _StubAdapter(SimulationOutcome(True, 0, 128, 4.0, ""))

    result = adapter.evaluate(
        _spec(), _candidate(Status.FAILED), template=TemplateRegistry().by_id("topk")
    )

    assert result.status is Status.SKIPPED
    assert adapter.calls == 0


def test_unsimulated_metrics_are_labelled_as_such():
    """An L2 badge must not imply cycles, area and power were simulated too."""
    adapter = _StubAdapter(SimulationOutcome(True, 0, 128, 4.0, ""))
    analytical = EvaluationResult(
        status=Status.PASSED, fidelity="L1-analytical", functional_passed=False,
        cycles=1234, throughput=5.0, pe_utilization=0.9, area=100.0,
        power=2.0, edp=42.0, wall_seconds=0.1, cloud_cost_usd=0.0,
        log_uri="", evidence=("model=L1-analytical (no RTL was simulated)",),
    )

    result = adapter.evaluate(
        _spec(), _candidate(), template=TemplateRegistry().by_id("topk"),
        analytical=analytical,
    )

    assert result.cycles == 1234
    assert any("NOT simulated" in item for item in result.evidence)
    # The analytical evidence travels along rather than being replaced.
    assert any("L1-analytical" in item for item in result.evidence)


def test_a_reconstructed_template_says_so_in_its_evidence():
    """exp_unit is FAST's own module; a result on it is not a DynaX result."""
    adapter = _StubAdapter(SimulationOutcome(True, 0, 116, 4.0, ""))

    result = adapter.evaluate(
        _spec(), _candidate(), template=TemplateRegistry().by_id("exp_unit")
    )

    assert any("fast-reconstruction" in item for item in result.evidence)


def test_every_bench_names_a_template_that_exists():
    """The bench table is a claim about what L2 can reach; it must stay true."""
    registry = TemplateRegistry()

    for template_id in DEFAULT_BENCHES:
        template = registry.by_id(template_id)
        assert template is not None, f"bench for unknown template {template_id}"
        # A bench exists because that module passed; the registry must agree.
        assert template.verified, f"{template_id} has a bench but is not verified"


def test_repeated_simulations_of_one_module_are_cached():
    """Elaboration is deterministic and the vectors are seeded."""
    adapter = VerilatorEvaluationAdapter(repo_root=Path("/nonexistent"))
    bench = DEFAULT_BENCHES["topk"]
    recorded = SimulationOutcome(True, 0, 128, 4.0, "")
    adapter._cache[(bench.elaborate_target, bench.top_module)] = recorded

    assert adapter.simulate(bench) is recorded
