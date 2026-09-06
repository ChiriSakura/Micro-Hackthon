"""Critic Agent：证据绑定的瓶颈归因，以及下一轮的 mutation。

在流水线里的位置：Kernel → Compiler → µArch → Evaluator → **Critic**。

规则版实现。它的契约不是「结论对不对」，而是**每个结论都必须指向产生它的
那条证据**：`Critique.evidence` 里放的是字段路径（如
`evaluation.functional_passed`），不是自然语言理由。这样做的目的是让
LLM 版本后续可以直接替换实现而不改 schema——归因的可审计性来自结构，
不来自模型。

归因到 `Layer`（KERNEL / COMPILER / UARCH / EVALUATOR）之后，
`Mutation` 描述下一轮该改哪一层的哪个字段、预期效果和风险。
跨层归因需要各 Agent 的搜索历史，那份共享数据在
`fast/storage/experiment_db.py` 的 `cross_layer` 视图里。
"""

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
