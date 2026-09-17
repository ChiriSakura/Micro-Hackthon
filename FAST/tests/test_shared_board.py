"""共享板：完整记录优化轨迹，并回答「验证过的最好的点是哪个」。

提案 Table II 里 Orchestrator 的输出是 "Prompts, shared state"，Fig. 1 里
Evaluator 挂着 "Shared Data"。这块基础设施一直在（`ExperimentDB` 有完整
schema），但循环从来没接上（`db=None` 让 `_record` 直接返回），而且接上也
不够——`stage_outputs` 的主键是 (run_id, label, layer)，第 N 轮**覆盖**第
N-1 轮，记的是最终状态不是轨迹。
"""

from __future__ import annotations

import pytest

from fast.storage.experiment_db import ExperimentDB
from fast.schemas.models import (
    ArchSpecs,
    Budget,
    CompilerSchedule,
    Critique,
    Decision,
    EvaluationResult,
    ExperimentSpec,
    KernelMeasurement,
    Layer,
    Status,
)


def _spec() -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="board", candidate_id="c0", model="m", dataset="d",
        sequence_length=128, sparsity_x=8, sparsity_m=64, epsilon=0.05,
        seed=0, budget=Budget(max_candidates=1, max_evaluations=1),
    )


def _plan(rows: int, pes: int, area: float, clock_ns: float = 2.528,
          cycles: float = 5000.0, power_mw: float = 400.0) -> CompilerSchedule:
    return CompilerSchedule(
        status=Status.PASSED, tile_q=64, tile_k=64, tile_d=64,
        loop_order=("q", "k", "d"), data_layout="row", parallelism=rows * pes,
        predicted_utilization=0.9, predicted_bytes=1 << 20,
        num_rows=rows, pe_per_row=pes, queue_depth=2,
        predicted_area_um2=area, predicted_clock_ns=clock_ns,
        predicted_cycles=cycles, predicted_power_mw=power_mw,
    )


def _evaluation(fidelity: str, util: float, *, passed: bool = True) -> EvaluationResult:
    return EvaluationResult(
        status=Status.PASSED, fidelity=fidelity, functional_passed=passed,
        cycles=1000, throughput=1.0, pe_utilization=util, area=None, power=None,
        edp=None, wall_seconds=0.1, cloud_cost_usd=0.0, log_uri="",
        evidence=("e",),
    )


def _critique(layer: Layer) -> Critique:
    return Critique(status=Status.PASSED, attribution=layer,
                    decision=Decision.CONTINUE, summary="s",
                    evidence=("evaluation.pe_utilization",))


def _measurement(label: str) -> KernelMeasurement:
    return KernelMeasurement(
        label=label, status=Status.PASSED, perplexity=10.0, quality_loss=0.02,
        actual_sparsity=0.8, index_entropy=0.9, block_occupancy=0.5,
        row_kept_min=8.0, row_kept_max=16.0, wall_seconds=1.0,
    )


@pytest.fixture
def board(tmp_path) -> ExperimentDB:
    return ExperimentDB(tmp_path / "board.sqlite")


def _write_round(board, run_id, index, *, label, plan, evaluation, layer):
    board.record_stage(run_id, label, "compiler", plan, round_index=index)
    board.record_stage(run_id, label, "evaluator", evaluation, round_index=index)
    board.record_attribution(run_id, label, _critique(layer), round_index=index)


def test_the_trajectory_keeps_every_round_not_just_the_last(board):
    """同一个候选被反复规划/实现时，每一轮都要留下来。

    被覆盖掉的恰好是「这一层改了之后指标怎么动」——归因唯一的依据。
    """
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:32:4:64")])
    for index, (rows, util) in enumerate([(32, 0.839), (16, 0.899), (16, 0.654)]):
        _write_round(board, run_id, index, label="xm:32:4:64",
                     plan=_plan(rows, 8, 1_000_000.0 + index),
                     evaluation=_evaluation("L2-rtl-simulation", util),
                     layer=Layer.COMPILER)

    trajectory = board.trajectory(run_id)
    assert [row["round_index"] for row in trajectory] == [0, 1, 2]
    assert [row["pe_utilization"] for row in trajectory] == [0.839, 0.899, 0.654]
    assert [row["num_rows"] for row in trajectory] == [32, 16, 16]


def test_the_front_holds_every_non_dominated_point(board):
    """输出是一张**帕累托表**，不是单点。

        min L(x)  s.t.  dAcc <= eps, A <= A_max, P <= P_max, f >= f_min

    单点会把多目标压成一个标量，而那个标量的权重是拍的——延迟和功耗谁更
    重要取决于部署场景，不该由循环替人决定。
    """
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:64:16:64")])
    # 轮0 慢但能耗低；轮1 快但能耗高；轮2 同功耗却更慢。
    # 功耗覆盖仍标 partial，前沿是预测能耗–延迟。
    for index, (cycles, area) in enumerate(
            [(6000.0, 1_000_000.0), (4000.0, 1_465_644.0), (7000.0, 1_800_000.0)]):
        _write_round(board, run_id, index, label="xm:64:16:64",
                     plan=_plan(16, 16, area, cycles=cycles, power_mw=(800.0 if index == 1 else 400.0)),
                     evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)

    front = board.pareto_front(run_id, ArchSpecs())
    assert [row["round_index"] for row in front] == [1, 0], "按延迟排，两个都在"
    assert all(row["latency_ns"] for row in front)


def test_a_dominated_point_never_enters_the_front(board):
    """在所有目标上都不更好的点，没有资格进前沿。"""
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:64:16:64")])
    _write_round(board, run_id, 0, label="xm:64:16:64",
                 plan=_plan(16, 16, 1_465_644.0, cycles=4000.0, power_mw=300.0),
                 evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)
    _write_round(board, run_id, 1, label="xm:64:16:64",
                 plan=_plan(16, 16, 1_465_644.0, cycles=5000.0, power_mw=400.0),
                 evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)

    assert [row["round_index"] for row in board.pareto_front(run_id, ArchSpecs())] == [0]


def test_an_infeasible_point_is_excluded_and_says_which_constraint(board):
    """「超了预算」和「没测到」是两件事，读的人要能分开。"""
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:64:16:64")])
    _write_round(board, run_id, 0, label="xm:64:16:64",
                 plan=_plan(32, 16, 5_000_000.0, cycles=3000.0, power_mw=300.0),
                 evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)
    _write_round(board, run_id, 1, label="xm:64:16:64",
                 plan=_plan(16, 16, 1_465_644.0, cycles=5000.0, power_mw=400.0),
                 evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)

    specs = ArchSpecs(max_area_um2=4_000_000.0)
    assert [row["round_index"] for row in board.pareto_front(run_id, specs)] == [1]
    blocked = board.infeasible(run_id, specs)
    assert blocked[0]["round_index"] == 0
    assert "area" in blocked[0]["violations"][0]


def test_a_power_budget_is_enforced_when_given(board):
    """约束是**输入**：不给功耗预算就不该拿功耗挡任何点。"""
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:64:16:64")])
    _write_round(board, run_id, 0, label="xm:64:16:64",
                 plan=_plan(16, 16, 1_465_644.0, cycles=3000.0, power_mw=900.0),
                 evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)

    assert len(board.pareto_front(run_id, ArchSpecs())) == 1           # 没给预算
    assert board.pareto_front(run_id, ArchSpecs(max_power_mw=500.0)) == []


def test_unverified_rounds_never_enter_the_front(board):
    """L1 的数是 planner 自己代价模型算的，让它进前沿等于让规划者给自己打分。"""
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:64:16:64")])
    _write_round(board, run_id, 0, label="xm:64:16:64",
                 plan=_plan(16, 16, 869_171.0, cycles=1000.0, power_mw=100.0),
                 evaluation=_evaluation("L1-analytical-shared-model", 0.99, passed=False),
                 layer=Layer.UARCH)
    _write_round(board, run_id, 1, label="xm:64:16:64",
                 plan=_plan(16, 16, 1_465_644.0, cycles=5000.0, power_mw=400.0),
                 evaluation=_evaluation("L2-rtl-simulation", 0.850), layer=Layer.UARCH)

    assert [row["round_index"] for row in board.pareto_front(run_id, ArchSpecs())] == [1]


def test_no_verified_round_means_an_empty_front(board):
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:64:16:64")])
    _write_round(board, run_id, 0, label="xm:64:16:64", plan=_plan(16, 16, 869_171.0),
                 evaluation=_evaluation("L1-analytical-shared-model", 0.99, passed=False),
                 layer=Layer.UARCH)

    assert board.pareto_front(run_id, ArchSpecs()) == []
    assert board.best_verified(run_id, ArchSpecs()) is None


def test_the_front_does_not_repeat_the_same_point(board):
    """相等的两个点互不支配（`dominates` 要求至少一个严格更好），所以它们
    全都会"活"下来。实测一次 4 轮的设计完全相同，前沿报了 4 个一模一样的
    行——那不是四个可选方案，是一个。
    """
    run_id = board.start_run(_spec())
    board.record_measurements(run_id, [_measurement("xm:32:4:64")])
    for index in range(4):
        _write_round(board, run_id, index, label="xm:32:4:64",
                     plan=_plan(16, 16, 1_465_644.0, cycles=5838.9, power_mw=680.7),
                     evaluation=_evaluation("L2-rtl-simulation", 0.839), layer=Layer.UARCH)

    front = board.pareto_front(run_id, ArchSpecs())
    assert len(front) == 1
    # 反复到达同一个点是有信息的（循环在原地打转），要留下来但不占四行。
    assert front[0]["reached_in_rounds"] == [0, 1, 2, 3]
