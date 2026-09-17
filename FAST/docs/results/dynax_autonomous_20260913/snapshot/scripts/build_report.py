"""Aggregate DynaX evaluation runs into a Markdown table and an HTML dashboard.

The generator is data-driven: point it at one or more ``results.json`` files
produced by ``DynaX/run_eval_matrix.py`` and it emits a combined ``report.json``,
a ``report.md`` for the repository, and a self-contained ``report.html``.

    python FAST/scripts/build_report.py \
        --results /scratch/.../runs/eval_matrix_*/results.json \
        --out /scratch/.../runs/report
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


FAMILIES = (
    ("dense", "Dense"),
    ("xm", "X:M"),
    ("nm", "N:M"),
    ("topk", "Top-K"),
    ("sanger", "Sanger"),
    ("salo", "SALO"),
)


def family_of(method: str) -> str:
    head = method.split(":")[0]
    for prefix, label in FAMILIES:
        if head == prefix:
            return label
    if head == "quant_xm":
        return "X:M + quant"
    return head


def load_run(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    manifest = payload["manifest"]
    dense = next(
        (item for item in payload["results"] if item["method"] == "dense" and item["status"] == "passed"),
        None,
    )
    rows = []
    for record in payload["results"]:
        stats = record.get("sparsity_stats") or {}
        method_stats = next(iter(stats.values()), {})
        loss = record.get("relative_quality_loss")
        rows.append(
            {
                "method": record["method"],
                "family": family_of(record["method"]),
                "status": record["status"],
                "error": record.get("error"),
                "perplexity": record.get("perplexity"),
                "relative_loss": loss,
                "sparsity": method_stats.get("mean_sparsity", 0.0),
                "causal_kept": method_stats.get("mean_causal_kept_ratio"),
                "entropy": method_stats.get("mean_index_entropy", 0.0),
                "occupancy": method_stats.get("mean_block_occupancy", 0.0),
                "row_kept_min": method_stats.get("row_kept_min"),
                "row_kept_max": method_stats.get("row_kept_max"),
                "calls": method_stats.get("calls"),
                "wall_seconds": record.get("wall_seconds"),
                "tokens": record.get("tokens"),
                "windows": record.get("windows"),
                "config_digest": record.get("config_digest"),
                "per_layer": method_stats.get("per_layer_mean_kept_ratio", {}),
            }
        )
    complete = manifest.get("complete")
    requested = manifest.get("methods_requested")
    partial = complete is False or (requested is not None and len(rows) < len(requested))
    return {
        "id": (f"{manifest.get('model', 'model')} · {manifest.get('dataset')} · "
               f"seq {manifest.get('sequence_length')}" + (" · in progress" if partial else "")),
        "partial": partial,
        "pending_methods": [m for m in (requested or []) if m not in {row["method"] for row in rows}],
        "source": str(path),
        "manifest": manifest,
        "dense_perplexity": dense["perplexity"] if dense else None,
        "rows": rows,
    }


def pareto_front(rows: list[dict[str, Any]]) -> set[str]:
    """Methods that no other method beats on both sparsity and quality loss."""
    candidates = [
        row for row in rows
        if row["status"] == "passed" and row["method"] != "dense" and row["relative_loss"] is not None
    ]
    front = set()
    for row in candidates:
        dominated = any(
            other["sparsity"] >= row["sparsity"]
            and other["relative_loss"] <= row["relative_loss"]
            and (other["sparsity"] > row["sparsity"] or other["relative_loss"] < row["relative_loss"])
            for other in candidates
        )
        if not dominated:
            front.add(row["method"])
    return front


def markdown(runs: list[dict[str, Any]]) -> str:
    lines = ["# DynaX sparse-attention evaluation", ""]
    lines.append(f"Generated {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    for run in runs:
        manifest = run["manifest"]
        front = pareto_front(run["rows"])
        lines.append(f"## {run['id']}")
        lines.append("")
        if run["partial"]:
            lines.append(
                f"> Run still in progress: {len(run['rows'])} of "
                f"{len(run['rows']) + len(run['pending_methods'])} configurations measured. "
                f"Pending: {', '.join(run['pending_methods']) or 'unknown'}."
            )
            lines.append("")
        lines.append(
            f"- Model: `{manifest.get('model')}` "
            f"({manifest.get('parameters', 0):,} parameters, {manifest.get('hidden_layers')} layers, "
            f"{manifest.get('attention_heads')} heads)"
        )
        lines.append(
            f"- Data: {manifest.get('dataset')}, sequence length {manifest.get('sequence_length')}, "
            f"{manifest.get('windows_evaluated')} of {manifest.get('windows_available')} windows"
        )
        lines.append(
            f"- Runtime: {manifest.get('device')} / {manifest.get('gpu') or manifest.get('host')}, "
            f"{manifest.get('dtype')}, seed {manifest.get('seed')}, Slurm job {manifest.get('slurm_job_id')}"
        )
        lines.append("")
        lines.append(
            "| Method | Perplexity | Δ vs dense | Sparsity | Index entropy | Block occupancy | "
            "Kept/row | Wall (s) | Pareto |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|:---:|")
        for row in run["rows"]:
            if row["status"] != "passed":
                lines.append(f"| `{row['method']}` | failed | — | — | — | — | — | — | |")
                continue
            delta = "baseline" if row["method"] == "dense" else f"{100 * (row['relative_loss'] or 0):+.2f}%"
            kept = (
                f"{row['row_kept_min']:.0f}–{row['row_kept_max']:.0f}"
                if row["row_kept_min"] is not None else "—"
            )
            lines.append(
                f"| `{row['method']}` | {row['perplexity']:.4f} | {delta} | "
                f"{100 * row['sparsity']:.2f}% | {row['entropy']:.4f} | {row['occupancy']:.4f} | "
                f"{kept} | {row['wall_seconds']:.1f} | {'●' if row['method'] in front else ''} |"
            )
        lines.append("")
    lines.append("Sparsity is the fraction of attention scores pruned, measured on the mask itself.")
    lines.append("Index entropy is the normalised entropy of retained columns (1.0 = spread evenly).")
    lines.append("Block occupancy is the fraction of 64-wide column blocks holding any retained value.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="DynaX Sparse Attention")
    args = parser.parse_args()

    paths = [path for path in args.results if path.is_file()]
    if not paths:
        raise SystemExit("no results.json found among the given paths")
    runs = [load_run(path) for path in sorted(paths)]
    for run in runs:
        run["pareto"] = sorted(pareto_front(run["rows"]))

    out: Path = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "runs": runs}
    (out / "report.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out / "report.md").write_text(markdown(runs), encoding="utf-8")

    template = Path(__file__).resolve().parent / "report_template.html"
    html = template.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(payload, separators=(",", ":"))
    ).replace("__TITLE__", args.title)
    (out / "report.html").write_text(html, encoding="utf-8")

    print(json.dumps({
        "report_json": str((out / "report.json").resolve()),
        "report_md": str((out / "report.md").resolve()),
        "report_html": str((out / "report.html").resolve()),
        "runs": [run["id"] for run in runs],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
