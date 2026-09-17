"""Protect configuration identity and traffic units at the shared boundaries."""
from dataclasses import replace

import pytest

from fast.agents.codesign import CoDesignPoint, to_schedule, working_set_bytes
from fast.agents.compiler import _as_plan
from fast.agents.cooptimizer import CoDesignResult
from fast.cli import load_spec
from fast.schemas.conversions import (
    algorithm_parameters,
    kernel_result_from_measurement,
    measurement_from_kernel_result,
)
from fast.schemas.models import KernelMeasurement, KernelSearchReport, Status


def measurement():
    return KernelMeasurement(
        label="xm:16:8:32:0.75:0.05", status=Status.PASSED,
        perplexity=10.1, quality_loss=0.01, actual_sparsity=0.7,
        index_entropy=0.9, block_occupancy=0.4, row_kept_min=0,
        row_kept_max=16, wall_seconds=2.0, proposed_by="random-kernel",
    )


def test_replay_preserves_algorithm_identity_and_marks_missing_search_context():
    measured = measurement()
    kernel = kernel_result_from_measurement(None, measured)
    assert kernel.sparse_method == measured.label
    assert algorithm_parameters(kernel) == {"block_m": 32, "kept_per_block": 16}
    assert kernel.baseline_metric == 0.0
    assert kernel.trace_uri == f"measurement://{measured.label}"
    assert "no search report: selection context unavailable" in kernel.evidence
    row = measurement_from_kernel_result(measured.label, kernel)
    assert (row.perplexity, row.quality_loss, row.actual_sparsity) == (
        measured.perplexity, measured.quality_loss, measured.actual_sparsity)
    # These per-measurement timings/ranges are absent from KernelResult.
    assert row.wall_seconds is None and row.row_kept_max is None


def test_search_conversion_keeps_baseline_and_selected_candidate_provenance():
    first = measurement()
    selected = replace(first, label="nm:8:32", proposed_by="sweep")
    spec = load_spec(None)
    search = KernelSearchReport(
        spec=spec, proposer="sweep", baseline_metric=10.0,
        measurements=(first, selected), pareto=(first.label, selected.label),
        best=first, rounds=1,
    )
    assert kernel_result_from_measurement(search).sparse_method == first.label
    kernel = kernel_result_from_measurement(search, selected)
    assert kernel.sparse_method == selected.label
    assert kernel.baseline_metric == 10.0
    assert kernel.trace_uri == f"search://{spec.experiment_id}/{selected.label}"
    assert "proposed_by=sweep" in kernel.evidence


def test_conversion_requires_an_actual_measurement():
    with pytest.raises(ValueError, match="no measurement"):
        kernel_result_from_measurement(None)


def test_compiler_export_preserves_nondefault_hardware_and_total_traffic():
    point = CoDesignPoint(
        tile_q=32, tile_k=32, tile_d=64, parallelism=8,
        double_buffer=False, num_rows=16, pe_per_row=8, reg_width=16,
        data_width=16, sram_bytes=131072, queue_depth=2,
        divider_stages=8, bank_count=16,
    )
    schedule = replace(to_schedule(point, (), 0.0),
                       loop_order=("k", "q", "d"), data_layout="custom-layout")
    metrics = dict(pe_utilization=0.6, dram_bytes=1234567, cycles=418,
                   area=20000, power=50)
    result = CoDesignResult(point, schedule, None, metrics, True,
                            rationale=("selected plan",))
    plan = _as_plan(result, block_m=32, kept_per_block=16)
    for field in ("tile_q", "tile_k", "tile_d", "parallelism", "num_rows",
                  "pe_per_row", "reg_width", "data_width", "sram_bytes",
                  "queue_depth", "divider_stages", "bank_count"):
        assert getattr(plan, field) == getattr(point, field)
    assert (plan.block_m, plan.kept_per_block) == (32, 16)
    assert plan.loop_order == schedule.loop_order
    assert plan.data_layout == schedule.data_layout
    assert plan.predicted_bytes == metrics["dram_bytes"] != working_set_bytes(point)
    assert plan.predicted_cycles == 418
    assert plan.predicted_power_mw == 50
    assert plan.rationale == result.rationale
