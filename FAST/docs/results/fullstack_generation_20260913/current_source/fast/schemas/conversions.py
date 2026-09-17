"""Shared conversions between measured kernels, compiler inputs and DB rows.

These helpers do not run quality gates. Callers must select a quality-passing
measurement before calling kernel_result_from_measurement; a search report
supplies provenance, not an additional validation step.
"""
from __future__ import annotations

from fast.schemas.models import KernelResult, KernelSearchReport, Status


def kernel_result_from_measurement(search: KernelSearchReport | None, best=None) -> KernelResult:
    """Narrow one measurement into the contract the Compiler consumes.

    `search` 允许是 None：调用方手里只有一条测量、没有整份报告时（比如从
    JSON 里挑出一个候选来做评估器的种子），基线指标就取不到。那时报 0.0
    而不是抛异常——基线只用于 `baseline_metric` 这个展示字段，下游的判断
    全部基于 `quality_loss`，而后者在测量本身里。
    """
    best = best if best is not None else (search.best if search else None)
    if best is None:
        raise ValueError("no measurement to narrow into a KernelResult")
    return KernelResult(
        status=Status.PASSED,
        baseline_metric=(search.baseline_metric or 0.0) if search else 0.0,
        candidate_metric=best.perplexity or 0.0,
        metric_name=f"{search.spec.dataset}_perplexity" if search else "perplexity",
        quality_loss=best.quality_loss or 0.0,
        actual_sparsity=best.actual_sparsity,
        index_entropy=best.index_entropy,
        block_occupancy=best.block_occupancy,
        # 获胜配置的 label 就是方法名（"xm:16:8:64" / "nm:16:64" / ...）。
        # 硬件侧靠它查 bank 冲突表——这是搜索结果流向下游的唯一通路，
        # 漏掉的话整条流水线都按最差的 xm 计价。
        sparse_method=best.label,
        trace_uri=(f"search://{search.spec.experiment_id}/{best.label}"
                   if search else f"measurement://{best.label}"),
        profile=best.profile,
        evidence=(
            (f"selected={best.label}", f"proposed_by={best.proposed_by}")
            + ((
                f"measured={len(search.measurements)} of budget "
                f"{search.spec.budget.max_evaluations}",
                f"pareto={','.join(search.pareto)}",
                f"quality_loss={best.quality_loss:.6f} <= epsilon={search.spec.epsilon}",
            ) if search else (
                # 没有整份报告时不要编造搜索层面的证据——「这条测量是从
                # 几个里选出来的」是一个真实的事实，猜不出来。
                f"quality_loss={best.quality_loss:.6f}",
                "no search report: selection context unavailable",
            ))
        ),
    )



def measurement_from_kernel_result(label: str, kernel: KernelResult):
    """Widen a single KernelResult into the row shape the shared database joins on."""
    from fast.schemas.models import KernelMeasurement

    return KernelMeasurement(
        label=label,
        status=kernel.status,
        perplexity=kernel.candidate_metric,
        quality_loss=kernel.quality_loss,
        actual_sparsity=kernel.actual_sparsity,
        index_entropy=kernel.index_entropy,
        block_occupancy=kernel.block_occupancy,
        row_kept_min=None,
        row_kept_max=None,
        wall_seconds=None,
        profile=kernel.profile,
        proposed_by="flow",
    )



def algorithm_parameters(kernel) -> dict:
    """从 kernel 候选的标签解析出硬件该按什么尺寸造。

    不解析的后果实测存在：`plan()` 的 `block_m=64, kept_per_block=16` 是
    **默认值**而调用方不传，于是软件跑的是 `xm:32:4:64`（每块在 {0,4,32} 中
    按质量选）而硬件按 block 64 / kept 16 规划——**评的和造的不是同一个东西**。

    解析不出来时返回空 dict，让 `plan()` 用它自己的默认值并在计划里留下
    痕迹；**不要瞎猜一组参数**。
    """
    from fast.schemas.contract import parse_algorithm

    contract = parse_algorithm(getattr(kernel, "sparse_method", ""))
    out = {}
    if contract.block_m:
        out["block_m"] = contract.block_m
    if contract.sizing_kept:
        # 硬件按**最坏情况**造：阵列和寄存器窗口要装得下最宽的那一行。
        out["kept_per_block"] = contract.sizing_kept
    return out

