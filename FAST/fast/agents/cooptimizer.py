"""Joint Compiler/µArch exploration.

Table II keeps the two agents separate - different inputs, outputs and stopping
criteria - but §II.A has them "jointly explore the coupled software-hardware
space". Both are true, and this is how: each agent still owns its own decision
and its own contract, while the pair is proposed, constrained and scored
together, because a schedule and an array are only meaningful against each other.

Ownership, mirroring the Kernel Agent:
- the proposer suggests co-design points;
- the CoOptimizer owns feasibility, scoring and the frontier;
- neither may bypass the verified-template gate.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import time
from typing import Protocol

from fast.agents.codesign import (
    CoDesignPoint,
    CoDesignSpace,
    estimate,
    pe_utilisation,
    to_hardware,
    to_schedule,
    violations,
    working_set_bytes,
)
from fast.agents.templates import TemplateRegistry
from fast.schemas.models import (
    ArchSpecs,
    CompilerSchedule,
    HardwareCandidate,
    KernelResult,
    Status,
)


@dataclass(frozen=True)
class CoDesignResult:
    """One evaluated pair: the schedule, the hardware, and what it would cost."""

    point: CoDesignPoint
    schedule: CompilerSchedule
    hardware: HardwareCandidate
    metrics: dict[str, float]
    feasible: bool
    violations: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoDesignReport:
    spec_sequence_length: int
    fidelity: str
    evaluated: int
    feasible: int
    best: CoDesignResult | None
    frontier: tuple[CoDesignResult, ...]
    rejected_examples: tuple[str, ...]
    wall_seconds: float
    rounds: int = 0
    stopped_because: str = ""


class CoDesignProposer(Protocol):
    name: str

    def propose(
        self,
        kernel: KernelResult,
        specs: ArchSpecs,
        space: CoDesignSpace,
        history: tuple[CoDesignResult, ...],
        count: int,
    ) -> tuple[CoDesignPoint, ...]: ...


class GuidedProposer:
    """Deterministic control, guided by the kernel profile rather than by a grid.

    The full product space is far larger than any measurement budget, so the
    opening batch is derived from what the kernel measured: the row imbalance
    sets the queue depth worth trying, and the retained fraction sets how many
    lanes can be kept fed.
    """

    name = "guided"

    def propose(self, kernel, specs, space, history, count):
        seen = {_key(item.point) for item in history}
        picked: list[CoDesignPoint] = []

        imbalance = max(1.0, kernel.profile.load_imbalance) if kernel.profile else 1.0
        # Depth that recovers most of the loss: utilisation 1/(1+(I-1)/(1+D)).
        wanted_queue = min(space.queue_depth, key=lambda d: abs(pe_utilisation(kernel.profile, d) - 0.9))

        for point in _ordered_candidates(kernel, specs, space, wanted_queue, imbalance):
            key = _key(point)
            if key in seen:
                continue
            seen.add(key)
            picked.append(point)
            if len(picked) == count:
                break
        return tuple(picked)


SRAM_CHOICES = (65536, 131072, 262144)


def _ordered_candidates(kernel, specs, space, wanted_queue, imbalance):
    """Candidates in the order worth spending a budget on.

    Widest arrays first, because the retained work is what has to be covered;
    for each shape the smallest SRAM that actually holds the tile, because
    over-provisioning memory costs area without buying cycles.
    """
    for rows in sorted(space.num_rows, reverse=True):
        for cols in sorted(space.pe_per_row, reverse=True):
            if rows * cols > specs.max_pe:
                continue
            for tile_k in space.tile_k:
                for reg_width in space.reg_width:
                    if tile_k % reg_width:
                        continue
                    for width in specs.data_widths:
                        for double in (True, False):
                            base = CoDesignPoint(
                                tile_q=64, tile_k=tile_k, tile_d=64,
                                parallelism=min(rows, max(space.parallelism)),
                                double_buffer=double,
                                num_rows=rows, pe_per_row=cols, reg_width=reg_width,
                                data_width=width, sram_bytes=SRAM_CHOICES[0],
                                queue_depth=wanted_queue,
                            )
                            fitted = _smallest_sram_that_fits(base)
                            if fitted is not None:
                                yield fitted


def _smallest_sram_that_fits(point: CoDesignPoint) -> CoDesignPoint | None:
    for sram in SRAM_CHOICES:
        candidate = replace(point, sram_bytes=sram)
        if working_set_bytes(candidate) <= sram:
            return candidate
    return None


def _key(point: CoDesignPoint) -> tuple:
    return tuple(sorted(point.__dict__.items()))


class CoOptimizer:
    """Explores schedule/hardware pairs against one kernel result."""

    FIDELITY = "L1-analytical"

    def __init__(
        self,
        registry: TemplateRegistry | None = None,
        *,
        template_id: str = "repe_array",
        allow_unverified: bool = False,
    ):
        self.registry = registry or TemplateRegistry()
        self.template_id = template_id
        # Composing an unverified template is the one thing the µArch Agent may
        # never do silently; exploring the cost space with one is legitimate but
        # must be asked for, and the candidate still reports FAILED.
        self.allow_unverified = allow_unverified

    def run(
        self,
        kernel: KernelResult,
        *,
        sequence_length: int,
        specs: ArchSpecs | None = None,
        space: CoDesignSpace | None = None,
        proposer: CoDesignProposer | None = None,
        budget: int = 24,
        batch: int = 8,
        block_m: int = 64,
        kept_per_block: int = 16,
        patience: int = 2,
        min_improvement: float = 0.02,
        timeout_seconds: float | None = None,
    ) -> CoDesignReport:
        if kernel.status is not Status.PASSED:
            return CoDesignReport(sequence_length, self.FIDELITY, 0, 0, None, (), (
                "kernel quality gate failed; nothing to co-optimise",
            ), 0.0, 0, "kernel gate")

        specs = specs or ArchSpecs()
        space = space or CoDesignSpace()
        proposer = proposer or GuidedProposer()
        template = self.registry.by_id(self.template_id)
        if template is None:
            return CoDesignReport(sequence_length, self.FIDELITY, 0, 0, None, (), (
                f"template {self.template_id!r} is not in the registry",
            ), 0.0, 0, "unknown template")
        if not template.verified and not self.allow_unverified:
            return CoDesignReport(sequence_length, self.FIDELITY, 0, 0, None, (), (
                f"{template.template_id} is unverified: {template.blocking_issue}",
            ), 0.0, 0, "verified-template gate")

        started = time.time()
        history: tuple[CoDesignResult, ...] = ()
        rejected: list[str] = []
        # Table II gives the Compiler Agent "Reduction or timeout" as its stopping
        # criterion, so the loop runs while rounds keep reducing EDP and stops
        # when they stop paying for themselves.
        best_edp = float("inf")
        stalled = 0
        rounds = 0
        stopped = "budget exhausted"

        while len(history) < budget:
            if timeout_seconds is not None and time.time() - started >= timeout_seconds:
                stopped = "timeout"
                break
            want = min(batch, budget - len(history))
            points = proposer.propose(kernel, specs, space, history, want)
            if not points:
                stopped = "proposer exhausted the space"
                break
            rounds += 1
            for point in points:
                problems = violations(
                    point, kernel, specs, self.registry,
                    block_m=block_m, kept_per_block=kept_per_block,
                )
                metrics = estimate(
                    point, kernel, sequence_length,
                    block_m=block_m, kept_per_block=kept_per_block,
                )
                rationale = _rationale(kernel, point, metrics)
                history += (CoDesignResult(
                    point=point,
                    schedule=to_schedule(point, rationale, metrics["pe_utilization"]),
                    hardware=to_hardware(
                        point, template, block_m=block_m, kept_per_block=kept_per_block
                    ),
                    metrics=metrics,
                    feasible=not problems,
                    violations=problems,
                    rationale=rationale,
                ),)
                if problems:
                    rejected.extend(problems[:1])

            round_best = min(
                (item.metrics["edp"] for item in history if item.feasible),
                default=float("inf"),
            )
            if round_best < best_edp * (1.0 - min_improvement):
                best_edp = round_best
                stalled = 0
            else:
                stalled += 1
                if stalled >= patience:
                    stopped = f"no EDP reduction for {patience} rounds"
                    break

        feasible = [item for item in history if item.feasible]
        best = min(feasible, key=lambda item: item.metrics["edp"]) if feasible else None
        return CoDesignReport(
            spec_sequence_length=sequence_length,
            fidelity=self.FIDELITY,
            evaluated=len(history),
            feasible=len(feasible),
            best=best,
            frontier=_frontier(feasible),
            rejected_examples=tuple(dict.fromkeys(rejected))[:8],
            wall_seconds=round(time.time() - started, 3),
            rounds=rounds,
            stopped_because=stopped,
        )


def _rationale(kernel, point: CoDesignPoint, metrics: dict[str, float]) -> tuple[str, ...]:
    lines = [
        f"kernel_sparsity={kernel.actual_sparsity:.4f}",
        f"block_occupancy={kernel.block_occupancy:.4f}",
        f"lanes={point.mac_lanes} queue_depth={point.queue_depth}",
        f"predicted_pe_utilization={metrics['pe_utilization']:.4f}",
    ]
    if kernel.profile is not None:
        lines.insert(1, f"load_imbalance={kernel.profile.load_imbalance:.4f}")
    return tuple(lines)


def _frontier(results: list[CoDesignResult]) -> tuple[CoDesignResult, ...]:
    """Points nothing else beats on both cycles and area."""
    front = []
    for item in results:
        dominated = any(
            other.metrics["cycles"] <= item.metrics["cycles"]
            and other.metrics["area"] <= item.metrics["area"]
            and (
                other.metrics["cycles"] < item.metrics["cycles"]
                or other.metrics["area"] < item.metrics["area"]
            )
            for other in results
        )
        if not dominated:
            front.append(item)
    return tuple(front)
