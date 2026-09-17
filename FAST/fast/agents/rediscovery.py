"""Search original DynaX algorithm parameters with downstream hardware feedback.

Quality is measured by DynaX, hardware performance is currently L1. No default
algorithm label, preselected hardware design, or old winner seeds this search.
The caller supplies every domain, constraint and budget explicitly.
"""
from dataclasses import asdict, replace
import json
import math
import random
import time

from fast.agents.codesign import DEFAULT_OBJECTIVE, POWER_COVERAGE
from fast.agents.cooptimizer import CoOptimizer
from fast.agents.critic import CriticAgent
from fast.agents.rediscovery_critic import CriticGuidedProposer, review_search, search_context
from fast.agents.pareto import dominates_vector, valid_vector
from fast.schemas.conversions import kernel_result_from_measurement
from fast.schemas.contract import parse_algorithm
from fast.schemas.models import KernelCandidate, Status, digest_json, to_primitive


class RandomKernelProposer:
    name = "random-kernel"

    def __init__(self, seed):
        self.rng = random.Random(seed)

    def propose(self, spec, space, history, count):
        seen = {m.label for m in history}
        legal = [label for label in space.labels() if label not in seen]
        return tuple(KernelCandidate(label=label, proposed_by=self.name,
                                     rationale=("unmeasured random control",))
                     for label in self.rng.sample(legal, min(count, len(legal))))


def joint_front(designs):
    feasible = [d for d in designs if d["feasible"] and
                valid_vector(DEFAULT_OBJECTIVE.vector(d["metrics"]))]
    survivors = [d for d in feasible if not any(
        dominates_vector(DEFAULT_OBJECTIVE.vector(other["metrics"]),
                         DEFAULT_OBJECTIVE.vector(d["metrics"])) for other in feasible)]
    # Same objective coordinates are one front location, but retain all design
    # identities in `designs` for independent validation and replay.
    unique = {}
    for d in survivors:
        unique.setdefault(DEFAULT_OBJECTIVE.vector(d["metrics"]), d)
    return [unique[key] for key in sorted(unique)]


class DynaXRediscovery:
    def __init__(self, adapter, kernel_proposer, hardware_proposer_factory, *, critic="rule"):
        self.adapter = adapter
        self.kernel_proposer = kernel_proposer
        self.hardware_proposer_factory = hardware_proposer_factory
        self.critic = CriticAgent() if critic == "rule" else critic

    def run(self, spec, *, kernel_space, hardware_space, specs, head_dim,
            kernel_batch, hardware_budget, hardware_batch, checkpoint=None):
        if kernel_space.algorithm != "xm" or kernel_space.threshold_pairs is None or kernel_space.block_ms is None:
            raise ValueError("rediscovery requires explicit XM M and T0/T1 domains")
        if min(kernel_batch, hardware_budget, hardware_batch, head_dim) <= 0:
            raise ValueError("budgets, batch sizes and head_dim must be positive")
        if kernel_space.max_sequence_length != spec.sequence_length:
            raise ValueError("kernel domain and measured sequence length differ")
        started = time.monotonic()
        history, designs, events = [], [], []
        critic_events, pending_kernel = [], {}
        baseline = None
        result = {
            "spec": to_primitive(spec), "kernel_space": asdict(kernel_space),
            "hardware_space": asdict(hardware_space), "constraints": asdict(specs),
            "head_dim": head_dim, "objective": asdict(DEFAULT_OBJECTIVE),
            "power_coverage": POWER_COVERAGE, "quality_evidence": "DynaX perplexity",
            "performance_evidence": "L1-analytical-shared-model; NOT independent PPA",
            "initial_design": None, "old_default_is_search_seed": False,
            "measurements": [], "designs": designs, "rounds": events,
            "frontier": [], "representative": None,
            "representative_policy": "lowest latency on model Pareto front",
            "hardware_budget_per_quality_passing_kernel": hardware_budget,
            "critic_enabled": self.critic is not None,
            "critic_reviews": critic_events,
            "critic_budget_policy": "interventions consume existing proposal slots; no gate relaxation or Critic early-stop",
        }
        while len(history) < spec.budget.max_evaluations:
            if time.monotonic() - started >= spec.budget.max_wall_seconds:
                break
            front = joint_front(designs)
            feedback = {
                "scope": result["performance_evidence"],
                "constraints": result["constraints"],
                "previous_hardware_evaluations": events,
                "joint_front": [{"label": d["label"], "point": d["point"],
                                 "seconds": d["metrics"]["seconds"],
                                 "energy_j": d["metrics"]["energy_j"]} for d in front],
                "critic_reviews": [{"review_id": e["review_id"], "critique": e["critique"],
                                    "outcome": e["outcome"]} for e in critic_events[-8:]],
            }
            self.kernel_proposer.hardware_feedback = json.dumps(feedback)
            want = min(kernel_batch, spec.budget.max_evaluations-len(history))
            seen = {m.label for m in history}
            injected = [KernelCandidate(label, "critic", (entry["critique"]["summary"],))
                        for label, entry in pending_kernel.items()
                        if label not in seen and entry["outcome"]["state"] == "pending"][:want]
            for c in injected:
                pending_kernel[c.label]["outcome"].update(state="proposed", after=c.label)
            requested = want - len(injected)
            proposed = tuple(injected) + tuple(self.kernel_proposer.propose(
                spec, kernel_space, tuple(history), requested) if requested else ())
            candidates = []
            for c in proposed:
                if kernel_space.contains(c.label) and c.label not in seen:
                    candidates.append(c)
                    seen.add(c.label)
                if len(candidates) == want:
                    break
            if not candidates:
                break
            measured, dense = self.adapter.measure(spec, tuple(candidates))
            if [m.label for m in measured] != [c.label for c in candidates]:
                raise ValueError("DynaX measurement identities do not match proposals")
            if baseline is None:
                baseline = dense
            for m in measured:
                history.append(m)
                event = {"label": m.label, "quality_passed": bool(m.within and math.isfinite(m.quality_loss) and m.quality_loss <= spec.epsilon),
                         "kernel_proposed_by": m.proposed_by, "hardware_evaluated": 0,
                         "feedback_before_proposal_sha256": digest_json(feedback)}
                search_history = ()
                # A failed measurement remains failed; conversion alone is not a quality gate.
                kernel = kernel_result_from_measurement(None, replace(m, quality_loss=m.quality_loss or 0.0))
                kernel = replace(kernel, status=Status.PASSED if event["quality_passed"] else Status.FAILED)
                if event["quality_passed"]:
                    contract = parse_algorithm(m.label)
                    proposer = self.hardware_proposer_factory(len(history)-1)
                    guided = CriticGuidedProposer(proposer, self.critic, spec, critic_events)
                    search = CoOptimizer(allow_unverified=True).run(
                        kernel, sequence_length=spec.sequence_length,
                        head_dim=head_dim, specs=specs, space=hardware_space,
                        block_m=contract.block_m, kept_per_block=contract.sizing_kept,
                        proposer=guided if self.critic else proposer, budget=hardware_budget, batch=hardware_batch,
                        timeout_seconds=max(0, spec.budget.max_wall_seconds-(time.monotonic()-started)), patience=None)
                    guided.observe(search.history)
                    search_history = search.history
                    for evaluated in search.history:
                        identity = {"task": spec.digest, "label": m.label,
                                    "head_dim": head_dim, "point": asdict(evaluated.point)}
                        intervention = next((r for r in critic_events
                            if r['context']['kernel']['sparse_method'] == m.label
                            and r['outcome'].get('after') == identity['point']), None)
                        design_id = digest_json(identity)
                        if intervention:
                            intervention['outcome']['design_id'] = design_id
                        designs.append({
                            "design_id": design_id, "label": m.label,
                            "critic_review_id": intervention['review_id'] if intervention else None,
                            "algorithm": asdict(contract), "point": asdict(evaluated.point),
                            "quality_loss": m.quality_loss, "metrics": evaluated.metrics,
                            "feasible": evaluated.feasible, "violations": evaluated.violations,
                            "hardware": to_primitive(evaluated.hardware),
                            "schedule": to_primitive(evaluated.schedule),
                        })
                    event.update(hardware_evaluated=search.evaluated,
                                 hardware_feasible=search.feasible,
                                 hardware_stopped=search.stopped_because,
                                 llm_successful_batches=getattr(proposer, "llm_batches", None),
                                 fallback_batches=getattr(proposer, "fallback_batches", 0),
                                 fallback_proposer=type(getattr(proposer, "fallback", None)).__name__,
                                 hardware_calls=getattr(proposer, "calls", []),
                                 hardware_rejections=getattr(proposer, "rejected", []),
                                 constraint_failures=sorted({v for d in search.history for v in d.violations}))
                if m.label in pending_kernel:
                    pending_kernel.pop(m.label)["outcome"].update(
                        state="evaluated", quality_passed=event["quality_passed"],
                        quality_loss=m.quality_loss, hardware_evaluated=event["hardware_evaluated"],
                        independent_improvement=None)
                context = search_context(spec, kernel, specs, hardware_space, search_history,
                    phase="kernel", allowed_labels=[l for l in kernel_space.labels()
                        if l not in {x.label for x in history} and l not in {c.label for c in candidates}],
                    remaining=spec.budget.max_evaluations-len(history))
                context["measurement_success"] = m.within and math.isfinite(m.quality_loss)
                analysis = review_search(self.critic, context, critic_events)
                if analysis and analysis["critique"]["mutations"]:
                    label = analysis["critique"]["mutations"][0]["value"]
                    if label in pending_kernel:
                        analysis["outcome"]["state"] = "already_pending"
                    else:
                        pending_kernel[label] = analysis
                events.append(event)
            result.update(measurements=to_primitive(history), frontier=joint_front(designs),
                          baseline_metric=baseline, wall_seconds=time.monotonic()-started,
                          kernel_rejections=getattr(self.kernel_proposer, "rejected", []))
            result["kernel_calls"] = getattr(self.kernel_proposer, "calls", [])
            result["critic_calls"] = getattr(self.critic, "search_calls", [])
            result["representative"] = result["frontier"][0] if result["frontier"] else None
            if checkpoint:
                checkpoint(result)
        result["kernel_budget_complete"] = len(history) == spec.budget.max_evaluations
        for analysis in pending_kernel.values():
            analysis["outcome"]["state"] = "not_executed_budget_or_search_end"
        if checkpoint:
            checkpoint(result)
        return result
