"""Aggregate one or more DynaX eval-matrix runs into tables and a summary JSON.

Usage:
    python scripts/legacy/summarize_eval.py RUN_DIR [RUN_DIR ...] --out-dir docs/results
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


COLUMNS = [
    ("method", "Method", "{}"),
    ("perplexity", "Perplexity", "{:.4f}"),
    ("perplexity_delta", "ΔPPL", "{:+.4f}"),
    ("relative_quality_loss", "Rel. loss", "{:+.2%}"),
    ("mean_sparsity", "Sparsity", "{:.2%}"),
    ("mean_causal_kept_ratio", "Causal kept", "{:.2%}"),
    ("mean_index_entropy", "Index entropy", "{:.4f}"),
    ("mean_block_occupancy", "Block occupancy", "{:.2%}"),
    ("wall_seconds", "Wall (s)", "{:.2f}"),
    ("speed_ratio_vs_dense", "Speed vs dense", "{:.2f}×"),
]


def flatten(record: dict[str, Any]) -> dict[str, Any]:
    stats = record.get("sparsity_stats") or {}
    method_stats = next(iter(stats.values()), {}) if stats else {}
    flat = {
        "method": record["method"],
        "status": record["status"],
        "error": record.get("error"),
        "config_digest": record.get("config_digest"),
        "perplexity": record.get("perplexity"),
        "mean_nll": record.get("mean_nll"),
        "perplexity_delta": record.get("perplexity_delta"),
        "relative_quality_loss": record.get("relative_quality_loss"),
        "wall_seconds": record.get("wall_seconds"),
        "seconds_per_window": record.get("seconds_per_window"),
        "speed_ratio_vs_dense": record.get("speed_ratio_vs_dense"),
        "peak_memory_bytes": record.get("peak_memory_bytes"),
        "windows": record.get("windows"),
        "tokens": record.get("tokens"),
    }
    for key in (
        "mean_sparsity",
        "mean_kept_ratio",
        "mean_index_entropy",
        "mean_block_occupancy",
        "mean_causal_kept_ratio",
        "calls",
        "row_kept_min",
        "row_kept_max",
    ):
        flat[key] = method_stats.get(key)
    flat["per_layer_kept_ratio"] = method_stats.get("per_layer_mean_kept_ratio", {})
    flat["config"] = record.get("config", {})
    return flat


def markdown_table(rows: list[dict[str, Any]]) -> str:
    header = "| " + " | ".join(label for _, label, _ in COLUMNS) + " |"
    divider = "|" + "|".join("---" for _ in COLUMNS) + "|"
    lines = [header, divider]
    for row in rows:
        cells = []
        for key, _, fmt in COLUMNS:
            value = row.get(key)
            cells.append("—" if value is None else (fmt.format(value) if not isinstance(value, str) else value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def pareto_front(rows: list[dict[str, Any]]) -> list[str]:
    """Methods not dominated on (higher sparsity, lower relative quality loss)."""
    usable = [
        row for row in rows
        if row["status"] == "passed" and row.get("mean_sparsity") is not None
        and row.get("relative_quality_loss") is not None
    ]
    front = []
    for row in usable:
        dominated = any(
            other is not row
            and other["mean_sparsity"] >= row["mean_sparsity"]
            and other["relative_quality_loss"] <= row["relative_quality_loss"]
            and (
                other["mean_sparsity"] > row["mean_sparsity"]
                or other["relative_quality_loss"] < row["relative_quality_loss"]
            )
            for other in usable
        )
        if not dominated:
            front.append(row["method"])
    return front


def load_run(run_dir: Path) -> dict[str, Any]:
    payload = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    rows = [flatten(record) for record in payload["results"]]
    return {
        "run_dir": str(run_dir),
        "manifest": payload["manifest"],
        "rows": rows,
        "pareto_front": pareto_front(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    runs = [load_run(path.expanduser()) for path in args.run_dirs]
    summary = {"schema_version": "0.2", "runs": runs}
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    sections = ["# DynaX 稀疏注意力评估结果\n"]
    for run in runs:
        manifest = run["manifest"]
        sections.append(
            f"## {manifest['model']} · {manifest['dataset']} · seq={manifest['sequence_length']}\n\n"
            f"- 设备：{manifest['device']}"
            + (f" ({manifest['gpu']})" if manifest.get("gpu") else "")
            + f"，dtype={manifest['dtype']}\n"
            f"- 参数量：{manifest['parameters']:,}，层数：{manifest['hidden_layers']}，注意力头：{manifest['attention_heads']}\n"
            f"- 评估窗口：{manifest['windows_evaluated']} / {manifest['windows_available']}，seed={manifest['seed']}\n"
            f"- Slurm 作业：{manifest.get('slurm_job_id')}，生成时间：{manifest['generated_at']}\n\n"
            + markdown_table(run["rows"])
            + f"\n\nPareto 前沿（稀疏率↑ / 相对精度损失↓）：{', '.join(run['pareto_front']) or '—'}\n"
        )
    (args.out_dir / "results.md").write_text("\n".join(sections), encoding="utf-8")
    print((args.out_dir / "results.md").resolve())
    print("\n".join(sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
