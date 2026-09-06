"""Compiler and µArch are jointly optimised, so the tests are about coupling.

Each case pins a rule that ties a software choice to a hardware one - the rules a
pipeline would get wrong because it decides one layer before seeing the other.
"""

from __future__ import annotations

import dataclasses

import pytest

from fast.agents.codesign import (
    CoDesignPoint,
    CoDesignSpace,
    area_units,
    estimate,
    pe_utilisation,
    to_hardware,
    violations,
    working_set_bytes,
)
from fast.agents.cooptimizer import CoOptimizer, GuidedProposer
from fast.agents.templates import (
    PROVENANCE_RECONSTRUCTED,
    PROVENANCE_UPSTREAM,
    TemplateRegistry,
    required_col_select_bits,
    topk_area_units,
)
from fast.schemas.models import ArchSpecs, KernelProfile, KernelResult, Status


def _profile(imbalance: float = 1.1) -> KernelProfile:
    return KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
        block_density_histogram=(1, 1, 1, 1), load_imbalance=imbalance,
        column_top1_mass=0.2, column_top5_mass=0.4, column_top10_mass=0.6,
    )


def _kernel(sparsity=0.84, occupancy=0.42, imbalance=1.1, status=Status.PASSED) -> KernelResult:
    return KernelResult(
        status=status, baseline_metric=10.0, candidate_metric=10.2, metric_name="ppl",
        quality_loss=0.02, actual_sparsity=sparsity, index_entropy=0.93,
        block_occupancy=occupancy, trace_uri="x", profile=_profile(imbalance),
    )


def _point(**overrides) -> CoDesignPoint:
    base = dict(
        tile_q=64, tile_k=64, tile_d=64, parallelism=8, double_buffer=False,
        num_rows=8, pe_per_row=8, reg_width=32, data_width=16,
        sram_bytes=262144, queue_depth=4,
    )
    base.update(overrides)
    return CoDesignPoint(**base)


# --- the couplings a pipeline would miss -------------------------------------

def test_a_schedule_may_not_ask_for_more_lanes_than_the_array_has():
    problems = violations(_point(parallelism=16, num_rows=8), _kernel(), ArchSpecs())

    assert any("exceeds num_rows" in item for item in problems)


def test_a_k_tile_that_does_not_divide_into_the_register_file_is_rejected():
    problems = violations(_point(tile_k=128, reg_width=64), _kernel(), ArchSpecs())
    assert not any("regWidth" in item for item in problems)   # 128 % 64 == 0 is fine

    problems = violations(_point(tile_k=32, reg_width=64), _kernel(), ArchSpecs())
    assert any("regWidth" in item for item in problems)


def test_double_buffering_can_push_a_tile_out_of_sram():
    single = _point(tile_q=128, tile_k=128, tile_d=64, sram_bytes=65536, double_buffer=False)
    doubled = _point(tile_q=128, tile_k=128, tile_d=64, sram_bytes=65536, double_buffer=True)

    assert working_set_bytes(doubled) == 2 * working_set_bytes(single)
    assert not any("working set" in item for item in violations(single, _kernel(), ArchSpecs()))
    assert any("working set" in item for item in violations(doubled, _kernel(), ArchSpecs()))


def test_the_kernel_block_budget_sizes_the_predict_unit():
    """TopK builds n-1 comparator stages, so keeping more per block costs area
    even though it reduces the execute unit's work. A pipeline that sizes the
    array first never sees this."""
    cheap = topk_area_units(64, 8, 16)
    dear = topk_area_units(64, 32, 16)

    assert dear > cheap
    hardware = to_hardware(
        _point(), TemplateRegistry().by_id("topk"), block_m=64, kept_per_block=32
    )
    assert hardware.topk_m == 64 and hardware.topk_n == 32
    assert hardware.col_select_bits == required_col_select_bits(64) == 6


def test_a_kept_count_wider_than_the_block_is_impossible():
    problems = violations(_point(), _kernel(), ArchSpecs(), block_m=64, kept_per_block=128)

    assert any("exceeds the block width" in item for item in problems)


def test_parameters_outside_the_chisel_module_ranges_are_refused():
    registry = TemplateRegistry()

    problems = violations(_point(num_rows=7), _kernel(), ArchSpecs(), registry)

    assert any("repe_array.numRows=7" in item for item in problems)


def test_an_array_beyond_the_pe_budget_is_refused():
    problems = violations(_point(num_rows=32, pe_per_row=32), _kernel(), ArchSpecs(max_pe=64))

    assert any("PE budget" in item for item in problems)


# --- the cost model ----------------------------------------------------------

def test_a_queue_amortises_row_imbalance():
    """The whole reason a work queue exists: without one the busiest lane sets
    the pace, with a deep one the array stays fed."""
    skewed = _profile(4.0)

    # No queue: the busiest lane sets the pace, so utilisation is 1/imbalance.
    assert pe_utilisation(skewed, 0) == pytest.approx(0.25)
    # Deeper queues recover monotonically toward a fed array.
    depths = [0, 2, 4, 8, 16]
    recovered = [pe_utilisation(skewed, depth) for depth in depths]
    assert recovered == sorted(recovered)
    assert recovered[-1] >= 0.85
    # A balanced kernel needs no queue at all.
    assert pe_utilisation(_profile(1.0), 0) == pytest.approx(1.0)


def test_utilisation_is_not_invented_when_the_kernel_measured_no_profile():
    """A profile-less kernel must not be scored as if it were balanced."""
    assert pe_utilisation(None, 16) == 0.75


def test_sparser_kernels_need_fewer_cycles():
    dense = estimate(_point(), _kernel(sparsity=0.50), 512)
    sparse = estimate(_point(), _kernel(sparsity=0.95), 512)

    assert sparse["cycles"] < dense["cycles"]


def test_traffic_follows_block_occupancy_not_sparsity():
    """Two kernels equally sparse can move very different amounts of data; that
    difference is the cross-layer signal the whole loop exists to exploit."""
    blocky = estimate(_point(), _kernel(sparsity=0.875, occupancy=1.0), 512)
    skippable = estimate(_point(), _kernel(sparsity=0.875, occupancy=0.42), 512)

    assert skippable["dram_bytes"] < blocky["dram_bytes"]
    assert skippable["cycles"] == pytest.approx(blocky["cycles"])


# --- the gate ----------------------------------------------------------------

def test_a_template_outside_the_registry_is_refused():
    report = CoOptimizer(template_id="not-a-template").run(_kernel(), sequence_length=512)

    assert report.evaluated == 0
    assert report.best is None
    assert any("not in the registry" in item for item in report.rejected_examples)


def test_an_unverified_template_is_refused_by_default():
    """The gate, exercised against a record with no evidence behind it.

    Every DynaX template now has simulation evidence, so this constructs the
    state rather than borrowing one - the gate has to keep working for whatever
    template is added next.
    """
    registry = TemplateRegistry((
        dataclasses.replace(
            TemplateRegistry().by_id("topk"),
            verified=False, verified_scope="", blocking_issue="no testbench yet",
        ),
    ))
    report = CoOptimizer(registry, template_id="topk").run(_kernel(), sequence_length=512)

    assert report.evaluated == 0
    assert report.best is None
    assert any("unverified" in item for item in report.rejected_examples)


def test_exploring_with_an_unverified_template_still_reports_the_hardware_as_failed():
    """Costing a design is allowed; claiming it is buildable is not."""
    registry = TemplateRegistry((
        dataclasses.replace(
            TemplateRegistry().by_id("topk"),
            verified=False, verified_scope="",
            blocking_issue="no functional testbench",
        ),
    ))
    report = CoOptimizer(registry, template_id="topk", allow_unverified=True).run(
        _kernel(), sequence_length=512, budget=8, batch=4
    )

    assert report.evaluated == 8
    assert report.best is not None
    assert report.best.hardware.status is Status.FAILED
    assert report.best.hardware.verified_template is False
    assert "no functional testbench" in report.best.hardware.error


def test_a_failed_kernel_stops_co_optimisation():
    report = CoOptimizer(allow_unverified=True).run(
        _kernel(status=Status.FAILED), sequence_length=512
    )

    assert report.evaluated == 0
    assert any("kernel quality gate" in item for item in report.rejected_examples)


def test_every_result_is_labelled_as_a_model_not_a_simulation():
    report = CoOptimizer(allow_unverified=True).run(_kernel(), sequence_length=512, budget=4, batch=4)

    assert report.fidelity == "L1-analytical"


# --- the proposer ------------------------------------------------------------

def test_the_proposer_picks_a_queue_deep_enough_for_the_measured_imbalance():
    skewed = _kernel(imbalance=4.0)
    balanced = _kernel(imbalance=1.0)
    space, specs = CoDesignSpace(), ArchSpecs()

    deep = GuidedProposer().propose(skewed, specs, space, (), 1)[0]
    shallow = GuidedProposer().propose(balanced, specs, space, (), 1)[0]

    assert deep.queue_depth > shallow.queue_depth


def test_the_proposer_never_repeats_a_point():
    report = CoOptimizer(allow_unverified=True).run(
        _kernel(), sequence_length=512, budget=16, batch=4
    )

    keys = [tuple(sorted(item.point.__dict__.items())) for item in report.frontier]
    assert len(keys) == len(set(keys))


def test_the_schedule_and_hardware_describe_the_same_point():
    report = CoOptimizer(allow_unverified=True).run(_kernel(), sequence_length=512, budget=4, batch=4)
    best = report.best

    assert best.schedule.parallelism == best.point.parallelism
    assert best.hardware.pe_rows == best.point.num_rows
    assert best.hardware.pe_cols == best.point.pe_per_row
    assert best.schedule.predicted_bytes == working_set_bytes(best.point)


# --- the gate, now that one template has actually passed --------------------

def test_every_template_carries_simulation_evidence():
    """The registry's status is measured, not assumed.

    Every template has now agreed with an independent reference in simulation.
    The invariant that matters is no longer "which ones" but that the two states
    stay mutually exclusive: a verified template says what it was verified at,
    an unverified one says why it is not. "Unverified" with no reason attached
    is what this project started from.
    """
    registry = TemplateRegistry()

    for item in registry.templates:
        assert bool(item.blocking_issue) != item.verified


def test_a_verified_template_states_the_configuration_it_was_verified_at():
    """`verified` is a claim about evidence, and the evidence has a size.

    RePEArray was checked as a 4x2 array; the paper's DynaX-L is 64x8. Both
    facts belong in the record, because a reader who sees `verified=True` and
    assumes the paper configuration was simulated has been misled by us.
    """
    for item in TemplateRegistry().templates:
        if item.verified:
            assert item.verified_scope, f"{item.template_id} is verified but says nothing about what was covered"
        else:
            assert not item.verified_scope


def test_the_arrays_name_the_paper_configurations_they_were_verified_at():
    """`verified_scope` has to track what was actually run, in both directions.

    It used to say "NOT verified at the paper sizes", which was the honest
    statement while only small instances had been simulated. Both arrays have
    since been checked at DynaX-S and DynaX-L, so the scope names those sizes -
    and a reader can tell 32x4 from 4x2 without leaving the registry.
    """
    registry = TemplateRegistry()

    execute = registry.by_id("repe_array").verified_scope
    assert "32x4" in execute and "64x8" in execute

    predict = registry.by_id("prepe_array").verified_scope
    assert "32x32" in predict and "64x32" in predict

    # And neither may still carry the old disclaimer.
    for scope in (execute, predict):
        assert "NOT verified at the paper sizes" not in scope


def test_non_upstream_templates_say_what_fast_changed():
    """Provenance is an evidence claim, so it cannot be silent.

    Five of DynaX's eight sources do not compile or elaborate as released, and
    one module they depend on is not in the release at all. Any template FAST
    fixed or wrote must record that, or a measurement taken on it would be
    reported as a DynaX baseline when it is not one.
    """
    for item in TemplateRegistry().templates:
        if item.provenance == PROVENANCE_UPSTREAM:
            assert not item.patch_note
        else:
            assert item.patch_note, f"{item.template_id} claims {item.provenance} with no note"


def test_the_predict_array_records_the_ordering_it_depends_on():
    """The array only matches DynaX's software under one feed order.

    A group's selection index runs opposite to its arrival order in both the 1:2
    and the 1:4 path, so each group has to be presented in descending index
    order. Nothing in the sources says so, and fed the other way the array
    computes a different sum from the Python it is supposed to implement. A
    `verified` flag that hid that would be worse than no flag.
    """
    array = TemplateRegistry().by_id("prepe_array")

    assert array.verified is True
    assert "USAGE CONSTRAINT" in array.verified_scope
    assert "DESCENDING" in array.verified_scope
    # Both pruning paths, not just the one the L2 bench table happens to name.
    assert "1_2_4bit" in array.verified_scope
    assert "1_4_6bit" in array.verified_scope


def test_the_reconstructed_exponential_is_not_labelled_as_dynax():
    """The one module FAST wrote from scratch, kept distinguishable.

    RePEA and PrePEA both instantiate it, so every execute-unit and predict-unit
    number depends on it. Calling those DynaX baselines would be false.
    """
    exp_unit = TemplateRegistry().by_id("exp_unit")

    assert exp_unit.provenance == PROVENANCE_RECONSTRUCTED
    assert "does not ship" in exp_unit.patch_note


def test_a_verified_template_can_be_composed_into_a_passing_candidate():
    registry = TemplateRegistry()

    hardware = to_hardware(
        _point(), registry.by_id("topk"), block_m=64, kept_per_block=16
    )

    assert hardware.status is Status.PASSED
    assert hardware.verified_template is True
    assert hardware.error is None
    assert hardware.topk_n == 16


def test_composing_the_topk_template_still_respects_its_parameter_ranges():
    """Verified does not mean unconstrained: n=24 has no comparator cascade."""
    problems = violations(
        _point(), _kernel(), ArchSpecs(), TemplateRegistry(),
        block_m=64, kept_per_block=24,
    )

    assert any("topk.n=24" in item for item in problems)
