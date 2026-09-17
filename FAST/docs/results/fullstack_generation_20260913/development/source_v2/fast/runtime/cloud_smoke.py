"""Run the five-agent graph on a live CHIA cluster and prove where it ran.

A cluster smoke test that only reports "passed" is worthless here: if the cloud
worker never joined, every task would quietly run on the head and the run would
still succeed. So each stage is pinned to a resource only the remote worker
advertises, and the placement of every task is reported and checked.

    python -m fast.runtime.cloud_smoke --output <dir>/cloud_report.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket

import ray

from chia.base.ChiaFunction import ChiaFunction, get
from fast.adapters import DeterministicEvaluationAdapter, DeterministicKernelAdapter
from fast.agents import TemplateRecord, UArchAgent
from fast.runtime.chia_nodes import (
    compiler_node,
    critic_node,
    evaluator_node,
    kernel_node,
    uarch_node,
)
from fast.runtime.runtime_env import fast_runtime_env
from fast.schemas.models import Budget, ExperimentSpec, RunReport, to_primitive


@ChiaFunction(num_cpus=0.25, max_retries=0)
def where_am_i() -> dict:
    """Report the machine a task landed on, plus proof FAST was importable."""
    import fast  # noqa: F401  - the import itself is the assertion
    from fast.schemas.models import SCHEMA_VERSION

    return {
        "hostname": socket.gethostname(),
        "node_ip": ray.util.get_node_ip_address(),
        "python": ".".join(map(str, __import__("sys").version_info[:3])),
        "ray": ray.__version__,
        "fast_schema_version": SCHEMA_VERSION,
    }


def spec_for_smoke() -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="fast-cloud-smoke",
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


def run(worker_resource: str, output: Path) -> dict:
    cluster = ray.cluster_resources()
    if worker_resource not in cluster:
        raise SystemExit(
            f"the cluster advertises no {worker_resource!r} resource, so nothing would run remotely.\n"
            f"visible resources: {sorted(cluster)}"
        )

    head_ip = ray.util.get_node_ip_address()
    placement = ray.get(where_am_i.options(resources={worker_resource: 0.25}).remote())
    if placement["node_ip"] == head_ip:
        raise SystemExit(
            f"the {worker_resource!r} task ran on the head ({head_ip}); the remote worker did not take it"
        )

    # Every stage is pinned to the remote worker so a missing worker fails the
    # run rather than silently falling back to the head.
    pin = {"resources": {worker_resource: 0.25}}
    uarch = UArchAgent((
        TemplateRecord("smoke-template", "sha256:smoke", "memory://template", True),
    ))
    kernel_ref = kernel_node.options(**pin).chia_remote(spec_for_smoke(), DeterministicKernelAdapter())
    compiler_ref = compiler_node.options(**pin).chia_remote(kernel_ref)
    hardware_ref = uarch_node.options(**pin).chia_remote(compiler_ref, uarch, "smoke-template")
    evaluation_ref = evaluator_node.options(**pin).chia_remote(
        spec_for_smoke(), hardware_ref, DeterministicEvaluationAdapter()
    )
    critique_ref = critic_node.options(**pin).chia_remote(
        spec_for_smoke(), kernel_ref, compiler_ref, hardware_ref, evaluation_ref
    )
    kernel, compiler, hardware, evaluation, critique = get(
        [kernel_ref, compiler_ref, hardware_ref, evaluation_ref, critique_ref]
    )
    report = RunReport(spec_for_smoke(), kernel, compiler, hardware, evaluation, critique)

    payload = {
        "head_ip": head_ip,
        "head_hostname": socket.gethostname(),
        "worker_resource": worker_resource,
        "worker_placement": placement,
        "cluster_resources": {k: v for k, v in sorted(cluster.items())},
        "nodes": [
            {"ip": node["NodeManagerAddress"], "alive": node["Alive"], "resources": node["Resources"]}
            for node in ray.nodes()
        ],
        "report": to_primitive(report),
        "functional_passed": bool(evaluation and evaluation.functional_passed),
        "decision": critique.decision.value,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker-resource", default="fast_cpu")
    parser.add_argument("--address", default="auto")
    args = parser.parse_args()

    # Connecting to an existing cluster must not try to place Ray's own temp
    # directory: that is the head's decision, and passing it here is rejected.
    options = {"address": args.address, "runtime_env": fast_runtime_env()}
    if args.address in {"", "local", None}:
        options["address"] = None
        options["_temp_dir"] = f"/tmp/fast-ray-{os.getuid()}-{os.getpid()}"
    ray.init(**options)
    try:
        payload = run(args.worker_resource, args.output)
    finally:
        ray.shutdown()

    print(json.dumps({
        "output": str(args.output.resolve()),
        "ran_on": payload["worker_placement"]["hostname"],
        "worker_ip": payload["worker_placement"]["node_ip"],
        "head_ip": payload["head_ip"],
        "worker_python": payload["worker_placement"]["python"],
        "worker_ray": payload["worker_placement"]["ray"],
        "functional_passed": payload["functional_passed"],
        "decision": payload["decision"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
