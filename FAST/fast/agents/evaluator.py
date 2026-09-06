"""Evaluator Agent：把某一档保真度的后端归一化成统一的评估契约。

在流水线里的位置：Kernel → Compiler → µArch → **Evaluator** → Critic。

这个 Agent 自己不测量任何东西，它只保证**无论后端是哪一档，出来的
`EvaluationResult` 形状一致、并且诚实标注自己是哪一档**：

    L0-deterministic            合成数据，只验证控制流    functional_passed 恒 False
    L1-analytical-shared-model  一阶代价模型              functional_passed 恒 False
    L2-rtl-simulation           Chisel→Verilator→golden   functional_passed 是实测

`fidelity` 字段会一路传到 Critic 的归因里，所以它不是「精度声明」，
是「这个数字是怎么来的」。L1 那个 `shared-model` 后缀尤其重要：
协同优化器用代价模型挑出获胜设计，Evaluator 再用同一个模型给它打分——
这时候「一致」是算术，不是确认。

后端见 `fast/adapters/`。
"""

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
