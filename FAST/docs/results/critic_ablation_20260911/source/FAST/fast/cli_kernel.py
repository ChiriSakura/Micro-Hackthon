"""Run one Kernel Agent search and write a report.

    python -m fast.cli_kernel --run-dir <dir> --proposer sweep --budget 8
    python -m fast.cli_kernel --run-dir <dir> --proposer llm   --budget 8

The two proposers see the same search space, the same measurement adapter and
the same epsilon gate, so running both at the same budget is the ablation, not
just a demo.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from fast.adapters import DynaXKernelAdapter
from fast.agents.kernel import KernelAgent
from fast.agents.llm_models import model_for
from fast.agents.proposers import LLMProposer, SweepProposer
from fast.schemas.models import Budget, ExperimentSpec, KernelSearchSpace, to_primitive

REPO_ROOT = Path(__file__).resolve().parents[2]


SYSTEM_MESSAGE = (
    "You are a careful hardware/software co-design engineer. You reason from "
    "measured numbers and never invent configurations."
)


def build_proposer(kind: str, model: str, project: str | None, location: str, backend: str):
    if kind == "sweep":
        return SweepProposer()
    if kind != "llm":
        raise ValueError(f"unknown proposer {kind!r}")
    if not project:
        raise SystemExit("--gcp-project or GCP_PROJECT is required for the llm proposer")

    if backend == "chia":
        # Routes through Ray and needs a cluster advertising `vertex_creds`.
        from chia.models.vertex import VertexGeminiLLM

        llm = VertexGeminiLLM(
            model=model, project=project, location=location,
            system_message=SYSTEM_MESSAGE, timeout_seconds=300, retries=2,
        )
    else:
        from fast.agents.llm_backends import VertexDirect

        llm = VertexDirect(
            model=model, project=project, location=location,
            system_message=SYSTEM_MESSAGE, timeout_seconds=300,
        )
    return LLMProposer(llm, model_name=model, fallback=SweepProposer())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--proposer", choices=["sweep", "llm"], default="sweep")
    # **算法是输入，不是搜索维度。** Agent 探索的是这个算法的配置，以及为它
    # 协同设计的架构；它不负责在 xm / nm / topk 之间选。要比较算法就每个跑
    # 一次这条流水线，那是一次对照实验，不是一次搜索。
    parser.add_argument(
        "--algorithm", default="xm", choices=list(KernelSearchSpace.SEARCHABLE),
        help="要为之做协同设计的稀疏注意力算法。DynaX 自己的是 xm（动态 X:M）。"
             f"基线 {'/'.join(KernelSearchSpace.BASELINES)} 的配置不在标签语法里"
             "（sanger 的阈值是 runner 的全局参数，salo 的五个参数硬编码），"
             "不能被搜索。")
    parser.add_argument("--budget", type=int, default=8, help="measurements the agent may spend")
    parser.add_argument("--batch", type=int, default=4, help="configurations measured per round")
    parser.add_argument("--block-ms", type=int, nargs="+", default=None)
    parser.add_argument("--xm-high", type=int, nargs="+", default=[8, 16, 32, 64])
    parser.add_argument("--xm-low", type=int, nargs="+", default=[4, 8, 16, 32])
    parser.add_argument("--threshold-0", type=float, nargs="+", default=None)
    parser.add_argument("--threshold-1", type=float, nargs="+", default=None)
    parser.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T")
    parser.add_argument("--dataset", default="wikitext-2-raw-v1")
    parser.add_argument("--seq-len", type=int, default=512)
    parser.add_argument("--max-samples", type=int, default=8)
    parser.add_argument("--epsilon", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--dtype", default="float32")
    parser.add_argument("--dynax-python", default=sys.executable)
    parser.add_argument("--dynax-device", default="auto")
    parser.add_argument(
        "--llm-model", default=None,
        help="覆盖该角色的默认模型；不给就用 fast/agents/llm_models.py 里的选择"
             "（kernel 角色默认最强的一档，不是最便宜的）")
    parser.add_argument("--gcp-project", default=os.environ.get("GCP_PROJECT"))
    parser.add_argument("--gcp-location", default=os.environ.get("GCP_LOCATION", "us-central1"))
    parser.add_argument(
        "--llm-backend", choices=["direct", "chia"], default="direct",
        help="direct calls Vertex straight; chia routes through Ray and needs a vertex_creds cluster",
    )
    args = parser.parse_args(argv)
    if (args.threshold_0 is None) != (args.threshold_1 is None):
        parser.error("both threshold domains must be supplied")

    run_dir: Path = args.run_dir.expanduser()
    run_dir.mkdir(parents=True, exist_ok=True)

    spec = ExperimentSpec(
        experiment_id="kernel-search",
        candidate_id=f"{args.algorithm}-{args.proposer}-b{args.budget}",
        model=args.model,
        dataset=args.dataset,
        sequence_length=args.seq_len,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=args.epsilon,
        seed=args.seed,
        sparse_method=args.algorithm,
        max_samples=args.max_samples,
        dtype=args.dtype,
        budget=Budget(
            max_candidates=args.budget,
            max_evaluations=args.budget,
            max_wall_seconds=7200,
        ),
    )
    agent = KernelAgent(
        DynaXKernelAdapter(
            dynax_root=REPO_ROOT / "DynaX",
            run_root=run_dir / "measurements",
            python_executable=args.dynax_python,
            device=args.dynax_device,
        )
    )
    report = agent.search(
        spec,
        proposer=build_proposer(
            args.proposer, args.llm_model or model_for("kernel").model, args.gcp_project,
            args.gcp_location, args.llm_backend,
        ),
        space=KernelSearchSpace(
            algorithm=args.algorithm, max_sequence_length=args.seq_len,
            xm_high=tuple(args.xm_high), xm_low=tuple(args.xm_low),
            block_ms=tuple(args.block_ms) if args.block_ms else None,
            threshold_pairs=tuple((a, b) for a in args.threshold_0 for b in args.threshold_1 if b <= a)
                            if args.threshold_0 is not None else None),
        batch=args.batch,
    )

    output = run_dir / f"kernel_search_{args.proposer}.json"
    output.write_text(json.dumps(to_primitive(report), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(output.resolve()),
        "proposer": report.proposer,
        "measured": len(report.measurements),
        "rounds": report.rounds,
        "pareto": list(report.pareto),
        "best": report.best.label if report.best else None,
        "best_sparsity": report.best.actual_sparsity if report.best else None,
        "best_quality_loss": report.best.quality_loss if report.best else None,
        "rejected": len(report.rejected),
        "wall_seconds": report.wall_seconds,
    }, indent=2))
    return 0 if report.best else 1


if __name__ == "__main__":
    raise SystemExit(main())
