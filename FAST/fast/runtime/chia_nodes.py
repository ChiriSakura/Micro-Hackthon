"""CHIA graph nodes for the five domain agents.

Resource requirements are intentionally supplied per dispatch. The same graph
can therefore target local Ray, Slurm-hosted workers, or GCP workers without
changing agent code.
"""

from __future__ import annotations

from chia.base.ChiaFunction import ChiaFunction

from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.adapters.base import EvaluationAdapter, KernelAdapter
from fast.adapters.synthesis import SynthesisResult, YosysSynthesisAdapter
from fast.schemas.models import (
    CompilerSchedule,
    Critique,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelResult,
)


@ChiaFunction(num_cpus=1, max_retries=1)
def kernel_node(spec: ExperimentSpec, adapter: KernelAdapter) -> KernelResult:
    return KernelAgent(adapter).run(spec)


@ChiaFunction(num_cpus=1, max_retries=1)
def compiler_node(kernel: KernelResult) -> CompilerSchedule:
    return CompilerAgent().run(kernel)


@ChiaFunction(num_cpus=1, max_retries=1)
def uarch_node(
    schedule: CompilerSchedule,
    agent: UArchAgent,
    template_id: str,
) -> HardwareCandidate:
    return agent.run(schedule, template_id=template_id)


@ChiaFunction(num_cpus=1, max_retries=1)
def evaluator_node(
    spec: ExperimentSpec,
    hardware: HardwareCandidate,
    adapter: EvaluationAdapter,
) -> EvaluationResult:
    return EvaluatorAgent(adapter).run(spec, hardware)


@ChiaFunction(num_cpus=0.25, max_retries=1)
def critic_node(
    spec: ExperimentSpec,
    kernel: KernelResult,
    compiler: CompilerSchedule,
    hardware: HardwareCandidate,
    evaluation: EvaluationResult,
) -> Critique:
    return CriticAgent().run(spec, kernel, compiler, hardware, evaluation)


RESOURCE_LABELS = {
    "kernel": {"fast_dynax_gpu": 1.0},
    "compiler": {"fast_cpu": 1.0},
    "uarch": {"fast_chisel": 1.0},
    "evaluator": {"fast_verilator": 1.0},
    "critic": {"fast_head": 0.01},
}


# 综合不属于五个 Agent 中的任何一个：它是 Evaluator 的一个证据来源，
# 但资源画像完全不同——CPU 密集、单模块之间彼此独立、一次几秒到几分钟。
# 所以它是自己的节点，可以并行铺开到任意 worker 上。
#
# `resources={"synthesis": 1}` 让集群配置决定它落在哪里：本地 Ray、
# Slurm 计算节点，或 GCP worker。节点自己不知道也不需要知道。
@ChiaFunction(num_cpus=4, max_retries=1, resources={"synthesis": 1})
def synthesis_node(
    adapter: YosysSynthesisAdapter,
    verilog: str,
    top_module: str,
) -> SynthesisResult:
    """综合一个模块，返回工具量出来的单元面积。"""
    from pathlib import Path

    return adapter.synthesize(Path(verilog), top_module)
