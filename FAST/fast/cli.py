"""Local entry point for one FAST candidate.

``--kernel deterministic`` exercises the control flow with no measurement cost.
``--kernel dynax`` runs the real DynaX dense-versus-sparse comparison, so its
numbers are experimental evidence rather than an orchestration smoke test.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from fast.adapters import DeterministicEvaluationAdapter, DeterministicKernelAdapter, DynaXKernelAdapter
from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, TemplateRecord, UArchAgent
from fast.orchestrator import FiveAgentFlow
from fast.schemas.models import Budget, ExperimentSpec, Status, to_primitive
from fast.storage import ExperimentStore, RunManifest, now


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC = {
    "experiment_id": "fast-smoke",
    "candidate_id": "x8-m64",
    "model": "hf-internal-testing/tiny-random-LlamaForCausalLM",
    "dataset": "wikitext-2-raw-v1",
    "sequence_length": 64,
    "sparsity_x": 8,
    "sparsity_m": 64,
    "epsilon": 0.01,
    "seed": 20260903,
}


def load_spec(path: Path | None) -> ExperimentSpec:
    data = dict(DEFAULT_SPEC)
    if path is not None:
        data.update(json.loads(path.read_text(encoding="utf-8")))
    data.pop("schema_version", None)
    budget = Budget(**data.pop("budget", {}))
    return ExperimentSpec(budget=budget, **data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=None, help="experiment spec JSON")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/smoke"))
    parser.add_argument("--kernel", choices=["deterministic", "dynax"], default="deterministic")
    parser.add_argument("--template-id", default="smoke-template")
    parser.add_argument("--template-verified", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dynax-root", type=Path, default=REPO_ROOT / "DynaX")
    parser.add_argument("--dynax-python", default=sys.executable)
    parser.add_argument("--dynax-device", default="auto")
    parser.add_argument("--dynax-launcher", default="", help="optional prefix, e.g. 'srun --gres=gpu:1'")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir: Path = args.run_dir.expanduser()
    run_dir.mkdir(parents=True, exist_ok=True)
    spec = load_spec(args.config)

    if args.kernel == "dynax":
        kernel_adapter = DynaXKernelAdapter(
            dynax_root=args.dynax_root,
            run_root=run_dir / "candidates",
            python_executable=args.dynax_python,
            launcher=tuple(args.dynax_launcher.split()) if args.dynax_launcher else (),
            device=args.dynax_device,
        )
    else:
        kernel_adapter = DeterministicKernelAdapter()

    template = TemplateRecord(
        args.template_id, f"sha256:{args.template_id}", f"memory://{args.template_id}", args.template_verified
    )
    flow = FiveAgentFlow(
        KernelAgent(kernel_adapter),
        CompilerAgent(),
        UArchAgent((template,)),
        EvaluatorAgent(DeterministicEvaluationAdapter()),
        CriticAgent(),
        store=ExperimentStore(run_dir / "fast.db"),
    )

    started_at = now()
    report = flow.run(spec, template_id=template.template_id)
    failed = next(
        (
            name
            for name, stage in (
                ("kernel", report.kernel),
                ("compiler", report.compiler),
                ("uarch", report.hardware),
                ("evaluator", report.evaluation),
            )
            if stage is not None and stage.status is Status.FAILED
        ),
        None,
    )
    exit_code = 0 if failed is None else 1

    manifest_path = RunManifest(
        root=run_dir / "candidates",
        repositories={"fast": REPO_ROOT / "FAST", "dynax": REPO_ROOT / "DynaX", "chia": REPO_ROOT / "chia"},
    ).write(
        report,
        started_at=started_at,
        finished_at=now(),
        exit_code=exit_code,
        failed_stage=failed,
        cloud_cost_usd=report.evaluation.cloud_cost_usd if report.evaluation else 0.0,
        extra={"kernel_backend": args.kernel},
    )

    output = run_dir / "report.json"
    output.write_text(json.dumps(to_primitive(report), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "report": str(output.resolve()),
            "manifest": str(manifest_path.resolve()),
            "kernel_status": report.kernel.status.value,
            "quality_loss": report.kernel.quality_loss,
            "actual_sparsity": report.kernel.actual_sparsity,
            "attribution": report.critique.attribution.value,
            "decision": report.critique.decision.value,
            "cache_hits": list(report.cache_hits),
            "failed_stage": failed,
        },
        indent=2,
    ))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
