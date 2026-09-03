from __future__ import annotations

import argparse
import json
from pathlib import Path

from fast.adapters import DeterministicEvaluationAdapter, DeterministicKernelAdapter
from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, TemplateRecord, UArchAgent
from fast.orchestrator import FiveAgentFlow
from fast.schemas.models import Budget, ExperimentSpec, to_primitive
from fast.storage import ExperimentStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic FAST five-agent smoke loop")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/smoke"))
    args = parser.parse_args()
    args.run_dir.mkdir(parents=True, exist_ok=True)

    spec = ExperimentSpec(
        experiment_id="fast-smoke",
        candidate_id="x8-m64",
        model="hf-internal-testing/tiny-random-LlamaForCausalLM",
        dataset="wikitext-2-raw-v1",
        sequence_length=64,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=0.01,
        seed=20260903,
        budget=Budget(),
    )
    template = TemplateRecord("smoke-template", "sha256:smoke", "memory://template", True)
    flow = FiveAgentFlow(
        KernelAgent(DeterministicKernelAdapter()),
        CompilerAgent(),
        UArchAgent((template,)),
        EvaluatorAgent(DeterministicEvaluationAdapter()),
        CriticAgent(),
        store=ExperimentStore(args.run_dir / "fast.db"),
    )
    report = flow.run(spec, template_id=template.template_id)
    output = args.run_dir / "report.json"
    output.write_text(json.dumps(to_primitive(report), indent=2) + "\n", encoding="utf-8")
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
