"""CHIA graph nodes for the five domain agents.

Resource requirements are intentionally supplied per dispatch. The same graph
can therefore target local Ray, Slurm-hosted workers, or GCP workers without
changing agent code.
"""

from __future__ import annotations

from chia.base.ChiaFunction import ChiaFunction

from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.adapters.base import EvaluationAdapter, KernelAdapter
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
