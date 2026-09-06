"""Who decides which kernel configuration to measure next.

The Kernel Agent's job is not to run one measurement; it is to spend a fixed
measurement budget well. That decision is isolated here behind one protocol so
the same agent, the same search space and the same gate can be driven by a rule
or by an LLM, and the two compared under an equal budget.

Every proposer returns labels from :class:`KernelSearchSpace`. A label outside
it is rejected before anything is measured, so a hallucinated configuration
costs nothing and shows up in the report's ``rejected`` list.
"""

from __future__ import annotations

import json
import re
from typing import Protocol

from fast.schemas.models import (
    ExperimentSpec,
    KernelCandidate,
    KernelMeasurement,
    KernelSearchSpace,
    Status,
)


class KernelProposer(Protocol):
    name: str

    def propose(
        self,
        spec: ExperimentSpec,
        space: KernelSearchSpace,
        history: tuple[KernelMeasurement, ...],
        count: int,
    ) -> tuple[KernelCandidate, ...]: ...


def _measured(history: tuple[KernelMeasurement, ...]) -> set[str]:
    return {item.label for item in history}


def _scored(history: tuple[KernelMeasurement, ...]) -> list[KernelMeasurement]:
    return [item for item in history if item.within]


class SweepProposer:
    """Deterministic control: coarse sweep, then refine around the frontier.

    Round 1 samples the space widely so the frontier is not guessed from one
    corner. Later rounds bisect between the sparsest configuration still inside
    the epsilon budget and the cheapest one outside it, which is where the
    frontier actually turns.
    """

    name = "sweep"

    def propose(
        self,
        spec: ExperimentSpec,
        space: KernelSearchSpace,
        history: tuple[KernelMeasurement, ...],
        count: int,
    ) -> tuple[KernelCandidate, ...]:
        labels = [item for item in space.labels() if item not in _measured(history)]
        if not labels:
            return ()

        if not history:
            picked = self._spread(labels, count)
            reason = ("no measurements yet",)
            effect = "map the accuracy/sparsity trade-off before refining"
        else:
            picked, reason, effect = self._refine(spec, labels, history, count)

        return tuple(
            KernelCandidate(
                label=label,
                proposed_by=self.name,
                rationale=reason,
                expected_effect=effect,
            )
            for label in picked
        )

    def _spread(self, labels: list[str], count: int) -> list[str]:
        """Take an evenly spaced slice so the first round covers the range."""
        if count >= len(labels):
            return labels
        step = len(labels) / count
        return [labels[int(index * step)] for index in range(count)]

    def _refine(self, spec, labels, history, count):
        inside = [item for item in _scored(history) if item.quality_loss <= spec.epsilon]
        outside = [item for item in _scored(history) if item.quality_loss > spec.epsilon]
        if inside and outside:
            edge = max(inside, key=lambda item: item.actual_sparsity)
            over = min(outside, key=lambda item: item.actual_sparsity)
            target = (edge.actual_sparsity + over.actual_sparsity) / 2
            reason = (
                f"{edge.label} holds {edge.actual_sparsity:.3f} sparsity within epsilon",
                f"{over.label} exceeds it at {over.actual_sparsity:.3f}",
            )
            effect = f"probe the frontier near {target:.3f} sparsity"
        elif inside:
            edge = max(inside, key=lambda item: item.actual_sparsity)
            target = min(0.99, edge.actual_sparsity + 0.05)
            reason = (f"everything measured is inside epsilon; sparsest is {edge.label}",)
            effect = "push sparsity until the accuracy budget binds"
        else:
            measured = [item.actual_sparsity for item in _scored(history)]
            target = (min(measured) if measured else 0.5) - 0.05
            reason = ("no configuration met the accuracy budget yet",)
            effect = "retreat to a looser budget"
        return rank_by_measured_sparsity(labels, history, target)[:count], reason, effect


def _family(label: str) -> str:
    return label.split(":")[0]


def _budget(label: str) -> float | None:
    """How much the label keeps per block, in comparable units across families.

    This orders candidates *within* a family; it is deliberately not a sparsity
    estimate. An earlier version guessed absolute sparsity from these numbers and
    was wrong by up to 0.35 on X:M, because X:M also drops whole blocks whose
    probability mass falls below its lower threshold - a branch no closed form
    sees. Ordering is all that is needed, and ordering is what this gives.
    """
    head, *rest = label.split(":")
    if head == "xm" and len(rest) == 3:
        high, low, _ = (int(value) for value in rest)
        return (high + low) / 2
    if head == "nm" and len(rest) == 2:
        return float(int(rest[0]))
    if head == "topk" and rest:
        return float(int(rest[0]))
    return None


def rank_by_measured_sparsity(
    labels: list[str], history: tuple[KernelMeasurement, ...], target: float
) -> list[str]:
    """Order unmeasured labels by how close they should land to ``target``.

    Sparsity is interpolated from what this run actually measured in the same
    family, so the ordering improves as the search proceeds and never depends on
    a hand-written model of the kernel. Families with no measurement yet sort
    first: unexplored is more informative than a guess.
    """
    measured: dict[str, list[tuple[float, float]]] = {}
    for item in history:
        if not item.within:
            continue
        budget = _budget(item.label)
        if budget is not None:
            measured.setdefault(_family(item.label), []).append((budget, item.actual_sparsity))

    def distance(label: str) -> tuple[int, float]:
        family = _family(label)
        budget = _budget(label)
        points = sorted(measured.get(family, ()))
        if budget is None or not points:
            return (0, 0.0)  # unmeasured family or parameterless method: explore it
        return (1, abs(_interpolate(points, budget) - target))

    return sorted(labels, key=distance)


def _interpolate(points: list[tuple[float, float]], budget: float) -> float:
    """Piecewise-linear in (kept-per-block -> measured sparsity), clamped at the ends."""
    if len(points) == 1:
        return points[0][1]
    if budget <= points[0][0]:
        return points[0][1]
    if budget >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= budget <= x1:
            if x1 == x0:
                return y0
            weight = (budget - x0) / (x1 - x0)
            return y0 + weight * (y1 - y0)
    return points[-1][1]


PROMPT = """You are the Kernel Agent in a hardware/software co-design loop for \
dynamic sparse attention. You choose which attention configurations to measure next.

Goal: find configurations that prune as much of the attention matrix as possible \
while keeping the relative perplexity increase at or below epsilon={epsilon}.

Two measured quantities matter to the hardware, not just sparsity:
- block_occupancy: the fraction of 64-wide column blocks that still hold a kept
  value. Lower is better: an accelerator can skip a whole empty block. Two
  methods at the same sparsity can differ completely here.
- index_entropy: how evenly the kept columns are spread. Near 1.0 means spread out.

Model: {model}
Dataset: {dataset}, sequence length {sequence_length}
Measurement budget left: {remaining} configurations, choose {count} now.

Legal labels (you MUST choose only from these, exactly as written):
{labels}

Already measured:
{history}

Reply with ONLY a JSON array, no prose, no code fence. Each element:
  {{"label": "<one legal label>",
    "rationale": ["<cites a specific measured number or states this is unexplored>"],
    "expected_effect": "<what you expect to change and why>"}}

Rules: propose exactly {count} distinct labels that are NOT already measured. \
Each rationale must reference a measured value from the table above, or say \
plainly that the region is unmeasured. Do not invent labels."""


class LLMProposer:
    """Lets a language model spend the measurement budget, under the same gate.

    The model never touches the measurement or the accuracy gate; it only says
    what to try next, and every label it returns is validated against the search
    space. It is deliberately given the hardware-facing metrics (block occupancy,
    index entropy) as well as accuracy, because that trade-off is the thing a
    single-layer sweep cannot see.
    """

    def __init__(self, llm, *, model_name: str = "llm", fallback: KernelProposer | None = None):
        self.llm = llm
        self.name = f"llm:{model_name}"
        self.fallback = fallback if fallback is not None else SweepProposer()
        self.rejected: list[str] = []

    def propose(
        self,
        spec: ExperimentSpec,
        space: KernelSearchSpace,
        history: tuple[KernelMeasurement, ...],
        count: int,
    ) -> tuple[KernelCandidate, ...]:
        legal = [label for label in space.labels() if label not in _measured(history)]
        if not legal:
            return ()

        remaining = max(0, spec.budget.max_evaluations - len(history))
        prompt = PROMPT.format(
            epsilon=spec.epsilon,
            model=spec.model,
            dataset=spec.dataset,
            sequence_length=spec.sequence_length,
            remaining=remaining,
            count=count,
            labels="\n".join(f"  {label}" for label in legal),
            history=_history_table(history),
        )

        try:
            reply = self.llm.prompt(prompt)
            text = reply.result if hasattr(reply, "result") else str(reply)
            success = getattr(reply, "success", True)
        except Exception as exc:  # a proposer outage must not end the search
            self.rejected.append(f"llm call failed: {type(exc).__name__}: {exc}")
            return self.fallback.propose(spec, space, history, count)

        if not success:
            self.rejected.append(f"llm returned failure: {getattr(reply, 'stderr', '')[:200]}")
            return self.fallback.propose(spec, space, history, count)

        candidates = self._parse(text, space, set(legal), count)
        if not candidates:
            self.rejected.append("llm proposed nothing usable; falling back to the sweep")
            return self.fallback.propose(spec, space, history, count)
        return candidates

    def _parse(self, text, space, legal, count) -> tuple[KernelCandidate, ...]:
        payload = _extract_json_array(text)
        if payload is None:
            self.rejected.append(f"reply was not a JSON array: {text.strip()[:160]}")
            return ()

        picked: list[KernelCandidate] = []
        seen: set[str] = set()
        for item in payload:
            if not isinstance(item, dict) or "label" not in item:
                self.rejected.append(f"entry without a label: {str(item)[:120]}")
                continue
            label = str(item["label"]).strip()
            if label in seen:
                self.rejected.append(f"{label}: proposed twice in one round")
                continue
            if label not in legal:
                why = "outside the search space" if not space.contains(label) else "already measured"
                self.rejected.append(f"{label}: {why}")
                continue
            rationale = item.get("rationale") or ()
            if isinstance(rationale, str):
                rationale = (rationale,)
            seen.add(label)
            picked.append(
                KernelCandidate(
                    label=label,
                    proposed_by=self.name,
                    rationale=tuple(str(entry) for entry in rationale)[:4],
                    expected_effect=str(item.get("expected_effect", ""))[:300],
                )
            )
            if len(picked) == count:
                break
        return tuple(picked)


def _history_table(history: tuple[KernelMeasurement, ...]) -> str:
    if not history:
        return "  (nothing measured yet)"
    rows = [
        "  label                 quality_loss  sparsity  block_occupancy  index_entropy",
    ]
    for item in history:
        if item.status is not Status.PASSED:
            rows.append(f"  {item.label:<20}  FAILED ({item.error or 'no result'})")
            continue
        rows.append(
            f"  {item.label:<20}  {item.quality_loss:>+11.4f}  {item.actual_sparsity:>8.4f}"
            f"  {item.block_occupancy:>15.4f}  {item.index_entropy:>13.4f}"
        )
    return "\n".join(rows)


def _extract_json_array(text: str):
    """Pull the JSON array out of a reply that may be fenced or prefaced."""
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, list) else None
