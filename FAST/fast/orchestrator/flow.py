"""The CHIA driver/control plane; it is deliberately not a sixth agent."""

from __future__ import annotations

from dataclasses import replace

from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.agents.cooptimizer import CoDesignReport, CoOptimizer
from fast.schemas.models import (
    ExperimentSpec,
    KernelResult,
    KernelSearchReport,
    RunReport,
    Status,
    digest_json,
    run_report_from_dict,
)
from fast.storage import ExperimentDB, ExperimentStore


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
        db: ExperimentDB | None = None,
        cooptimizer: CoOptimizer | None = None,
    ):
        self.kernel = kernel
        self.compiler = compiler
        self.uarch = uarch
        self.evaluator = evaluator
        self.critic = critic
        self.store = store
        self.db = db
        # When present, the Compiler and uArch agents are explored jointly
        # instead of in sequence: a schedule and an array constrain each other.
        self.cooptimizer = cooptimizer

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
        report = self._downstream(spec, kernel, template_id, label=spec.candidate_id)
        if self.store is not None:
            self._cache(key, cache_input, report)
        return report

    def _cache(self, key: str, cache_input: dict, report: RunReport) -> None:
        """Cache each stage on the inputs that produced it, plus the whole report."""
        spec, kernel = report.spec, report.kernel
        compiler, hardware = report.compiler, report.hardware
        evaluation, critique = report.evaluation, report.critique
        self.store.put(key, "kernel", spec, kernel)
        self.store.put(key, "compiler", kernel, compiler)
        self.store.put(key, "uarch", compiler, hardware)
        self.store.put(key, "evaluator", (spec, hardware), evaluation)
        self.store.put(key, "critic", (spec, kernel, compiler, hardware, evaluation), critique)
        self.store.put(key, "report", cache_input, report)

    def search_then_build(
        self,
        spec: ExperimentSpec,
        *,
        template_id: str,
        proposer=None,
        space=None,
        batch: int = 4,
    ) -> tuple[KernelSearchReport, RunReport | None]:
        """Search the kernel space, then hand the winner to the rest of the loop.

        The Kernel Agent's job in the proposal is workload characterisation, so
        the whole frontier is kept; what flows downstream is the sparsest
        configuration that stayed inside the accuracy budget, carrying its
        sparse-index profile with it.
        """
        search = self.kernel.search(spec, proposer=proposer, space=space, batch=batch, db=self.db)
        if search.best is None:
            return search, None

        kernel = _as_kernel_result(search)
        report = self._downstream(spec, kernel, template_id, label=search.best.label)
        return search, report

    def _downstream(self, spec, kernel, template_id, *, label: str) -> RunReport:
        """Compiler, uArch, Evaluator and Critic, recording each layer as it goes."""
        codesign: CoDesignReport | None = None
        if self.cooptimizer is not None:
            codesign = self.cooptimizer.run(kernel, sequence_length=spec.sequence_length)
            if codesign.best is not None:
                compiler = codesign.best.schedule
                hardware = codesign.best.hardware
            else:
                # The joint search found nothing buildable; fall back so the
                # Critic still receives a typed reason rather than a gap.
                compiler = self.compiler.run(kernel)
                hardware = self.uarch.run(compiler, template_id=template_id)
        else:
            compiler = self.compiler.run(kernel)
            hardware = self.uarch.run(compiler, template_id=template_id)

        evaluation = self.evaluator.run(spec, hardware)
        critique = self.critic.run(spec, kernel, compiler, hardware, evaluation)

        if self.db is not None:
            run_id = self.db.start_run(spec, proposer="flow")
            # The cross_layer view starts from the kernel row, so a candidate that
            # entered through run() rather than a search still needs one; without
            # it every downstream stage is recorded but nothing can be joined.
            self.db.record_measurements(run_id, [_as_measurement(label, kernel)])
            self.db.record_stage(run_id, label, "compiler", compiler)
            self.db.record_stage(run_id, label, "uarch", hardware)
            self.db.record_stage(run_id, label, "evaluator", evaluation)
            self.db.record_attribution(run_id, label, critique)
            self.db.finish_run(run_id)

        self.last_codesign = codesign
        return RunReport(spec, kernel, compiler, hardware, evaluation, critique)


def _as_measurement(label: str, kernel: KernelResult):
    """Widen a single KernelResult into the row shape the shared database joins on."""
    from fast.schemas.models import KernelMeasurement

    return KernelMeasurement(
        label=label,
        status=kernel.status,
        perplexity=kernel.candidate_metric,
        quality_loss=kernel.quality_loss,
        actual_sparsity=kernel.actual_sparsity,
        index_entropy=kernel.index_entropy,
        block_occupancy=kernel.block_occupancy,
        row_kept_min=None,
        row_kept_max=None,
        wall_seconds=None,
        profile=kernel.profile,
        proposed_by="flow",
    )


def _as_kernel_result(search: KernelSearchReport) -> KernelResult:
    """Narrow the winning measurement into the contract the Compiler consumes."""
    best = search.best
    return KernelResult(
        status=Status.PASSED,
        baseline_metric=search.baseline_metric or 0.0,
        candidate_metric=best.perplexity or 0.0,
        metric_name=f"{search.spec.dataset}_perplexity",
        quality_loss=best.quality_loss or 0.0,
        actual_sparsity=best.actual_sparsity,
        index_entropy=best.index_entropy,
        block_occupancy=best.block_occupancy,
        trace_uri=f"search://{search.spec.experiment_id}/{best.label}",
        profile=best.profile,
        evidence=(
            f"selected={best.label}",
            f"proposed_by={best.proposed_by}",
            f"measured={len(search.measurements)} of budget {search.spec.budget.max_evaluations}",
            f"pareto={','.join(search.pareto)}",
            f"quality_loss={best.quality_loss:.6f} <= epsilon={search.spec.epsilon}",
        ),
    )
