from __future__ import annotations

from fast.adapters.base import KernelAdapter
from fast.schemas.models import ExperimentSpec, KernelResult


class KernelAgent:
    """Runs a DynaX-compatible measurement and enforces the quality gate."""

    def __init__(self, adapter: KernelAdapter):
        self.adapter = adapter

    def run(self, spec: ExperimentSpec) -> KernelResult:
        result = self.adapter.evaluate(spec)
        if result.quality_loss < 0 or not 0 <= result.actual_sparsity <= 1:
            raise ValueError("kernel adapter returned invalid metrics")
        return result
