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


def _profile(imbalance: float = 1.1, tile_imbalance: float | None = None) -> KernelProfile:
    return KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
        block_density_histogram=(1, 1, 1, 1), load_imbalance=imbalance,
        column_top1_mass=0.2, column_top5_mass=0.4, column_top10_mass=0.6,
        tile_load_imbalance=(
            () if tile_imbalance is None else ((32, tile_imbalance), (64, tile_imbalance))
        ),
    )


def _kernel(sparsity=0.84, occupancy=0.42, imbalance=1.1, status=Status.PASSED,
            method="xm") -> KernelResult:
    return KernelResult(
        sparse_method=method,
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
    problems = violations(_point(parallelism=16, num_rows=8), _kernel(), ArchSpecs(), head_dim=64)

    assert any("exceeds num_rows" in item for item in problems)


def test_a_k_tile_that_does_not_divide_into_the_register_file_is_rejected():
    problems = violations(_point(tile_k=128, reg_width=64), _kernel(), ArchSpecs(), head_dim=64)
    assert not any("regWidth" in item for item in problems)   # 128 % 64 == 0 is fine

    problems = violations(_point(tile_k=32, reg_width=64), _kernel(), ArchSpecs(), head_dim=64)
    assert any("regWidth" in item for item in problems)


def test_double_buffering_can_push_a_tile_out_of_sram():
    single = _point(tile_q=128, tile_k=128, tile_d=64, sram_bytes=65536, double_buffer=False)
    doubled = _point(tile_q=128, tile_k=128, tile_d=64, sram_bytes=65536, double_buffer=True)

    assert working_set_bytes(doubled) == 2 * working_set_bytes(single)
    assert not any("working set" in item for item in violations(single, _kernel(), ArchSpecs(), head_dim=64))
    assert any("working set" in item for item in violations(doubled, _kernel(), ArchSpecs(), head_dim=64))


def test_the_kernel_block_budget_sizes_the_predict_unit():
    """TopK builds n-1 comparator stages, so keeping more per block costs area
    even though it reduces the execute unit's work. A pipeline that sizes the
    array first never sees this."""
    cheap = topk_area_units(64, 8, 16)
    dear = topk_area_units(64, 32, 16)

    assert dear > cheap
    hardware = to_hardware(
        _point(), TemplateRegistry().by_id("topk"),
        head_dim=64, block_m=64, kept_per_block=32
    )
    assert hardware.topk_m == 64 and hardware.topk_n == 32
    assert hardware.col_select_bits == required_col_select_bits(64) == 6


def test_a_kept_count_wider_than_the_block_is_impossible():
    problems = violations(_point(), _kernel(), ArchSpecs(), head_dim=64, block_m=64, kept_per_block=128)

    assert any("exceeds the block width" in item for item in problems)


def test_parameters_outside_the_chisel_module_ranges_are_refused():
    registry = TemplateRegistry()

    problems = violations(_point(num_rows=7), _kernel(), ArchSpecs(), registry, head_dim=64)

    assert any("repe_array.numRows=7" in item for item in problems)


def test_an_array_beyond_the_pe_budget_is_refused():
    problems = violations(_point(num_rows=32, pe_per_row=32), _kernel(), ArchSpecs(max_pe=64), head_dim=64)

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


def test_the_measured_curve_is_used_when_the_workload_matches_a_measurement():
    """xm 是 DynaX 的默认稀疏方法，它的曲线是实测的，模型不该再自己算。

    实测值来自 Verilator 跑真实的逐 tile 行工作量（TinyLlama L10）。
    """
    xm = _profile(3.26, tile_imbalance=1.413)

    # 深度 0 = 严格锁步 = 1/imbalance，RTL 实测逐条落在这个解析界上。
    assert pe_utilisation(xm, 0) == pytest.approx(0.7079, abs=1e-4)
    # **实测曲线在 1 以下饱和**，而原公式收敛到 1。这正是原模型看不到的
    # 那部分：一行的保留数不是 pe 的整数倍时，最后一趟有空槽，加多少队列
    # 都填不上。深度 4 以后就不再改善。
    assert pe_utilisation(xm, 16) == pytest.approx(0.8669, abs=1e-4)
    assert pe_utilisation(xm, 16) - pe_utilisation(xm, 4) < 0.005
    # 原公式在深度 16 会给出 0.976——比实测高 11 个百分点。
    assert 1.0 / (1.0 + (1.413 - 1.0) / 17.0) > pe_utilisation(xm, 16) + 0.10


def test_an_imbalance_outside_the_measured_range_falls_back_instead_of_guessing():
    """实测点覆盖 1.00-1.70。范围之外必须退回模型，不能拿最近的曲线充数。

    区别是实打实的：不均衡度 4.0 用最近曲线会得到 0.59，而它真实的锁步
    上界是 0.25。静默取最近点会把一个差 2.4 倍的数当成实测报出去。
    """
    wild = _profile(4.0, tile_imbalance=4.0)
    assert pe_utilisation(wild, 0) == pytest.approx(0.25)


def test_the_tile_imbalance_is_preferred_over_the_global_one():
    """阵列感受到的是 tile 内的不均衡，不是整行全序列的全局极值。

    两者连排序都不一样（实测：全局量把完美均衡的 N:M 排在 topk 之前）。
    """
    # 全局量说很不均衡，tile 内说完美均衡——按 tile 内的走。
    disagreeing = _profile(1.825, tile_imbalance=1.0)
    assert pe_utilisation(disagreeing, 0) == pytest.approx(1.0)


def test_a_deeper_queue_costs_area():
    """队列不是免费的。此前 area_units() 对 queue_depth 完全不收费，于是
    它成了一个只有收益的维度——优化器必然选最深的那个还看不出选错了。"""
    # DynaX-S 的形状，这个尺寸上队列面积是实测的而不是外推的。
    shape = dict(num_rows=32, pe_per_row=4)
    shallow = area_units(_point(queue_depth=0, **shape), block_m=64, kept_per_block=16, head_dim=64)
    deep = area_units(_point(queue_depth=16, **shape), block_m=64, kept_per_block=16, head_dim=64)

    # 深度 16 的队列实测 134,870 um^2，深度 0 是 8,899——差 126k。
    # 两个阵列合计约 740k，所以这不是舍入误差，是 17% 的芯片面积。
    assert deep - shallow == pytest.approx(134870.2 - 8899.3, abs=1.0)


def test_a_balanced_kernel_is_not_sold_a_queue_it_cannot_use():
    """N:M 结构化稀疏按构造完美均衡，队列买不到任何东西，就不该花那个面积。

    旧启发式（用全局 imbalance 去够 0.9 这个固定目标）在 nm 上选深度 8——
    因为全局量把完美均衡的 nm 报成了 1.825。那是 74k um^2 买零收益。
    """
    from fast.agents.cooptimizer import _shallowest_effective_queue

    balanced = _profile(1.825, tile_imbalance=1.000)
    assert _shallowest_effective_queue(balanced, (0, 2, 4, 8, 16)) == 0


def test_the_chosen_depth_stops_where_the_clock_penalty_takes_over():
    """深度选在吞吐峰值上，不是利用率峰值上。

    xm 的利用率在深度 8/16 最高（0.867），但队列的关键路径到那时已经
    3.14 ns，超过阵列的 2.23 ns。算上时钟，峰值在深度 2。

    旧启发式在这里选 16：多花 126k um^2（DynaX-S 芯片面积的 17%）买一个
    比完全不装队列还慢的系统。
    """
    from fast.agents.cooptimizer import _shallowest_effective_queue

    xm = _profile(3.26, tile_imbalance=1.413)
    chosen = _shallowest_effective_queue(xm, (0, 2, 4, 8, 16))
    assert chosen == 2
    # 利用率单看确实是深度 16 最高——所以判据不能只看利用率。
    assert pe_utilisation(xm, 16) > pe_utilisation(xm, chosen)


def test_the_memory_path_is_in_the_cycle_count():
    """访存必须影响周期数。此前 `cycles = sparse_macs / (lanes * util)` 里
    一项和访存有关的都没有——等于假设带宽无限，于是 bank 数、sram_bytes、
    double_buffer 对周期数的影响全是零。"""
    few = estimate(_point(bank_count=4), _kernel(), 512, head_dim=64)
    many = estimate(_point(bank_count=32), _kernel(), 512, head_dim=64)

    assert few["cycles"] > many["cycles"]
    # 实测：xm 在 4 个 bank 下减速 3.05x，32 个 bank 降到 1.13x。
    assert few["memory_slowdown"] == pytest.approx(3.054, abs=1e-3)
    assert many["memory_slowdown"] == pytest.approx(1.133, abs=1e-3)
    # 计算周期本身不该被 bank 数影响，被影响的是总周期。
    assert few["compute_cycles"] == pytest.approx(many["compute_cycles"])


def test_double_buffering_cannot_fix_a_bandwidth_shortfall():
    """双缓冲藏的是延迟不是带宽。

    取数引擎的吞吐比阵列的需求慢 N 倍时，再多的缓冲也补不上那 N 倍——
    所以 double_buffer 不该出现在访存减速那一项里。它只影响驻留字节和面积。
    """
    single = estimate(_point(double_buffer=False), _kernel(), 512, head_dim=64)
    double = estimate(_point(double_buffer=True), _kernel(), 512, head_dim=64)

    assert single["memory_slowdown"] == double["memory_slowdown"]
    assert single["cycles"] == pytest.approx(double["cycles"])


def test_the_sparse_method_changes_the_bank_conflict_cost():
    """同样的 bank 数，不同稀疏方法的冲突代价差很多——冲突取决于索引的
    分布而不是个数。N:M 结构化稀疏步长规则，取模映射下几乎不撞。"""
    structured = estimate(_point(bank_count=8), _kernel(method="nm:16:64"), 512, head_dim=64)
    dynamic = estimate(_point(bank_count=8), _kernel(method="xm"), 512, head_dim=64)

    # 实测 8 bank：nm 1.19x，xm 2.14x。
    assert structured["memory_slowdown"] < dynamic["memory_slowdown"]
    assert dynamic["cycles"] > structured["cycles"] * 1.5


def test_sram_area_is_not_a_rounding_error():
    """SRAM 面积此前是 `bytes * 0.1`，256 KB 只有 26,214 um^2——一个舍入
    误差。真实的宏拼装是 1,049,989 um^2，比两个阵列合计（74 万）还大。"""
    from fast.agents.templates import sram_area_units

    assert sram_area_units(262144) == pytest.approx(1_049_989, rel=1e-3)
    assert sram_area_units(262144) > 40 * (262144 * 0.1)


def test_utilisation_is_not_invented_when_the_kernel_measured_no_profile():
    """A profile-less kernel must not be scored as if it were balanced."""
    assert pe_utilisation(None, 16) == 0.75


def test_sparser_kernels_need_fewer_cycles():
    dense = estimate(_point(), _kernel(sparsity=0.50), 512, head_dim=64)
    sparse = estimate(_point(), _kernel(sparsity=0.95), 512, head_dim=64)

    assert sparse["cycles"] < dense["cycles"]


def test_traffic_follows_block_occupancy_not_sparsity():
    """Two kernels equally sparse can move very different amounts of data; that
    difference is the cross-layer signal the whole loop exists to exploit."""
    blocky = estimate(_point(), _kernel(sparsity=0.875, occupancy=1.0), 512, head_dim=64)
    skippable = estimate(_point(), _kernel(sparsity=0.875, occupancy=0.42), 512, head_dim=64)

    assert skippable["dram_bytes"] < blocky["dram_bytes"]
    assert skippable["cycles"] == pytest.approx(blocky["cycles"])


# --- the gate ----------------------------------------------------------------

def test_a_template_outside_the_registry_is_refused():
    report = CoOptimizer(template_id="not-a-template").run(_kernel(), sequence_length=512, head_dim=64)

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
    report = CoOptimizer(registry, template_id="topk").run(_kernel(), sequence_length=512, head_dim=64)

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
        _kernel(), sequence_length=512, head_dim=64, budget=8, batch=4
    )

    assert report.evaluated == 8
    assert report.best is not None
    assert report.best.hardware.status is Status.FAILED
    assert report.best.hardware.verified_template is False
    assert "no functional testbench" in report.best.hardware.error


def test_a_failed_kernel_stops_co_optimisation():
    report = CoOptimizer(allow_unverified=True).run(
        _kernel(status=Status.FAILED), sequence_length=512, head_dim=64
    )

    assert report.evaluated == 0
    assert any("kernel quality gate" in item for item in report.rejected_examples)


def test_every_result_is_labelled_as_a_model_not_a_simulation():
    report = CoOptimizer(allow_unverified=True).run(_kernel(), sequence_length=512, head_dim=64, budget=4, batch=4)

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
        _kernel(), sequence_length=512, head_dim=64, budget=16, batch=4
    )

    keys = [tuple(sorted(item.point.__dict__.items())) for item in report.frontier]
    assert len(keys) == len(set(keys))


def test_the_schedule_and_hardware_describe_the_same_point():
    report = CoOptimizer(allow_unverified=True).run(_kernel(), sequence_length=512, head_dim=64, budget=4, batch=4)
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
        _point(), registry.by_id("topk"),
        head_dim=64, block_m=64, kept_per_block=16
    )

    assert hardware.status is Status.PASSED
    assert hardware.verified_template is True
    assert hardware.error is None
    assert hardware.topk_n == 16


def test_composing_the_topk_template_still_respects_its_parameter_ranges():
    """Verified does not mean unconstrained: n=24 has no comparator cascade."""
    problems = violations(
        _point(), _kernel(), ArchSpecs(), TemplateRegistry(),
        head_dim=64, block_m=64, kept_per_block=24,
    )

    assert any("topk.n=24" in item for item in problems)
