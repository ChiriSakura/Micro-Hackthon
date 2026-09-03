"""GPU smoke test for DynaX sparse-attention kernels.

This deliberately uses synthetic tensors so the core pruning algorithms can be
validated before downloading a model or dataset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from models.utils.sparse_attention import prune_attn_scores, quant_qk_matmul


def _kept(mask: torch.Tensor) -> torch.Tensor:
    assert mask.shape == (1, 2, 64, 64)
    assert torch.all((mask == 0) | (mask == -10000))
    return mask == 0


def _check_attention(scores: torch.Tensor, mask: torch.Tensor) -> None:
    probabilities = torch.softmax(scores + mask, dim=-1)
    assert torch.isfinite(probabilities).all()
    torch.testing.assert_close(
        probabilities.sum(dim=-1),
        torch.ones_like(probabilities.sum(dim=-1)),
    )


def run() -> dict[str, object]:
    if not torch.cuda.is_available():
        raise RuntimeError("This smoke test requires a CUDA GPU allocation")

    torch.manual_seed(20260903)
    torch.cuda.manual_seed_all(20260903)
    device = torch.device("cuda")
    scores = torch.randn(1, 2, 64, 64, device=device)
    attention_mask = torch.zeros(1, 1, 64, 64, device=device)

    masks = {
        "xm": prune_attn_scores(
            scores, attention_mask, threshold_0=1.0, threshold_1=0.1, sparse_method="xm"
        ),
        "nm": prune_attn_scores(scores, attention_mask, m=64, n=16, sparse_method="nm"),
        "topk": prune_attn_scores(scores, attention_mask, topk=8, sparse_method="topk"),
        "sanger": prune_attn_scores(
            scores, attention_mask, threshold=1e-4, sparse_method="sanger"
        ),
        "salo": prune_attn_scores(scores, attention_mask, sparse_method="salo"),
    }

    kept = {name: _kept(mask) for name, mask in masks.items()}
    assert torch.all(kept["nm"].sum(dim=-1) == 16)
    assert torch.all(kept["topk"].sum(dim=-1) == 8)
    assert torch.all((kept["xm"].sum(dim=-1) == 8) | (kept["xm"].sum(dim=-1) == 16))
    for mask in masks.values():
        _check_attention(scores, mask)

    # X:M should be deterministic for the same scores and seed-independent path.
    xm_again = prune_attn_scores(
        scores, attention_mask, threshold_0=1.0, threshold_1=0.1, sparse_method="xm"
    )
    assert torch.equal(masks["xm"], xm_again)

    query = torch.randn(1, 2, 64, 16, device=device)
    key = torch.randn(1, 2, 16, 64, device=device)
    for method in ("1_2_4bit", "1_4_6bit"):
        qk = quant_qk_matmul(method, query, key, torch.matmul)
        assert qk.shape == (1, 2, 64, 64)
        assert torch.isfinite(qk).all()

    properties = torch.cuda.get_device_properties(0)
    return {
        "status": "passed",
        "seed": 20260903,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "gpu": properties.name,
        "gpu_memory_gib": round(properties.total_memory / 2**30, 2),
        "shape": list(scores.shape),
        "kept_fraction": {
            name: round(mask.float().mean().item(), 6) for name, mask in kept.items()
        },
        "checks": [
            "valid additive masks",
            "finite normalized attention",
            "N:M cardinality",
            "Top-K cardinality",
            "X:M cardinality and determinism",
            "Sanger path",
            "SALO path",
            "quantized QK paths",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
