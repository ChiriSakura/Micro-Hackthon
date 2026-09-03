from __future__ import annotations

from fast.schemas.models import (
    CompilerSchedule,
    Critique,
    Decision,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelResult,
    Layer,
    Mutation,
    Status,
)


class CriticAgent:
    """Evidence-bound rule critic; an LLM can later propose the same schema."""

    def run(
        self,
        spec: ExperimentSpec,
        kernel: KernelResult,
        compiler: CompilerSchedule | None,
        hardware: HardwareCandidate | None,
        evaluation: EvaluationResult | None,
    ) -> Critique:
        if kernel.status is not Status.PASSED:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.KERNEL,
                decision=Decision.REVERT,
                summary="quality loss exceeds the configured epsilon",
                evidence=("kernel.quality_loss", "spec.epsilon"),
                mutations=(Mutation(
                    layer=Layer.KERNEL,
                    field="sparsity_x",
                    operation="increase",
                    value=1,
                    expected_effect="retain more attention values and reduce quality loss",
                    risk="lower sparsity and speedup",
                ),),
            )
        if hardware is None or hardware.status is not Status.PASSED:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.UARCH,
                decision=Decision.REVERT,
                summary="no verified hardware candidate reached evaluation",
                evidence=("hardware.status", "hardware.verified_template"),
            )
        if evaluation is None or not evaluation.functional_passed:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.EVALUATOR,
                decision=Decision.REVERT,
                summary="functional verification failed",
                evidence=("evaluation.functional_passed", "evaluation.log_uri"),
            )
        if evaluation.pe_utilization is not None and evaluation.pe_utilization < 0.70:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.COMPILER,
                decision=Decision.CONTINUE,
                summary="PE utilization is below the initial target",
                evidence=("evaluation.pe_utilization", "compiler.parallelism"),
                mutations=(Mutation(
                    layer=Layer.COMPILER,
                    field="parallelism",
                    operation="increase",
                    value=2,
                    expected_effect="expose more independent sparse blocks",
                    risk="higher buffering and routing pressure",
                ),),
            )
        return Critique(
            status=Status.PASSED,
            attribution=Layer.EVALUATOR,
            decision=Decision.STOP,
            summary="single-candidate acceptance gates passed",
            evidence=("kernel.quality_loss", "evaluation.functional_passed", "evaluation.pe_utilization"),
        )
