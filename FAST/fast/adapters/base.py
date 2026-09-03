"""Backend boundaries; implementations may run locally, through Slurm, or on GCP."""

from __future__ import annotations

from typing import Protocol

from fast.schemas.models import EvaluationResult, ExperimentSpec, HardwareCandidate, KernelResult


class KernelAdapter(Protocol):
    def evaluate(self, spec: ExperimentSpec) -> KernelResult: ...


class EvaluationAdapter(Protocol):
    def evaluate(
        self, spec: ExperimentSpec, candidate: HardwareCandidate
    ) -> EvaluationResult: ...
