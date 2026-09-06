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
    block_m: int = 64
    kept_per_block: int = 16
    shares_optimizer_model: bool = True

    def evaluate(self, spec: ExperimentSpec, candidate: HardwareCandidate) -> EvaluationResult:
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

        point = CoDesignPoint(
            tile_q=64, tile_k=64, tile_d=64,
            parallelism=min(candidate.pe_rows, 16), double_buffer=False,
            num_rows=candidate.pe_rows, pe_per_row=candidate.pe_cols,
            reg_width=candidate.reg_width, data_width=candidate.data_width,
            sram_bytes=candidate.sram_bytes, queue_depth=candidate.queue_depth,
        )
        metrics = estimate(
            point, self.kernel, spec.sequence_length,
            block_m=candidate.topk_m or self.block_m,
            kept_per_block=candidate.topk_n or self.kept_per_block,
        )

        evidence = [
            f"model=L1-analytical (no RTL was simulated)",
            f"pe_utilization={metrics['pe_utilization']:.4f}",
            f"cycles={metrics['cycles']:.0f}",
            f"dram_bytes={metrics['dram_bytes']:.0f}",
            f"area_units={metrics['area']:.1f}",
        ]
        if self.kernel.profile is not None:
            evidence.append(f"kernel.load_imbalance={self.kernel.profile.load_imbalance:.4f}")
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
