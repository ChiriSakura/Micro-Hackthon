"""The CHIA driver/control plane; it is deliberately not a sixth agent."""

from __future__ import annotations

from dataclasses import replace

from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.schemas.models import ExperimentSpec, RunReport, digest_json, run_report_from_dict
from fast.storage import ExperimentStore


class FiveAgentFlow:
    def __init__(
        self,
        kernel: KernelAgent,
        compiler: CompilerAgent,
        uarch: UArchAgent,
        evaluator: EvaluatorAgent,
        critic: CriticAgent,
        *,
        store: ExperimentStore | None = None,
    ):
        self.kernel = kernel
        self.compiler = compiler
        self.uarch = uarch
        self.evaluator = evaluator
        self.critic = critic
        self.store = store

    def run(self, spec: ExperimentSpec, *, template_id: str) -> RunReport:
        key = f"{spec.experiment_id}/{spec.candidate_id}"
        cache_input = {"spec": spec, "template_id": template_id}
        if self.store is not None:
            cached = self.store.get(key, "report", digest_json(cache_input))
            if cached is not None:
                return replace(
                    run_report_from_dict(cached),
                    cache_hits=("kernel", "compiler", "uarch", "evaluator", "critic"),
                )

        kernel = self.kernel.run(spec)
        compiler = self.compiler.run(kernel)
        hardware = self.uarch.run(compiler, template_id=template_id)
        evaluation = self.evaluator.run(spec, hardware)
        critique = self.critic.run(spec, kernel, compiler, hardware, evaluation)
        report = RunReport(spec, kernel, compiler, hardware, evaluation, critique)
        if self.store is not None:
            self.store.put(key, "kernel", spec, kernel)
            self.store.put(key, "compiler", kernel, compiler)
            self.store.put(key, "uarch", compiler, hardware)
            self.store.put(key, "evaluator", (spec, hardware), evaluation)
            self.store.put(key, "critic", (spec, kernel, compiler, hardware, evaluation), critique)
            self.store.put(key, "report", cache_input, report)
        return report
