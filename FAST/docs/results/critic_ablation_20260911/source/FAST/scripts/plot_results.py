"""Turn DynaX evaluation runs into PNG figures for a report or slide deck.

    python FAST/scripts/plot_results.py \
        --results /scratch/.../runs/eval_matrix_*/results.json \
        --out /scratch/.../runs/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_report import load_run, pareto_front  # noqa: E402

INK, MUTED, GRID, SURFACE = "#0d1117", "#4a5567", "#dbe1ea", "#ffffff"
BLUE, ORANGE, DOMINATED = "#2a78d6", "#eb6834", "#a9a7a0"
SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#f4f6f9", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)

plt.rcParams.update({
    "figure.dpi": 160, "savefig.dpi": 160, "font.family": "DejaVu Sans", "font.size": 9,
    "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": GRID,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def _clean(axis):
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    axis.grid(True, color=GRID, lw=0.7)
    axis.set_axisbelow(True)


def _scored(run):
    return [row for row in run["rows"]
            if row["status"] == "passed" and row["method"] != "dense" and row["relative_loss"] is not None]


def figure_pareto(run, out: Path) -> Path | None:
    rows = _scored(run)
    if not rows:
        return None
    front = pareto_front(run["rows"])
    fig, axis = plt.subplots(figsize=(6.6, 4.4), constrained_layout=True)

    ordered = sorted((r for r in rows if r["method"] in front), key=lambda r: r["sparsity"])
    if len(ordered) > 1:
        axis.plot([r["sparsity"] * 100 for r in ordered], [r["relative_loss"] * 100 for r in ordered],
                  color=BLUE, lw=1.6, alpha=0.45, zorder=1)
    for row in rows:
        on_front = row["method"] in front
        axis.scatter(row["sparsity"] * 100, row["relative_loss"] * 100, s=70, zorder=3,
                     color=BLUE if on_front else DOMINATED,
                     edgecolor=SURFACE, linewidth=1.6)
        axis.annotate(row["method"], (row["sparsity"] * 100, row["relative_loss"] * 100),
                      textcoords="offset points", xytext=(0, 11), ha="center", fontsize=7.5,
                      color=INK if on_front else MUTED,
                      fontweight="bold" if on_front else "normal")
    axis.axhline(0, color=MUTED, lw=0.9, ls="-", alpha=0.5)
    axis.set_xlabel("attention scores pruned (%)")
    axis.set_ylabel("perplexity increase vs dense (%)")
    manifest = run["manifest"]
    axis.set_title(
        f"Sparsity versus quality cost\n{manifest['model'].split('/')[-1]} · "
        f"{manifest['dataset']} · {manifest['windows_evaluated']}x{manifest['sequence_length']} tokens",
        color=INK, fontweight="bold", fontsize=10)
    handles = [plt.Line2D([], [], marker="o", ls="", color=BLUE, label="Pareto frontier", markersize=7),
               plt.Line2D([], [], marker="o", ls="", color=DOMINATED, label="dominated", markersize=7)]
    axis.legend(handles=handles, frameon=False, fontsize=8, loc="upper left")
    _clean(axis)
    path = out / f"pareto_{_slug(run)}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_cost_and_sparsity(run, out: Path) -> Path | None:
    rows = _scored(run)
    if not rows:
        return None
    front = pareto_front(run["rows"])
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 0.45 * len(rows) + 2.1), constrained_layout=True)

    for axis, key, label, fmt in (
        (axes[0], "relative_loss", "perplexity increase vs dense (%)", "{:+.1f}%"),
        (axes[1], "sparsity", "attention scores pruned (%)", "{:.1f}%"),
    ):
        ordered = sorted(rows, key=lambda r: r[key])
        values = [row[key] * 100 for row in ordered]
        colors = [BLUE if row["method"] in front else DOMINATED for row in ordered]
        positions = np.arange(len(ordered))
        axis.barh(positions, values, color=colors, height=0.62)
        axis.set_yticks(positions, [row["method"] for row in ordered], fontsize=8)
        axis.set_xlabel(label)
        span = max(values) - min(min(values), 0)
        for position, value in zip(positions, values):
            axis.text(value + (0.02 * span if value >= 0 else -0.02 * span), position, fmt.format(value),
                      va="center", ha="left" if value >= 0 else "right", fontsize=7.5, color=INK)
        axis.margins(x=0.16)
        _clean(axis)
        axis.grid(axis="y", visible=False)
    axes[0].axvline(0, color=MUTED, lw=0.9)
    fig.suptitle(f"{run['manifest']['model'].split('/')[-1]} · per-configuration cost and density",
                 fontweight="bold", fontsize=10, color=INK)
    path = out / f"cost_sparsity_{_slug(run)}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_layers(run, out: Path) -> Path | None:
    rows = [row for row in run["rows"] if row.get("per_layer") and len(row["per_layer"]) > 1]
    if not rows:
        return None
    layers = sorted({int(k) for row in rows for k in row["per_layer"]})
    matrix = np.array([[row["per_layer"].get(str(layer), np.nan) for layer in layers] for row in rows])
    fig, axis = plt.subplots(figsize=(0.30 * len(layers) + 3.4, 0.42 * len(rows) + 1.9),
                             constrained_layout=True)
    image = axis.imshow(matrix * 100, cmap=SEQ, aspect="auto", interpolation="nearest")
    axis.set_yticks(np.arange(len(rows)), [row["method"] for row in rows], fontsize=8)
    step = max(1, len(layers) // 12)
    axis.set_xticks(np.arange(0, len(layers), step), [layers[i] for i in range(0, len(layers), step)], fontsize=8)
    axis.set_xlabel("decoder layer")
    axis.set_title(f"Attention values kept per layer (%)\n{run['manifest']['model'].split('/')[-1]}",
                   color=INK, fontweight="bold", fontsize=10)
    bar = fig.colorbar(image, ax=axis, fraction=0.03, pad=0.02)
    bar.set_label("kept (%)", color=MUTED, fontsize=8)
    bar.outline.set_edgecolor(GRID)
    for spine in axis.spines.values():
        spine.set_edgecolor(GRID)
    path = out / f"per_layer_{_slug(run)}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_occupancy(runs, out: Path) -> Path | None:
    """Two methods can prune equally and still differ entirely for the hardware."""
    if not any(_scored(run) for run in runs):
        return None
    families = {"X:M": BLUE, "N:M": ORANGE, "Top-K": "#1baf7a"}
    markers = ["o", "s", "^", "D", "v", "P"]
    fig, axis = plt.subplots(figsize=(7.6, 4.6), constrained_layout=True)

    run_handles = []
    for index, run in enumerate(runs):
        rows = [row for row in _scored(run) if row["occupancy"]]
        if not rows:
            continue
        marker = markers[index % len(markers)]
        axis.scatter([row["sparsity"] * 100 for row in rows], [row["occupancy"] * 100 for row in rows],
                     s=62, marker=marker, zorder=3, linewidth=1.4, edgecolor=SURFACE,
                     color=[families.get(row["family"], DOMINATED) for row in rows])
        run_handles.append(plt.Line2D([], [], marker=marker, ls="", color=MUTED, markersize=7,
                                      label=_label(run)))

    axis.set_xlabel("attention scores pruned (%)")
    axis.set_ylabel("64-wide column blocks still occupied (%)")
    axis.set_ylim(0, 108)
    axis.set_title("Same sparsity, very different value to an accelerator",
                   color=INK, fontweight="bold", fontsize=11)
    family_handles = [plt.Line2D([], [], marker="o", ls="", color=color, markersize=8, label=name)
                      for name, color in families.items()]
    family_handles.append(plt.Line2D([], [], marker="o", ls="", color=DOMINATED, markersize=8,
                                     label="Sanger / SALO"))
    first = axis.legend(handles=family_handles, frameon=False, fontsize=8.5, loc="center left",
                        bbox_to_anchor=(1.01, 0.72), title="method family")
    first.get_title().set_fontsize(8)
    first.get_title().set_color(MUTED)
    axis.add_artist(first)
    second = axis.legend(handles=run_handles, frameon=False, fontsize=8, loc="center left",
                         bbox_to_anchor=(1.01, 0.28), title="run")
    second.get_title().set_fontsize(8)
    second.get_title().set_color(MUTED)
    axis.annotate("N:M and SALO keep every column block alive:\nthe hardware still has to fetch all of them",
                  xy=(0.5, 0.965), xycoords="axes fraction", ha="center", fontsize=8, color=MUTED)
    axis.annotate("X:M concentrates what it keeps,\nso whole blocks can be skipped",
                  xy=(0.62, 0.19), xycoords="axes fraction", ha="center", fontsize=8, color=BLUE)
    _clean(axis)
    path = out / "block_occupancy.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def _label(run) -> str:
    manifest = run["manifest"]
    return f"{manifest['model'].split('/')[-1].split('-intermediate')[0]} · seq {manifest['sequence_length']}"


def _slug(run) -> str:
    manifest = run["manifest"]
    return f"{manifest['model'].split('/')[-1].replace('.', '-')}_seq{manifest['sequence_length']}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    paths = [path for path in args.results if path.is_file()]
    if not paths:
        raise SystemExit("no results.json found")
    runs = [load_run(path) for path in sorted(paths)]
    out: Path = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)

    written = []
    for run in runs:
        for builder in (figure_pareto, figure_cost_and_sparsity, figure_layers):
            path = builder(run, out)
            if path:
                written.append(path)
    path = figure_occupancy(runs, out)
    if path:
        written.append(path)
    for path in written:
        print(f"[fast] wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
