"""Run the co-design loop and confirm its winner by actually simulating the RTL.

This is the end-to-end version of what tests/test_verilator_adapter.py checks in
isolation. The co-optimizer picks a design with the analytical model; the winner
is then handed to the Verilator backend, which elaborates the Chisel, verilates
it and runs the golden testbench. The two evaluations are printed side by side
because their difference is the point:

  * the analytical result cannot disagree -- it scores the winner with the same
    cost model that chose it, so its functional_passed is a constant False
  * the Verilator result can, and its functional_passed is a measurement

Run it inside a Slurm allocation (slurm/loop/fast_l2_closed_loop.slurm): it shells
out to slurm/rtl/fast_rtl_verify.slurm, which needs the JVM, scala-cli and the
Verilator container that the login node cannot provide.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from fast.adapters.analytical import AnalyticalEvaluationAdapter
from fast.adapters.verilator import VerilatorEvaluationAdapter
from fast.agents.codesign import to_hardware
from fast.agents.cooptimizer import CoOptimizer
from fast.agents.templates import TemplateRegistry
from fast.schemas.models import (
    EvaluationResult,
    ExperimentSpec,
    KernelProfile,
    KernelResult,
    Status,
)


def _kernel_from(path: Path | None) -> KernelResult:
    """The measured kernel result, or a stand-in that says it is one.

    A real run passes --kernel pointing at a run_eval_matrix.py output. Without
    one the loop still exercises every stage, but the numbers are a fixture and
    the report says so rather than passing them off as measurements.
    """
    if path is None:
        # The numbers below are the ones the X:M sweep actually produced for
        # llama at 512 (block occupancy 0.42 against 0.90 sparsity is the
        # separation X:M shows and N:M does not), but this is still a fixture:
        # it is typed in rather than read from a run, so the evidence says so.
        return KernelResult(
            status=Status.PASSED,
            baseline_metric=10.0,
            candidate_metric=10.012,
            metric_name="perplexity",
            quality_loss=0.012,
            actual_sparsity=0.90,
            index_entropy=0.5,
            block_occupancy=0.42,
            trace_uri="memory://l2-closed-loop/kernel",
            profile=KernelProfile(
                histogram_bins=32,
                row_density_histogram=tuple([0] * 32),
                block_density_histogram=tuple([0] * 32),
                load_imbalance=1.35,
                column_top1_mass=0.11,
                column_top5_mass=0.34,
                column_top10_mass=0.52,
            ),
            evidence=("FIXTURE: not a measurement; pass --kernel for real numbers",),
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    profile = payload.get("profile")
    return KernelResult(
        status=Status.PASSED,
        baseline_metric=float(payload["baseline_metric"]),
        candidate_metric=float(payload["candidate_metric"]),
        metric_name=payload.get("metric_name", "perplexity"),
        quality_loss=float(payload["quality_loss"]),
        actual_sparsity=float(payload["actual_sparsity"]),
        index_entropy=float(payload.get("index_entropy", 0.0)),
        block_occupancy=float(payload.get("block_occupancy", 0.0)),
        trace_uri=payload.get("trace_uri", str(path)),
        profile=KernelProfile(**profile) if profile else None,
        evidence=tuple(payload.get("evidence", ())),
    )


def _show(title: str, result: EvaluationResult) -> None:
    print(f"\n--- {title} ---")
    print(f"  status           {result.status.value}")
    print(f"  fidelity         {result.fidelity}")
    print(f"  functional_passed{result.functional_passed!s:>6}")
    print(f"  cycles           {result.cycles}")
    print(f"  pe_utilization   {result.pe_utilization}")
    print(f"  wall_seconds     {result.wall_seconds:.1f}")
    if result.error:
        print(f"  error            {result.error}")
    for item in result.evidence:
        print(f"    * {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--kernel", type=Path, default=None,
                        help="a run_eval_matrix.py result; omit to use a fixture")
    parser.add_argument("--template", default="topk",
                        help="template to compose and simulate")
    parser.add_argument("--sequence-length", type=int, default=512)
    parser.add_argument("--budget", type=int, default=24)
    args = parser.parse_args()

    kernel = _kernel_from(args.kernel)
    registry = TemplateRegistry()
    template = registry.by_id(args.template)
    if template is None:
        print(f"no such template: {args.template}", file=sys.stderr)
        return 2

    print("=== 1. co-optimise (L1 analytical) ===")
    report = CoOptimizer(registry, template_id=args.template).run(
        kernel, sequence_length=args.sequence_length, budget=args.budget
    )
    print(f"evaluated={report.evaluated} feasible={report.feasible} "
          f"rounds={report.rounds} stopped_because={report.stopped_because!r}")
    if report.best is None:
        for item in report.rejected_examples:
            print(f"  rejected: {item}")
        return 1

    point = report.best.point
    print(f"winner: rows={point.num_rows} pe/row={point.pe_per_row} "
          f"reg_width={point.reg_width} tile=({point.tile_q},{point.tile_k},{point.tile_d})")

    candidate = to_hardware(
        point, template,
        block_m=report.best.hardware.topk_m,
        kept_per_block=report.best.hardware.topk_n,
    )

    print("\n=== 2. score it with the model that chose it ===")
    analytical = AnalyticalEvaluationAdapter(kernel=kernel).evaluate(
        _spec(args.sequence_length), candidate
    )
    _show("analytical (cannot disagree)", analytical)

    print("\n=== 3. confirm it by simulating the RTL ===")
    verilator = VerilatorEvaluationAdapter(repo_root=args.repo_root)
    measured = verilator.evaluate(
        _spec(args.sequence_length), candidate,
        template=template, analytical=analytical,
    )
    _show("verilator (can disagree)", measured)

    print("\n=== verdict ===")
    print(f"the co-optimizer's winner {'IS' if measured.functional_passed else 'IS NOT'} "
          f"backed by a passing RTL simulation")
    return 0 if measured.status is Status.PASSED else 1


def _spec(sequence_length: int) -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="l2-closed-loop", candidate_id="best",
        model="llama", dataset="wikitext",
        sequence_length=sequence_length,
        sparsity_x=8, sparsity_m=64, epsilon=0.02, seed=20260905,
    )


if __name__ == "__main__":
    raise SystemExit(main())
