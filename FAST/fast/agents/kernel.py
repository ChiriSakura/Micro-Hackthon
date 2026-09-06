"""The Kernel Agent: spend a measurement budget, not just take one measurement.

The agent owns three things a proposer must not touch: what gets measured (the
adapter), whether a result clears the accuracy budget (the epsilon gate), and
what counts as a frontier. A proposer only says which configurations to try
next, so a rule and an LLM can be swapped and compared under identical
conditions.
"""

from __future__ import annotations

import time

from fast.adapters.base import KernelAdapter
from fast.agents.proposers import KernelProposer, SweepProposer
from fast.schemas.models import (
    ExperimentSpec,
    KernelMeasurement,
    KernelResult,
    KernelSearchReport,
    KernelSearchSpace,
    Status,
)


class KernelAgent:
    """Runs DynaX-backed measurements and enforces the quality gate."""

    def __init__(self, adapter: KernelAdapter):
        self.adapter = adapter

    def run(self, spec: ExperimentSpec) -> KernelResult:
        """Measure the single candidate named by the spec."""
        result = self.adapter.evaluate(spec)
        if result.quality_loss < 0 or not 0 <= result.actual_sparsity <= 1:
            raise ValueError("kernel adapter returned invalid metrics")
        return result

    def search(
        self,
        spec: ExperimentSpec,
        *,
        proposer: KernelProposer | None = None,
        space: KernelSearchSpace | None = None,
        batch: int = 4,
        db=None,
    ) -> KernelSearchReport:
        """Spend ``spec.budget.max_evaluations`` measurements on the space.

        Rounds are batched because the expensive part is loading the model, not
        measuring one more configuration: the adapter evaluates a whole round in
        a single process.

        ``db`` is an optional :class:`~fast.storage.ExperimentDB`. It is injected
        rather than owned so the agent stays a pure function of its inputs in
        tests, and so recording a search never changes what the search does.
        """
        proposer = proposer or SweepProposer()
        space = space or KernelSearchSpace(max_sequence_length=spec.sequence_length)
        # Budget already refuses a non-positive max_evaluations, so there is no
        # second guard here: one owner per invariant.
        budget = spec.budget.max_evaluations

        started = time.time()
        history: tuple[KernelMeasurement, ...] = ()
        baseline: float | None = None
        rounds = 0
        run_id = db.start_run(spec, proposer=proposer.name) if db is not None else None
        seen_rejections = 0

        while len(history) < budget:
            want = min(batch, budget - len(history))
            candidates = proposer.propose(spec, space, history, want)
            if not candidates:
                break
            rounds += 1
            measured, round_baseline = self.adapter.measure(spec, candidates)
            if baseline is None:
                baseline = round_baseline
            history += tuple(measured)
            if db is not None:
                db.record_proposals(run_id, rounds, "kernel", candidates)
                db.record_measurements(run_id, measured)
                notes = list(getattr(proposer, "rejected", ()) or ())
                db.record_rejections(run_id, rounds, "kernel", notes[seen_rejections:])
                seen_rejections = len(notes)

        if db is not None:
            db.finish_run(run_id)
        rejected = tuple(getattr(proposer, "rejected", ()) or ())
        accepted = [item for item in history if item.within and item.quality_loss <= spec.epsilon]
        best = max(accepted, key=lambda item: item.actual_sparsity) if accepted else None
        return KernelSearchReport(
            spec=spec,
            proposer=proposer.name,
            baseline_metric=baseline,
            measurements=history,
            pareto=pareto_front(history),
            best=best,
            rounds=rounds,
            rejected=rejected,
            wall_seconds=round(time.time() - started, 3),
        )


def pareto_front(history: tuple[KernelMeasurement, ...]) -> tuple[str, ...]:
    """Configurations nothing else beats on both sparsity and quality loss.

    Block occupancy is reported but deliberately not part of the frontier: it is
    the compiler and micro-architecture layers that turn low occupancy into
    speed, so the kernel layer must not pre-judge it.
    """
    scored = [item for item in history if item.within]
    front = []
    for item in scored:
        dominated = any(
            other.actual_sparsity >= item.actual_sparsity
            and other.quality_loss <= item.quality_loss
            and (
                other.actual_sparsity > item.actual_sparsity
                or other.quality_loss < item.quality_loss
            )
            for other in scored
        )
        if not dominated:
            front.append(item.label)
    return tuple(front)
