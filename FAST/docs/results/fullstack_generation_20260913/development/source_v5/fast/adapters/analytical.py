"""Evaluation derived from the co-design cost model.

This is a stand-in for the Verilator backend that plan stage 1 has not built yet,
and it carries a warning it must not lose: **it shares the co-optimizer's model**.
When the optimizer picks a point because the model says its EDP is lowest, and
then this adapter scores that point with the same model, agreement is arithmetic,
not confirmation. The Critic is told so explicitly in the evidence, so a decision
never rests on a check that could not have failed.

Independent evaluation arrives with Verilator: a different implementation, run
against golden vectors, able to disagree.
"""

from __future__ import annotations

from dataclasses import dataclass

from fast.agents.codesign import CoDesignPoint, estimate
from fast.schemas.models import (
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelResult,
    Status,
)


@dataclass(frozen=True)
class AnalyticalEvaluationAdapter:
    """Scores a hardware candidate with the first-order model.

    It needs the kernel result as well as the candidate, because utilisation is
    a property of the workload's row imbalance rather than of the array alone.
    """

    kernel: KernelResult
    # 模型的**真实 head 维度**。默认 64 是 TinyLlama / BLOOM 这两个被测模型
    # 的值；换模型必须跟着改——它决定总工作量，不是一个调参。
    #
    # 和分块尺寸 `tile_d` 是两回事：代价模型曾经用 `tile_d` 冒充它，于是把
    # 分块改小会被当成「活变少」，实测 tile_d 64->32 让 cycles 减半、
    # EDP 变四分之一，纯粹是模型假象。
    head_dim: int = 64
    block_m: int = 64
    kept_per_block: int = 16
    shares_optimizer_model: bool = True

    def evaluate(self, spec: ExperimentSpec, candidate: HardwareCandidate,
                 plan=None, kernel=None) -> EvaluationResult:
        if candidate.status is not Status.PASSED:
            return EvaluationResult(
                status=Status.SKIPPED,
                fidelity="none",
                functional_passed=False,
                cycles=None, throughput=None, pe_utilization=None,
                area=None, power=None, edp=None,
                wall_seconds=0.0, cloud_cost_usd=0.0, log_uri="",
                evidence=("hardware.status", "hardware.verified_template"),
                error=candidate.error or "hardware candidate gate failed",
            )

        # **优先用计划本身，不要从 HardwareCandidate 反推。**
        #
        # candidate 只装硬件字段，`tile_*` / `double_buffer` / `divider_stages` /
        # `bank_count` 都不在里面，反推只能猜——而 `divider_stages` 猜成默认的
        # 0 级就是 14.78 ns，计划里是 8 级 1.98 ns，时钟差 7 倍。评的于是根本
        # 不是被规划的那个点。
        #
        # 这个 bug 是 Critic 的「规划值 vs 实测值」检查抓出来的：两边共用同一个
        # 代价模型却算出不同的数，那不是标定问题，是实现分叉。
        # 闭环里每一轮的 kernel 候选都不同，所以 workload 是**调用参数**而不是
        # 构造参数。构造时绑定的那个只作为单点路径的兜底——绑死会让每一轮都
        # 用第 0 轮的稀疏度打分，而稀疏度直接决定周期数。
        workload = kernel if kernel is not None else self.kernel

        if plan is not None and plan.status is Status.PASSED:
            point = CoDesignPoint(
                tile_q=plan.tile_q, tile_k=plan.tile_k, tile_d=plan.tile_d,
                parallelism=plan.parallelism,
                double_buffer="double" in plan.data_layout,
                num_rows=plan.num_rows, pe_per_row=plan.pe_per_row,
                reg_width=plan.reg_width, data_width=plan.data_width,
                sram_bytes=plan.sram_bytes, queue_depth=plan.queue_depth,
                divider_stages=plan.divider_stages, bank_count=plan.bank_count,
            )
        else:
            point = CoDesignPoint(
                tile_q=64, tile_k=64, tile_d=64,
                parallelism=min(candidate.pe_rows, 16), double_buffer=False,
                num_rows=candidate.pe_rows, pe_per_row=candidate.pe_cols,
                reg_width=candidate.reg_width, data_width=candidate.data_width,
                sram_bytes=candidate.sram_bytes, queue_depth=candidate.queue_depth,
            )
        metrics = estimate(
            point, workload, spec.sequence_length, head_dim=self.head_dim,
            block_m=candidate.topk_m or self.block_m,
            kept_per_block=candidate.topk_n or self.kept_per_block,
        )

        evidence = [
            f"model=L1-analytical (no RTL was simulated)",
            f"pe_utilization={metrics['pe_utilization']:.4f}",
            # 取数减速的出处：`fallback:` 开头意味着这个算法**没有自己的
            # 标定**，借了 xm 的值。研究结论依赖于这个区别。
            f"memory_slowdown={metrics['memory_slowdown']:.3f} "
            f"({metrics.get('memory_slowdown_source', 'unknown')})",
            f"cycles={metrics['cycles']:.0f}",
            f"dram_bytes={metrics['dram_bytes']:.0f}",
            f"area_units={metrics['area']:.1f}",
        ]
        if workload.profile is not None:
            evidence.append(f"kernel.load_imbalance={workload.profile.load_imbalance:.4f}")
        else:
            evidence.append("kernel profile absent: utilisation is a default, not a measurement")
        if self.shares_optimizer_model:
            evidence.append(
                "NOT INDEPENDENT: this shares the co-optimizer's cost model, so it "
                "cannot disagree with the choice it is scoring"
            )

        return EvaluationResult(
            status=Status.PASSED,
            # The fidelity string travels with every downstream report, so it
            # says what this is rather than just how precise it claims to be.
            fidelity="L1-analytical-shared-model" if self.shares_optimizer_model else "L1-analytical",
            # A model cannot establish functional correctness; only a simulation
            # against golden vectors can, and none has run.
            functional_passed=False,
            cycles=int(metrics["cycles"]),
            throughput=metrics["throughput"],
            pe_utilization=metrics["pe_utilization"],
            area=metrics["area"],
            power=metrics["power"],
            edp=metrics["edp"],
            wall_seconds=0.0,
            cloud_cost_usd=0.0,
            log_uri="model://l1-analytical",
            evidence=tuple(evidence),
            error="functional correctness is unproven: no RTL simulation has run",
        )
