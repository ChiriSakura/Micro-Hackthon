"""Render the attention masks each sparse method actually produces, as PNGs.

The masks are captured from a real forward pass on a real checkpoint, not drawn
from the method's nominal ratio: the script wraps ``prune_attn_scores`` inside
the model under test and keeps the tensor the kernel returned.

    python plot_attention_masks.py \
        --model TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T \
        --seq-len 512 --layer 10 --head 0 --out figures/

★ FAST 新增，非 DynaX 上游文件。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.colors import LinearSegmentedColormap, LogNorm
import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoConfig, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataUtil import get_dataset  # noqa: E402
from models.utils.runtime_config import set_dynax_config  # noqa: E402
from run_eval_matrix import BASE_CONFIG, method_config  # noqa: E402


INK = "#0d1117"
MUTED = "#4a5567"
GRID = "#dbe1ea"
BLUE = "#2a78d6"
SURFACE = "#ffffff"
KEPT_CMAP = LinearSegmentedColormap.from_list("kept", ["#f4f6f9", BLUE])
KEPT_CMAP.set_bad(SURFACE)  # above-diagonal cells the causal mask always removes
PROB_CMAP = LinearSegmentedColormap.from_list(
    "prob", ["#f4f6f9", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)

plt.rcParams.update({
    "figure.dpi": 160,
    "savefig.dpi": 160,
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "text.color": INK,
    "axes.labelcolor": MUTED,
    "axes.edgecolor": GRID,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlesize": 9,
    "figure.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def install_spy(model_type: str, layer: int, sink: dict):
    """Wrap the model's own reference to prune_attn_scores and keep one layer."""
    module_name = "models.llama_modeling" if model_type == "llama" else "models.bloom_modeling"
    module = sys.modules[module_name]
    original = module.prune_attn_scores

    def spy(attn_scores, attn_mask, *args, **kwargs):
        mask = original(attn_scores, attn_mask, *args, **kwargs)
        if kwargs.get("layer_idx") == layer and "kept" not in sink:
            sink["scores"] = attn_scores.detach().float().cpu()
            sink["kept"] = (mask.detach().cpu() == 0)
        return mask

    module.prune_attn_scores = spy
    return lambda: setattr(module, "prune_attn_scores", original)


def load_model(model_name: str, dtype, tokenizer):
    hf_config = AutoConfig.from_pretrained(model_name)
    model_type = getattr(hf_config, "model_type", "")
    if model_type == "llama":
        from models.llama_modeling import LlamaForCausalLM as Model
    elif model_type == "bloom":
        from models.bloom_modeling import BloomForCausalLM as Model
    else:
        raise ValueError(f"model_type={model_type!r} has no DynaX implementation")
    model = Model.from_pretrained(model_name, torch_dtype=dtype, pad_token_id=tokenizer.pad_token_id)
    model.config.pad_token_id = tokenizer.pad_token_id
    return model, model_type, hf_config


def capture(model, tokens, config, model_type, layer, device) -> dict:
    sink: dict = {}
    restore = install_spy(model_type, layer, sink)
    try:
        set_dynax_config(config)
        with torch.no_grad():
            model(tokens.to(device), use_cache=False)
    finally:
        restore()
        set_dynax_config(None)
    if "kept" not in sink:
        raise RuntimeError(f"layer {layer} never called prune_attn_scores; is the model deep enough?")
    return sink


def panel_stats(kept: np.ndarray) -> dict:
    """Causal-only statistics: positions above the diagonal are never candidates."""
    length = kept.shape[-1]
    causal = np.tril(np.ones((length, length), dtype=bool))
    candidates = causal.sum()
    retained = (kept & causal).sum()
    per_row = (kept & causal).sum(axis=-1)
    blocks = kept.reshape(length, length // 64, 64) if length % 64 == 0 else None
    occupancy = float(blocks.any(axis=-1).mean()) if blocks is not None else float("nan")
    return {
        "sparsity": 1.0 - retained / candidates,
        "kept_min": int(per_row.min()),
        "kept_max": int(per_row.max()),
        "kept_mean": float(per_row.mean()),
        "block_occupancy": occupancy,
        "per_row": per_row,
    }


def figure_masks(reference, panels, meta, out: Path) -> Path:
    columns = len(panels) + 1
    rows = 2 if columns > 4 else 1
    per_row = (columns + rows - 1) // rows
    fig, axes = plt.subplots(rows, per_row, figsize=(2.35 * per_row, 2.65 * rows), constrained_layout=True)
    axes = np.atleast_1d(axes).ravel()

    probs = reference["probs"]
    floor = max(probs[probs > 0].min(), 1e-8)
    axes[0].imshow(np.maximum(probs, floor), cmap=PROB_CMAP,
                   norm=LogNorm(vmin=floor, vmax=probs.max()), interpolation="nearest", aspect="equal")
    axes[0].set_title("dense attention\nprobability (log)", color=INK, fontweight="bold")
    axes[0].set_ylabel("query position", fontsize=7.5)

    for axis, (label, kept, stats) in zip(axes[1:], panels):
        # Positions above the diagonal are removed by the causal mask regardless of
        # what the pruner emitted, so showing them would overstate what is kept.
        causal = np.tril(np.ones_like(kept, dtype=bool))
        shown = np.where(causal, kept.astype(float), np.nan)
        axis.imshow(shown, cmap=KEPT_CMAP, vmin=0, vmax=1, interpolation="nearest", aspect="equal")
        axis.set_title(
            f"{label}\n{stats['sparsity'] * 100:.1f}% pruned · "
            f"{stats['kept_min']}–{stats['kept_max']} kept/row",
            color=INK,
        )
    for axis in axes[len(panels) + 1:]:
        axis.axis("off")
    for axis in axes[: len(panels) + 1]:
        axis.set_xticks([]); axis.set_yticks([])
        for spine in axis.spines.values():
            spine.set_edgecolor(GRID)

    fig.suptitle(
        f"Retained attention positions · {meta['model'].split('/')[-1]} · "
        f"layer {meta['layer']}, head {meta['head']} · {meta['seq_len']} tokens\n"
        f"percentages are over the causal region of this one head, not the whole model",
        fontsize=10, fontweight="bold", color=INK,
    )
    path = out / "attention_masks.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_kept_distribution(panels, meta, out: Path) -> Path:
    fig, axis = plt.subplots(figsize=(7.2, 3.4), constrained_layout=True)
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
    for (label, _kept, stats), color in zip(panels, colors):
        rows = np.arange(1, len(stats["per_row"]) + 1)
        axis.plot(rows, stats["per_row"], lw=1.4, color=color, label=label)
    axis.set_xlabel("query position (context length available to that row)")
    axis.set_ylabel("attention values kept")
    axis.set_title(
        f"Kept values per query row · {meta['model'].split('/')[-1]} · layer {meta['layer']}, head {meta['head']}",
        color=INK, fontweight="bold",
    )
    axis.grid(True, color=GRID, lw=0.7)
    axis.set_axisbelow(True)
    for spine in ("top", "right"):
        axis.spines[spine].set_visible(False)
    axis.legend(frameon=False, ncols=3, fontsize=7.5, loc="upper left")
    path = out / "kept_per_row.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset", default="wiki", choices=["wiki", "ptb", "c4"])
    parser.add_argument("--seq-len", type=int, default=512)
    parser.add_argument("--layer", type=int, default=10)
    parser.add_argument("--head", type=int, default=0)
    parser.add_argument("--methods", default="xm,xm:32:16:64,nm:16:64,topk:64,sanger,salo")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=20260903)
    args = parser.parse_args()

    out: Path = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    device = torch.device(
        ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    )
    dtype = torch.float32
    torch.manual_seed(args.seed)

    tokenizer = AutoTokenizer.from_pretrained(args.model, legacy=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model, model_type, hf_config = load_model(args.model, dtype, tokenizer)
    model.to(device).eval()

    tokens = get_dataset(tokenizer, seqlen=args.seq_len, dataset=args.dataset).input_ids
    window = tokens[:, : args.seq_len]
    print(f"[fast] captured window of {window.shape[-1]} tokens", flush=True)

    # A pass that keeps everything gives the true dense probabilities at this layer.
    reference_config = dict(BASE_CONFIG)
    reference_config.update({"is_sparse": True, "is_quant": False,
                             "sparse_methed": "sanger", "threshold_sanger": -1.0})
    reference = capture(model, window, reference_config, model_type, args.layer, device)
    probs = torch.softmax(reference["scores"][0, args.head], dim=-1).numpy()
    print("[fast] dense reference captured", flush=True)

    panels = []
    summary = {}
    for method in [item.strip() for item in args.methods.split(",") if item.strip()]:
        config = method_config(method, {"topk": min(BASE_CONFIG["topk"], args.seq_len // 8)})
        sink = capture(model, window, config, model_type, args.layer, device)
        kept = sink["kept"][0, args.head].numpy()
        stats = panel_stats(kept)
        panels.append((method, kept, stats))
        summary[method] = {k: (v if not isinstance(v, np.ndarray) else None)
                           for k, v in stats.items() if k != "per_row"}
        print(f"[fast] {method}: {stats['sparsity'] * 100:.2f}% pruned, "
              f"{stats['kept_min']}–{stats['kept_max']} kept/row", flush=True)

    meta = {"model": args.model, "layer": args.layer, "head": args.head, "seq_len": args.seq_len,
            "dataset": args.dataset, "layers_total": getattr(hf_config, "num_hidden_layers", None)}
    written = [
        figure_masks({"probs": probs}, panels, meta, out),
        figure_kept_distribution(panels, meta, out),
    ]
    (out / "mask_stats.json").write_text(
        json.dumps({"meta": meta, "methods": summary}, indent=2) + "\n", encoding="utf-8"
    )
    for path in written:
        print(f"[fast] wrote {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
