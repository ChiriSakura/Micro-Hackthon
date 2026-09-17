"""Execute all five FAST agents as a real local CHIA/Ray task graph."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import ray

from chia.base.ChiaFunction import get
from fast.adapters import DeterministicEvaluationAdapter, DeterministicKernelAdapter
from fast.agents import TemplateRecord, UArchAgent
from fast.runtime.chia_nodes import (
    compiler_node,
    critic_node,
    evaluator_node,
    kernel_node,
    uarch_node,
)
from fast.schemas.models import Budget, ExperimentSpec, RunReport, to_primitive


def run(output: Path) -> RunReport:
    spec = ExperimentSpec(
        experiment_id="fast-chia-smoke",
        candidate_id="x8-m64",
        model="tiny-llama",
        dataset="wikitext-2-raw-v1",
        sequence_length=64,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=0.01,
        seed=20260903,
        budget=Budget(),
    )
    uarch = UArchAgent((
        TemplateRecord("smoke-template", "sha256:smoke", "memory://template", True),
    ))

    # Empty per-call resources make this smoke portable to a single local Ray
    # node. Production dispatch supplies the labels in RESOURCE_LABELS.
    kernel_ref = kernel_node.options(resources={}).chia_remote(
        spec, DeterministicKernelAdapter()
    )
    compiler_ref = compiler_node.options(resources={}).chia_remote(kernel_ref)
    hardware_ref = uarch_node.options(resources={}).chia_remote(
        compiler_ref, uarch, "smoke-template"
    )
    evaluation_ref = evaluator_node.options(resources={}).chia_remote(
        spec, hardware_ref, DeterministicEvaluationAdapter()
    )
    critique_ref = critic_node.options(resources={}).chia_remote(
        spec, kernel_ref, compiler_ref, hardware_ref, evaluation_ref
    )
    kernel, compiler, hardware, evaluation, critique = get([
        kernel_ref, compiler_ref, hardware_ref, evaluation_ref, critique_ref
    ])
    report = RunReport(spec, kernel, compiler, hardware, evaluation, critique)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(to_primitive(report), indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Ray's AF_UNIX sockets must stay below Linux's 107-byte path limit. The
    # project scratch root is intentionally long, so keep ephemeral sockets in
    # node-local /tmp while reports and databases remain on scratch.
    ray.init(_temp_dir=f"/tmp/fast-ray-{os.getuid()}-{os.getpid()}")
    try:
        report = run(args.output)
    finally:
        ray.shutdown()
    print(json.dumps({
        "output": str(args.output.resolve()),
        "decision": report.critique.decision.value,
        "functional_passed": report.evaluation.functional_passed if report.evaluation else False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
