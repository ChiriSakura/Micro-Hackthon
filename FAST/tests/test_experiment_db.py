"""The shared database exists so the Critic can attribute across layers.

Attribution is a join, so these tests are mostly about whether the join actually
answers the questions the Critic asks - not about whether rows round-trip.
"""

from __future__ import annotations

import pytest

from fast.schemas.models import (
    Budget,
    CompilerSchedule,
    Critique,
    Decision,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelCandidate,
    KernelMeasurement,
    KernelProfile,
    Layer,
    Status,
)
from fast.storage import ExperimentDB


def _spec(candidate_id="c1") -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="attrib-test", candidate_id=candidate_id, model="tiny",
        dataset="wikitext-2-raw-v1", sequence_length=512, sparsity_x=8,
        sparsity_m=64, epsilon=0.05, seed=1,
        budget=Budget(max_candidates=4, max_evaluations=4, max_wall_seconds=60),
    )


def _profile(imbalance: float, top5: float = 0.3) -> KernelProfile:
    return KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 2, 3, 4),
        block_density_histogram=(4, 3, 2, 1), load_imbalance=imbalance,
        column_top1_mass=0.1, column_top5_mass=top5, column_top10_mass=0.5,
        per_layer_kept_ratio=(0.1, 0.2),
    )


def _measurement(label, loss, sparsity, imbalance=1.1, by="sweep") -> KernelMeasurement:
    return KernelMeasurement(
        label=label, status=Status.PASSED, perplexity=10.0 * (1 + loss),
        quality_loss=loss, actual_sparsity=sparsity, index_entropy=0.9,
        block_occupancy=0.4, row_kept_min=8, row_kept_max=16, wall_seconds=12.0,
        profile=_profile(imbalance), proposed_by=by,
    )


def _db(tmp_path) -> ExperimentDB:
    return ExperimentDB(tmp_path / "shared.db")


def test_the_cross_layer_view_joins_every_layer_for_one_candidate(tmp_path):
    """This row is what "attribute the bottleneck to a layer" is computed from."""
    db = _db(tmp_path)
    spec = _spec()
    run_id = db.start_run(spec, proposer="sweep")
    db.record_measurements(run_id, [_measurement("xm:32:8:64", 0.02, 0.86, imbalance=3.4)])
    db.record_stage(run_id, "xm:32:8:64", "compiler", CompilerSchedule(
        status=Status.PASSED, tile_q=64, tile_k=64, tile_d=32, loop_order=("q",),
        data_layout="blocked-qkd", parallelism=5, predicted_utilization=0.29,
        predicted_bytes=1024,
    ))
    db.record_stage(run_id, "xm:32:8:64", "uarch", HardwareCandidate(
        status=Status.PASSED, template_id="t", template_digest="d", verified_template=True,
        pe_rows=5, pe_cols=1, queue_depth=8, sram_bytes=1024, data_width=16, manifest_uri="m",
    ))
    db.record_stage(run_id, "xm:32:8:64", "evaluator", EvaluationResult(
        status=Status.PASSED, fidelity="L0", functional_passed=True, cycles=900,
        throughput=1.0, pe_utilization=0.31, area=5.0, power=1.0, edp=810.0,
        wall_seconds=1.0, cloud_cost_usd=0.0, log_uri="l",
    ))
    db.record_attribution(run_id, "xm:32:8:64", Critique(
        status=Status.PASSED, attribution=Layer.KERNEL, decision=Decision.CONTINUE,
        summary="rows are imbalanced", evidence=("kernel.load_imbalance",),
    ))

    rows = db.cross_layer(run_id)

    assert len(rows) == 1
    row = rows[0]
    assert row["label"] == "xm:32:8:64"
    assert row["load_imbalance"] == pytest.approx(3.4)
    assert row["compiler_parallelism"] == 5
    assert row["eval_pe_utilization"] == pytest.approx(0.31)
    assert row["attribution"] == "kernel"


def test_a_candidate_with_no_downstream_stages_still_appears(tmp_path):
    """A kernel result that never reached the compiler is exactly the case the
    Critic must be able to see, so the join must not drop it."""
    db = _db(tmp_path)
    run_id = db.start_run(_spec())
    db.record_measurements(run_id, [_measurement("nm:8:64", 0.30, 0.87)])

    row = db.cross_layer(run_id)[0]

    assert row["label"] == "nm:8:64"
    assert row["compiler_parallelism"] is None
    assert row["attribution"] is None


def test_rejected_proposals_are_recorded_not_discarded(tmp_path):
    """"What did the agent rule out" is the first question when a search goes
    somewhere strange."""
    db = _db(tmp_path)
    run_id = db.start_run(_spec())
    db.record_rejections(run_id, 2, "kernel", [
        "xm:999:1:64: outside the search space",
        "llm call failed: TimeoutError",
    ])

    rejected = db.rejected(run_id)

    assert {row["label"] for row in rejected} == {"xm:999:1:64", "(unnamed)"}
    assert any("outside the search space" in row["reject_reason"] for row in rejected)


def test_the_frontier_query_returns_only_configurations_inside_epsilon(tmp_path):
    db = _db(tmp_path)
    run_id = db.start_run(_spec())
    db.record_measurements(run_id, [
        _measurement("sparse-but-costly", 0.30, 0.96),
        _measurement("good", 0.02, 0.86),
        _measurement("safe", 0.00, 0.74),
    ])

    frontier = db.frontier(run_id, epsilon=0.05)

    assert [row["label"] for row in frontier] == ["good", "safe"]


def test_the_database_refuses_to_write_through_the_query_hatch(tmp_path):
    db = _db(tmp_path)

    with pytest.raises(ValueError, match="read-only"):
        db.query("DELETE FROM kernel_measurements")


def test_two_runs_of_the_same_spec_share_an_id_but_different_specs_do_not(tmp_path):
    """The id is the spec digest, so a rerun updates in place and a changed spec
    never silently overwrites the earlier evidence."""
    db = _db(tmp_path)

    same = db.start_run(_spec()), db.start_run(_spec())
    other = db.start_run(_spec(candidate_id="c2"))

    assert same[0] == same[1]
    assert other != same[0]


def test_a_measurement_without_a_profile_records_null_not_zero(tmp_path):
    """Zero would read as a perfectly balanced workload; null says "not measured"."""
    db = _db(tmp_path)
    run_id = db.start_run(_spec())
    bare = KernelMeasurement(
        label="legacy", status=Status.PASSED, perplexity=10.0, quality_loss=0.01,
        actual_sparsity=0.8, index_entropy=0.9, block_occupancy=0.4,
        row_kept_min=None, row_kept_max=None, wall_seconds=1.0,
    )
    db.record_measurements(run_id, [bare])

    row = db.cross_layer(run_id)[0]

    assert row["load_imbalance"] is None
