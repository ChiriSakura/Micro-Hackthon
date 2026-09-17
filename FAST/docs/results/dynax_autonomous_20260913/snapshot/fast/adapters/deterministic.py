"""Cheap deterministic adapters used to validate orchestration, not paper results."""

from __future__ import annotations

from fast.schemas.models import (
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelResult,
    Status,
)


class DeterministicKernelAdapter:
    def evaluate(self, spec: ExperimentSpec) -> KernelResult:
        retained = spec.sparsity_x / spec.sparsity_m
        loss = round((1.0 - retained) * 0.01, 8)
        return KernelResult(
            status=Status.PASSED if loss <= spec.epsilon else Status.FAILED,
            baseline_metric=10.0,
            candidate_metric=10.0 + loss,
            metric_name="synthetic_perplexity_delta",
            quality_loss=loss,
            actual_sparsity=1.0 - retained,
            index_entropy=0.5,
            block_occupancy=retained,
            trace_uri=f"memory://{spec.candidate_id}/kernel",
            sparse_method=spec.sparse_method,
            evidence=("deterministic-adapter",),
            error=None if loss <= spec.epsilon else "quality_loss exceeds epsilon",
        )


class DeterministicEvaluationAdapter:
    def evaluate(
        self, spec: ExperimentSpec, candidate: HardwareCandidate,
        plan=None, kernel=None,
    ) -> EvaluationResult:
        functional = candidate.verified_template
        utilization = min(0.95, (candidate.pe_rows * candidate.pe_cols) / 64.0)
        cycles = max(1, spec.sequence_length * spec.sequence_length // max(1, candidate.pe_rows * candidate.pe_cols))
        power = 0.05 * candidate.pe_rows * candidate.pe_cols
        return EvaluationResult(
            status=Status.PASSED if functional else Status.FAILED,
            fidelity="L0-deterministic",
            functional_passed=functional,
            cycles=cycles,
            throughput=spec.sequence_length / cycles,
            pe_utilization=utilization,
            area=float(candidate.pe_rows * candidate.pe_cols),
            power=power,
            edp=power * cycles * cycles,
            wall_seconds=0.0,
            cloud_cost_usd=0.0,
            log_uri=f"memory://{spec.candidate_id}/evaluation",
            evidence=("verified_template", "cycles", "pe_utilization"),
            error=None if functional else "template has not passed the verification gate",
        )
