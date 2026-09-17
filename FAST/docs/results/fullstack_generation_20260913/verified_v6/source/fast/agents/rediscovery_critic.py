"""Executable Critic interventions for joint search and independent repair.

Reuse Critique/Mutation and the existing rule/LLM Critic agents. A decision can
spend an existing proposal slot, never alter a gate, budget or measured metric.
L1 frontier contributions and independent validation outcomes remain separate.
"""
from dataclasses import asdict
import json

from fast.agents.codesign import DEFAULT_OBJECTIVE
from fast.agents.cooptimizer import CoDesignResult
from fast.agents.pareto import extends_frontier
from fast.schemas.contract import parse_algorithm
from fast.schemas.models import Critique, Decision, Layer, Mutation, Status, digest_json, to_primitive


SEARCH_PROMPT = """You are the Critic in DynaX joint algorithm/hardware search.
Analyse the supplied evidence and propose at most ONE executable intervention.
Minimise (seconds, energy_j) for the SAME completed task as a Pareto set, subject
to the unchanged quality, area, power and frequency constraints. Do not optimise
quality loss inside the allowed budget. L1 energy has partial, outdated power
calibration; never call it measured whole-system energy. Independent scheduler
cycles/area must NOT be compared to full-attention model cycles/area as if they
covered the same workload. Missing validation is not a failed RTL simulation.

Use only supplied observations and domains, not remembered calibration tables.
For phase=hardware/repair, keep the algorithm fixed and change ONE field of
parent_point via layer=compiler, operation=set. For phase=kernel, use
layer=kernel, field=candidate, operation=set, value=one allowed_kernel_labels
entry. No RTL rewrite or model recalibration is executable in this entry point.
For phase=validation, review the independent observations with mutations=[];
any subsequent executable action is owned by the separately budgeted repair phase.
Unsupported actions and invented evidence paths will be rejected. Stop means
no intervention for this phase; fixed-budget exploration may still continue.
When no justified executable action exists, return mutations=[].
Any full point already in history is excluded, including infeasible points.
queue_depth is the number of buffered entries, not an arithmetic pipeline depth;
divider_stages controls the divider pipeline. Do not assume deeper queues improve
timing: use the supplied observed comparisons and keep changes falsifiable.

Return one JSON object. attribution MUST be exactly ONE of: kernel, compiler,
uarch, evaluator, infrastructure, planner_model. It is an enum, NOT an explanation;
put your explanation in summary. decision is continue, revert, or stop.
evidence is a nonempty list of real paths into the context: use numeric dot
indices, e.g. history.0.metrics.max_frequency_mhz or validation.0.frequency_feasible.
frequency_feasible is on the validation ROW, not inside its metrics object.
Other top-level fields are summary and mutations. Each mutation
has layer, field, operation, value, expected_effect (a testable hypothesis), risk.
Do not claim a hypothesis succeeded before evaluating it.

CONTEXT:
"""


def search_context(spec, kernel, specs, space, history=(), *, phase="hardware",
                   allowed_labels=(), validation=(), parent_point=None, remaining=0):
    feasible = [r for r in history if r.feasible]
    parent = (min(feasible, key=lambda r: DEFAULT_OBJECTIVE.score(r.metrics)) if feasible
              else min(history, key=lambda r: len(r.violations)) if history else None)
    return dict(
        phase=phase, kernel=to_primitive(kernel), epsilon=spec.epsilon,
        quality_passed=kernel.status is Status.PASSED and kernel.quality_loss <= spec.epsilon,
        constraints=to_primitive(specs), domains={**asdict(space), "data_width": specs.data_widths},
        parent_point=parent_point or (asdict(parent.point) if parent else None),
        history=[dict(point=asdict(r.point), metrics=r.metrics, feasible=r.feasible,
                      violations=list(r.violations)) for r in history],
        allowed_kernel_labels=list(allowed_labels), validation=list(validation),
        remaining_proposals=remaining,
        scope="L1-analytical-shared-model; partial energy with legacy power calibration",
    )


def rule_review(context):
    """Conservative, evidence-bound hypotheses; no hidden model evaluations."""
    def reply(layer, summary, evidence, mutation=None):
        return Critique(Status.PASSED, layer, Decision.CONTINUE, summary,
                        tuple(evidence), (mutation,) if mutation else ())

    if context.get("measurement_success") is False:
        return reply(Layer.INFRASTRUCTURE, "Kernel measurement failed; no quality conclusion is available",
                     ("measurement_success", "kernel"))
    if context["phase"] == "validation":
        failed = any(v.get("frequency_feasible") is False for v in context["validation"])
        return reply(Layer.COMPILER if failed else Layer.EVALUATOR,
                     "Independent scheduler evidence reviewed; repairs use their own explicit budget",
                     ("validation",))
    if not context["quality_passed"]:
        current = parse_algorithm(context["kernel"]["sparse_method"])
        for label in context["allowed_kernel_labels"]:
            other = parse_algorithm(label)
            # Increase retention without also changing block shape or thresholds.
            if (other.block_m == current.block_m and
                (other.threshold_0, other.threshold_1) == (current.threshold_0, current.threshold_1)
                and other.kept_high >= current.kept_high and other.kept_low >= current.kept_low
                and (other.kept_high, other.kept_low) != (current.kept_high, current.kept_low)):
                return reply(Layer.KERNEL, "Quality gate failed; test a higher-retention configuration",
                    ("kernel.quality_loss", "epsilon"), Mutation(
                        Layer.KERNEL, "candidate", "set", label,
                        "measure whether increased retention brings quality_loss within epsilon",
                        "more work may increase latency and energy"))
        return reply(Layer.KERNEL, "Quality gate failed; no comparable retention intervention remains",
                     ("kernel.quality_loss", "allowed_kernel_labels"))
    if context["phase"] == "kernel":
        return reply(Layer.KERNEL, "Continue algorithm exploration using the observed hardware outcomes",
                     ("history", "allowed_kernel_labels"))
    parent = context["parent_point"]
    if parent is None:
        return reply(Layer.EVALUATOR, "No evaluated hardware to diagnose yet", ("history",))
    validation = context["validation"]
    failed_timing = any(v.get("function_passed") is True and
                        v.get("frequency_feasible") is False for v in validation)
    failed_function = any(v.get("function_passed") is False for v in validation)
    if failed_function and not failed_timing:
        return reply(Layer.UARCH, "Functional failure requires RTL debugging; parameter search cannot certify a fix",
                     ("validation",))
    problems = " ".join(v for h in context["history"] if h["point"] == parent
                        for v in h["violations"]).lower()
    if failed_timing:
        dimensions = (("queue_depth", -1), ("num_rows", -1), ("pe_per_row", -1))
        reason, evidence = "Independent scheduler timing failed; test reduced scheduling fanout", ("validation",)
    elif "clock" in problems or "mhz" in problems:
        dimensions = (("divider_stages", 1), ("queue_depth", -1))
        reason, evidence = "Model frequency constraint failed; test a different pipeline/queue configuration", ("history",)
    elif "area" in problems or "power" in problems or "max_pe" in problems:
        dimensions = (("num_rows", -1), ("pe_per_row", -1), ("sram_bytes", -1))
        reason, evidence = "Resource constraint failed; test a smaller configuration", ("history",)
    else:
        dimensions = (("queue_depth", 1), ("bank_count", 1), ("num_rows", -1))
        reason, evidence = "Test a scheduling/memory trade-off on the model Pareto frontier", ("history",)
    seen = [h["point"] for h in context["history"]]
    for field, direction in dimensions:
        values = sorted(context["domains"][field], reverse=direction < 0)
        for value in values:
            point = {**parent, field: value}
            if (value - parent[field]) * direction > 0 and point not in seen:
                return reply(Layer.COMPILER, reason, evidence, Mutation(
                    Layer.COMPILER, field, "set", value,
                    "test constraint recovery and latency/energy trade-off; independent evidence is required for acceptance",
                    "may worsen another objective or remain infeasible"))
    return reply(Layer.COMPILER, "No untried one-field intervention remains; continue proposer exploration",
                 ("history", "domains"))


def _resolve(context, path):
    value = context
    for part in path.split("."):
        value = value[int(part)] if isinstance(value, (list, tuple)) else value[part]
    return value


def validate_review(critique, context):
    if critique.status is not Status.PASSED or not critique.evidence:
        raise ValueError("Critic must return a successful, evidence-bound analysis")
    for path in critique.evidence:
        try:
            _resolve(context, path)
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(f"unknown evidence path: {path}") from None
    if len(critique.mutations) > 1:
        raise ValueError("one intervention per review is required for attribution")
    if not critique.mutations:
        return
    if context["phase"] == "validation":
        raise ValueError("validation review cannot spend the separate repair budget")
    m = critique.mutations[0]
    if critique.decision is Decision.STOP:
        raise ValueError("stop cannot also dispatch an intervention")
    # Attribution names the diagnosed cause; mutation.layer names the executor.
    # A hardware timing problem can legitimately require a compiler parameter
    # change. The existing FiveAgentFlow Critic also emits cross-layer actions.
    if m.operation != "set" or not m.expected_effect:
        raise ValueError("only explicit set actions with a testable hypothesis are executable")
    if context["phase"] == "kernel":
        if m.layer is not Layer.KERNEL or m.field != "candidate" or m.value not in context["allowed_kernel_labels"]:
            raise ValueError("kernel action must name an unmeasured legal candidate")
    else:
        if m.layer is not Layer.COMPILER or m.field not in context["domains"]:
            raise ValueError("only legal hardware fields can change during hardware/repair search")
        if not any(type(m.value) is type(v) and m.value == v for v in context["domains"][m.field]):
            raise ValueError("hardware value is outside the declared domain")
        if not context["quality_passed"] or context["parent_point"] is None:
            raise ValueError("hardware intervention requires passing quality and a parent")
        child = {**context["parent_point"], m.field: m.value}
        if child == context["parent_point"] or any(child == h["point"] for h in context["history"]):
            raise ValueError("intervention repeats an evaluated configuration")


def review_search(critic, context, events):
    """Record exactly which context, analysis, fallback and action were used."""
    if critic is None:
        return None
    error = None
    try:
        critique = critic.review_search(context)
        validate_review(critique, context)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        critique = rule_review(context)
        validate_review(critique, context)
    event = dict(
        review_id=digest_json({"index": len(events), "context": context}),
        critic=getattr(critic, "name", type(critic).__name__),
        context=context, context_sha256=digest_json(context),
        critique=to_primitive(critique), fallback_reason=error,
        outcome={"state": "pending" if critique.mutations else "no_action"},
    )
    events.append(event)
    calls = getattr(critic, "search_calls", ())
    if calls and calls[-1]["context_sha256"] == event["context_sha256"]:
        event["llm_call"] = calls[-1]
        event["fallback_reason"] = error or calls[-1].get("fallback_reason")
    return event


def build_search_critic(mode, *, llm=None, model_name="llm", specs=None):
    if mode == "off":
        return None
    if mode == "rule":
        from fast.agents.critic import CriticAgent
        return CriticAgent()
    if mode == "llm" and llm is not None:
        from fast.agents.llm_critic import LLMCriticAgent
        return LLMCriticAgent(llm, model_name=model_name, specs=specs)
    raise ValueError("LLM Critic requires an LLM backend; choose rule or off otherwise")


def read_validation_evidence(path, design_id, target_mhz):
    """Bind independent observations to their design and acceptance gates."""
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return False, [dict(design_id=design_id, scope="validation unavailable",
                            error=f"{type(exc).__name__}: {exc}")]
    identity_ok = data.get("design_id") == design_id
    complete = data.get("complete_captured_task") is True
    unchanged = data.get("sources_unchanged") is True
    frequency_matches = data.get("fixed_frequency_mhz") == target_mhz
    rows = [dict(design_id=data.get("design_id"), scope=data.get("scope"),
                 function_passed=r.get("passed"), frequency_feasible=r.get("frequency_feasible"),
                 metrics=r.get("metrics", {}), latency_s=r.get("latency_s"),
                 identity_ok=identity_ok, complete_captured_task=complete,
                 sources_unchanged=unchanged, frequency_matches=frequency_matches,
                 source=data.get("source"), log_uri=str(path)) for r in data.get("results", [])]
    if not identity_ok:
        return False, [dict(design_id=design_id, scope="validation identity mismatch", log_uri=str(path))]
    accepted = bool(rows and complete and unchanged and frequency_matches and all(
        r["function_passed"] is True and r["frequency_feasible"] is True
        and isinstance(r["metrics"].get("slack_ns"), (int, float))
        and r["metrics"]["slack_ns"] >= 0 for r in rows))
    return accepted, rows or [dict(design_id=design_id, scope="validation has no results", log_uri=str(path))]


class CriticGuidedProposer:
    """Reserve one existing proposal slot for a validated Critic intervention."""
    def __init__(self, delegate, critic, spec, events, *, validation=(), parent_point=None,
                 context_filter=None, apply_interventions=True):
        self.delegate, self.critic, self.spec, self.events = delegate, critic, spec, events
        self.validation, self.parent_point = validation, parent_point
        self.pending = None
        self.context_filter = context_filter
        self.apply_interventions = apply_interventions

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def observe(self, history):
        if self.pending is None:
            return
        event, child, old_vectors = self.pending
        observed = next((h for h in history if asdict(h.point) == child), None)
        if observed is None:
            return
        event["outcome"].update(
            state="evaluated", feasible=observed.feasible, metrics=observed.metrics,
            violations=list(observed.violations),
            model_frontier_extended=bool(observed.feasible and extends_frontier(
                old_vectors, DEFAULT_OBJECTIVE.vector(observed.metrics))),
            independent_improvement=None,
        )
        self.pending = None

    def propose(self, kernel, specs, space, history, count):
        self.observe(history)
        if count <= 0:
            return ()
        selected, event = [], None
        if self.critic is not None and (history or self.validation):
            context = search_context(self.spec, kernel, specs, space, history,
                phase="repair" if self.validation else "hardware", validation=self.validation,
                parent_point=self.parent_point, remaining=count)
            if self.context_filter is not None:
                context = self.context_filter(context)
            event = review_search(self.critic, context, self.events)
            mutations = event["critique"]["mutations"]
            if mutations and not self.apply_interventions:
                event['outcome']['state'] = 'shadow_not_applied'
            if mutations and self.apply_interventions:
                from fast.agents.codesign import CoDesignPoint
                m = mutations[0]
                child = {**context["parent_point"], m["field"]: m["value"]}
                selected = [CoDesignPoint(**child)]
                event["outcome"] = dict(state="proposed", before=context["parent_point"], after=child)
                self.pending = (event, child, [DEFAULT_OBJECTIVE.vector(h.metrics) for h in history if h.feasible])
        # The delegate sees the intervention in its exclusion history. Feedback is
        # also available to LLM delegates, but application never relies on prose.
        shadow = tuple(history) + tuple(CoDesignResult(p, None, None, {}, False) for p in selected)
        self.delegate.critic_feedback = json.dumps(event) if event and self.apply_interventions else ""
        proposed = self.delegate.propose(kernel, specs, space, shadow, count-len(selected)) if len(selected) < count else ()
        seen = [asdict(h.point) for h in shadow]
        domains = {**asdict(space), "data_width": specs.data_widths}
        for p in proposed:
            data = asdict(p)
            if data in seen or not all(any(type(data[k]) is type(v) and data[k] == v for v in values)
                                       for k, values in domains.items()):
                continue
            selected.append(p)
            seen.append(data)
            if len(selected) == count:
                break
        return tuple(selected)
