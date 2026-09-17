"""Behavioural checks for the fixed-task energy/latency research objective."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from fast.agents.codesign import DEFAULT_OBJECTIVE, DesignObjectives, dominates, estimate
from fast.agents.cooptimizer import CoDesignResult, _frontier
from fast.agents.pareto import extends_frontier, frontier_vectors, hypervolume_2d
from fast.orchestrator.flow import _LoopState
from fast.schemas.models import Status


def test_energy_is_power_integrated_over_task_time():
    # 500 mW for 2 ms = 1 mJ, efficiency = 1000 completed tasks/J.
    p = DesignObjectives(2e6, 500.0, 100.0, None)
    assert p.energy_j == pytest.approx(0.001)
    assert p.energy_efficiency_tasks_per_j == pytest.approx(1000)


def test_lower_power_does_not_imply_lower_energy():
    fast = DesignObjectives(1e6, 500.0, 200.0, None)
    slow = DesignObjectives(4e6, 200.0, 100.0, None)
    assert dominates(fast, slow)  # area is a constraint, not an objective


def test_slower_but_lower_energy_design_survives():
    points = [(1.0, 4.0), (2.0, 2.0), (3.0, 3.0)]
    assert frontier_vectors(points) == ((1.0, 4.0), (2.0, 2.0))
    assert extends_frontier([(1.0, 4.0)], (2.0, 2.0), .02)


@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), -1, 0])
def test_missing_or_invalid_energy_cannot_dominate(invalid):
    assert not DEFAULT_OBJECTIVE.dominates(
        {"seconds": 1, "energy_j": invalid}, {"seconds": 2, "energy_j": 3})


def test_fixed_reference_hypervolume_counts_union_once():
    assert hypervolume_2d([(1, 4), (2, 2), (3, 3), (1, 4)], (5, 5)) == 10


def test_inner_front_uses_seconds_and_energy_not_cycles_or_area():
    def result(seconds, energy, cycles, area, feasible=True):
        return CoDesignResult(None, None, None, {
            "seconds": seconds, "energy_j": energy, "cycles": cycles, "area": area
        }, feasible)
    a, b = result(1, 4, 100, 100), result(2, 2, 200, 200)
    c = result(.1, .1, 1, 1, False)
    assert _frontier([a, b, c]) == (a, b)


def test_energy_only_progress_keeps_outer_loop_alive():
    from fast.schemas.models import Critique, Decision, Layer
    critique = Critique(Status.PASSED, Layer.UARCH, Decision.CONTINUE, "same",
                        evidence=("energy",))
    state = _LoopState(0)
    for power in [800, 600, 400, 200]:
        report = SimpleNamespace(
            compiler=SimpleNamespace(predicted_cycles=1000, predicted_clock_ns=2,
                                     predicted_power_mw=power),
            evaluation=SimpleNamespace(fidelity="L2-rtl-simulation", functional_passed=True),
            mutation=None)
        assert not state._converged(critique, report)
    assert len(state.objective_front) == 1


def test_estimator_uses_si_energy_and_retains_coverage():
    from test_work_conservation import _point, _kernel
    metrics = estimate(_point(), _kernel(), 512, head_dim=64)
    assert metrics["energy_j"] == pytest.approx(metrics["power"] * 1e-3 * metrics["seconds"])
    assert metrics["edp"] == pytest.approx(metrics["energy_j"] * metrics["seconds"])
    assert metrics["energy_scope"].startswith("partial-model")


@pytest.mark.parametrize("field", ["area_um2", "clock_ns", "power_mw"])
@pytest.mark.parametrize("value", [None, float("nan"), 0])
def test_active_constraints_require_valid_evidence(field, value):
    from fast.agents.codesign import constraint_violations
    from fast.schemas.models import ArchSpecs
    point = DesignObjectives(1000, 500, 1000, None, 2)
    point = replace(point, **{field: value})
    violations = constraint_violations(point, ArchSpecs(max_power_mw=1000))
    assert any("feasibility unverified" in reason for reason in violations)
