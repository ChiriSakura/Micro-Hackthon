"""Equal-budget Pareto search on frozen real Kernel measurements.

This is a MODEL benchmark, not independent hardware performance evidence.
Every method receives the same measured workload and legal design space. Failed
and infeasible proposals remain in the trace. Optional LLM variants differ only
in whether numerical feedback is shown; neither may change feasibility gates.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fast.agents.codesign import DEFAULT_OBJECTIVE, POWER_COVERAGE, CoDesignSpace
from fast.agents.cooptimizer import (
    CoOptimizer, GuidedProposer, RandomProposer, ParetoFeedbackProposer,
)
from fast.agents.pareto import frontier_vectors, hypervolume_2d
from fast.schemas.conversions import kernel_result_from_measurement, algorithm_parameters
from fast.schemas.models import ArchSpecs, digest_json, kernel_search_report_from_dict


class CommonStart:
    """Same first batch and same exclusion history for every strategy."""
    def __init__(self, delegate):
        self.delegate = delegate
        self.name = getattr(delegate, "name", type(delegate).__name__)

    def propose(self, kernel, specs, space, history, count):
        if not history:
            return GuidedProposer().propose(kernel, specs, space, history, count)
        return self.delegate.propose(kernel, specs, space, history, count)


class NoFeedback:
    """Hide scores, feasibility and diagnoses; keep IDs to prevent repeats."""
    def __init__(self, delegate):
        self.delegate = delegate
        self.name = "llm-no-numerical-feedback"

    def propose(self, kernel, specs, space, history, count):
        from dataclasses import replace
        hidden = tuple(replace(item, metrics={}, feasible=False, violations=(), rationale=())
                       for item in history)
        return self.delegate.propose(kernel, specs, space, hidden, count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--head-dim", type=int, required=True)
    parser.add_argument("--budget", type=int, default=32)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--labels", nargs="+", help="Exact accepted labels; default all")
    parser.add_argument("--methods", nargs="+", default=["random", "guided", "feedback-rules"],
                        choices=["random", "guided", "feedback-rules", "llm", "llm-no-feedback"])
    parser.add_argument("--max-area-um2", type=float, default=4e6)
    parser.add_argument("--target-mhz", type=float, default=350)
    parser.add_argument("--max-power-mw", type=float)
    parser.add_argument("--reference-latency-s", type=float)
    parser.add_argument("--reference-energy-j", type=float)
    parser.add_argument("--gcp-project")
    parser.add_argument("--gcp-location", default="us-central1")
    parser.add_argument("--llm-model", default="gemini-2.5-pro")
    parser.add_argument("--llm-timeout", type=int, default=90)
    args = parser.parse_args()
    if args.budget < args.batch * 2:
        parser.error("budget must allow at least one feedback batch after the common start")
    if (args.reference_latency_s is None) != (args.reference_energy_j is None):
        parser.error("both fixed hypervolume reference coordinates are required")
    reference = ((args.reference_latency_s, args.reference_energy_j)
                 if args.reference_latency_s is not None else None)
    raw = args.search.read_bytes()
    report = kernel_search_report_from_dict(json.loads(raw))
    accepted = [m for m in report.measurements if m.within and m.quality_loss <= report.spec.epsilon]
    if args.labels:
        accepted = [m for m in accepted if m.label in args.labels]
        if set(args.labels) != {m.label for m in accepted}:
            parser.error("every requested label must have a passing quality measurement")
    if not accepted:
        parser.error("no measured candidate passes the quality constraint")
    specs = ArchSpecs(max_area_um2=args.max_area_um2, target_mhz=args.target_mhz,
                      max_power_mw=args.max_power_mw)
    space = CoDesignSpace()
    root = Path(__file__).resolve().parents[1]
    sources = [*sorted((root / "fast").rglob("*.py")), Path(__file__).resolve()]
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sources}
    output = {
        "objective": asdict(DEFAULT_OBJECTIVE), "constraints": asdict(specs),
        "accuracy_epsilon": report.spec.epsilon, "power_coverage": POWER_COVERAGE,
        "fidelity": "L1-analytical-shared-model", "independent_validation": False,
        "scope": "one attention head at fixed sequence length and head_dim; partial energy",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source": str(args.search.resolve()), "head_dim": args.head_dim,
        "space": asdict(space), "seeds": args.seeds, "budget": args.budget,
        "code_sha256": source_hashes,
        "seed_scope": "Python stochastic proposers only; LLM sampling is unseeded",
        "llm_configuration": {"model": args.llm_model, "temperature": 0.2,
                              "timeout_seconds": args.llm_timeout,
                              "location": args.gcp_location},
        "budget_unit": "unique design evaluations per kernel configuration",
        "llm_cost_note": "LLM wall time/rejections included; API monetary cost not instrumented",
        "reference": reference, "runs": [],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for measurement in accepted:
        kernel = kernel_result_from_measurement(report, measurement)
        params = algorithm_parameters(kernel)
        if not params.get("block_m") or not params.get("kept_per_block"):
            parser.error(f"{measurement.label}: hardware sizing contract incomplete")
        for seed in args.seeds:
            for method in args.methods:
                llm_proposer = None
                if method == "random":
                    proposer = RandomProposer(seed)
                elif method == "guided":
                    proposer = GuidedProposer()
                elif method == "feedback-rules":
                    proposer = ParetoFeedbackProposer(seed)
                else:
                    if not args.gcp_project:
                        parser.error("LLM methods require --gcp-project")
                    from fast.agents.llm_backends import VertexDirect
                    from fast.agents.plan_proposers import LLMPlanProposer
                    llm = VertexDirect(model=args.llm_model, project=args.gcp_project,
                                       location=args.gcp_location,
                                       system_message="Propose legal designs from evidence.",
                                       temperature=0.2, timeout_seconds=args.llm_timeout)
                    llm_proposer = LLMPlanProposer(llm, model_name=args.llm_model)
                    proposer = NoFeedback(llm_proposer) if method.endswith("no-feedback") else llm_proposer
                search = CoOptimizer(allow_unverified=True).run(
                    kernel, sequence_length=report.spec.sequence_length, head_dim=args.head_dim,
                    specs=specs, space=space, budget=args.budget, batch=args.batch,
                    patience=None, proposer=CommonStart(proposer), **params)
                trace, vectors = [], []
                for i, result in enumerate(search.history, 1):
                    identity = {"source_sha256": output["source_sha256"], "label": measurement.label,
                                "head_dim": args.head_dim, "point": asdict(result.point)}
                    if result.feasible:
                        vectors.append(DEFAULT_OBJECTIVE.vector(result.metrics))
                    front = frontier_vectors(vectors)
                    trace.append({"evaluation": i, "design_id": digest_json(identity),
                                  "point": asdict(result.point), "metrics": result.metrics,
                                  "feasible": result.feasible, "violations": result.violations,
                                  "frontier": front,
                                  "hypervolume": hypervolume_2d(front, reference) if reference else None})
                run = {"label": measurement.label, "method": method, "seed": seed,
                       "evaluated": search.evaluated, "feasible": search.feasible,
                       "wall_seconds": search.wall_seconds, "stopped": search.stopped_because,
                       "budget_complete": search.evaluated == args.budget,
                       "trace": trace,
                       "llm_rejections": getattr(llm_proposer, "rejected", []),
                       "llm_successful_batches": getattr(llm_proposer, "llm_batches", None),
                       "fallback_batches": getattr(llm_proposer, "fallback_batches", 0)}
                output["runs"].append(run)
                args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
                print(f"{measurement.label} {method} seed={seed}: "
                      f"{search.evaluated} evaluated, {len(search.frontier)} Pareto points", flush=True)
    lines = ["**Equal-budget energy/latency search pilot**", "",
             "These are L1 shared-model predictions with partial energy coverage. "
             "They do not prove independent acceleration or an LLM advantage.", "",
             "| Workload | Method | Seeds | Mean feasible | Mean Pareto size |", "|---|---|---|---|---|"]
    for label in sorted({r["label"] for r in output["runs"]}):
        for method in args.methods:
            group = [r for r in output["runs"] if r["label"] == label and r["method"] == method]
            sizes = [len(r["trace"][-1]["frontier"]) if r["trace"] else 0 for r in group]
            lines.append(f"| {label} | {method} | {len(group)} | "
                         f"{statistics.mean(r['feasible'] for r in group):.1f} | {statistics.mean(sizes):.1f} |")
    lines += ["", "Front size is descriptive, not a quality score. Compare fixed-reference "
              "hypervolume or the actual coordinates, then independently validate candidates."]
    args.out.with_suffix(".md").write_text("\n".join(lines)+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
