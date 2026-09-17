"""Backend boundaries; implementations may run locally, through Slurm, or on GCP."""

from __future__ import annotations

from typing import Protocol

from fast.schemas.models import (
    CompilerSchedule,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelResult,
)


class KernelAdapter(Protocol):
    def evaluate(self, spec: ExperimentSpec) -> KernelResult: ...


class EvaluationAdapter(Protocol):
    def evaluate(
        self,
        spec: ExperimentSpec,
        candidate: HardwareCandidate,
        # 评估的对象是 (workload, plan, hardware) 三元组。
        #
        # `plan` 必须传：候选只装硬件字段，`tile_*` / `divider_stages` /
        # `bank_count` 都不在里面，从候选反推只能猜——猜成默认的 0 级除法器
        # 就是 14.78 ns 而计划里是 1.98 ns，评的不是被规划的那个点。
        #
        # `kernel` 必须传：闭环里每一轮的候选都不同，而稀疏度直接决定周期数。
        # 在构造时绑死一个 workload，会让每一轮都用第 0 轮的数打分。
        plan: CompilerSchedule | None = None,
        kernel: KernelResult | None = None,
    ) -> EvaluationResult: ...
