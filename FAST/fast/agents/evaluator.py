from __future__ import annotations

from fast.adapters.base import EvaluationAdapter
from fast.schemas.models import EvaluationResult, ExperimentSpec, HardwareCandidate, Status


class EvaluatorAgent:
    """Normalizes one fidelity backend into the common evaluation contract."""

    def __init__(self, adapter: EvaluationAdapter):
        self.adapter = adapter

    def run(self, spec: ExperimentSpec, candidate: HardwareCandidate) -> EvaluationResult:
        if candidate.status is not Status.PASSED:
            return EvaluationResult(
                status=Status.SKIPPED,
                fidelity="none",
                functional_passed=False,
                cycles=None,
                throughput=None,
                pe_utilization=None,
                area=None,
                power=None,
                edp=None,
                wall_seconds=0.0,
                cloud_cost_usd=0.0,
                log_uri="",
                evidence=("hardware.status",),
                error="hardware candidate gate failed",
            )
        result = self.adapter.evaluate(spec, candidate)
        if result.cloud_cost_usd < 0 or result.wall_seconds < 0:
            raise ValueError("evaluator returned invalid cost or duration")
        return result
