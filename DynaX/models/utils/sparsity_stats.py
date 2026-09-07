"""Explicit, per-run collection of sparse-attention statistics.

The previous implementation accumulated module-level counters and appended to
``sparsity_<method>.txt`` in the current working directory, which made results
depend on process history and on where the interpreter happened to be started.
This module keeps the same measurements but stores them in an explicit recorder
that a caller owns, resets, and serialises into a candidate-specific directory.

★ FAST 新增，非 DynaX 上游文件。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
from typing import Any

import torch


@dataclass
class MethodStats:
    """Running statistics for one sparse-attention method."""

    calls: int = 0
    kept_ratio_sum: float = 0.0
    causal_kept_ratio_sum: float = 0.0
    mean_len_sum: float = 0.0
    index_entropy_sum: float = 0.0
    block_occupancy_sum: float = 0.0
    row_kept_min: float = math.inf
    row_kept_max: float = 0.0
    per_layer_kept_ratio_sum: dict[int, float] = field(default_factory=dict)
    per_layer_calls: dict[int, int] = field(default_factory=dict)

    # Distributions, not just means. A compiler schedules tiles and balances PE
    # load from the shape of these; an average hides exactly the imbalance that
    # makes a systolic array idle.
    bins: int = 32
    row_density_histogram: list[int] = field(default_factory=list)
    block_density_histogram: list[int] = field(default_factory=list)
    load_imbalance_sum: float = 0.0
    column_top1_mass_sum: float = 0.0
    column_top5_mass_sum: float = 0.0
    column_top10_mass_sum: float = 0.0
    per_layer_imbalance_sum: dict[int, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        if self.calls == 0:
            return {"calls": 0}
        per_layer = {
            str(layer): self.per_layer_kept_ratio_sum[layer] / self.per_layer_calls[layer]
            for layer in sorted(self.per_layer_kept_ratio_sum)
        }
        return {
            "calls": self.calls,
            "mean_kept_ratio": self.kept_ratio_sum / self.calls,
            "mean_sparsity": 1.0 - self.kept_ratio_sum / self.calls,
            "mean_causal_kept_ratio": self.causal_kept_ratio_sum / self.calls,
            "mean_sequence_length": self.mean_len_sum / self.calls,
            "mean_index_entropy": self.index_entropy_sum / self.calls,
            "mean_block_occupancy": self.block_occupancy_sum / self.calls,
            "row_kept_min": None if self.row_kept_min is math.inf else self.row_kept_min,
            "row_kept_max": self.row_kept_max,
            "per_layer_mean_kept_ratio": per_layer,
            # --- the sparse-index profile the compiler layer consumes ---
            "histogram_bins": self.bins,
            "row_density_histogram": list(self.row_density_histogram),
            "block_density_histogram": list(self.block_density_histogram),
            "mean_load_imbalance": self.load_imbalance_sum / self.calls,
            "column_top1_mass": self.column_top1_mass_sum / self.calls,
            "column_top5_mass": self.column_top5_mass_sum / self.calls,
            "column_top10_mass": self.column_top10_mass_sum / self.calls,
            "per_layer_mean_load_imbalance": {
                str(layer): self.per_layer_imbalance_sum[layer] / self.per_layer_calls[layer]
                for layer in sorted(self.per_layer_imbalance_sum)
            },
        }


class SparsityRecorder:
    """Collects mask statistics for one evaluation run."""

    BLOCK = 64

    def __init__(self, *, enabled: bool = True, block_size: int = BLOCK):
        self.enabled = enabled
        self.block_size = block_size
        self.methods: dict[str, MethodStats] = {}

    def reset(self) -> None:
        self.methods = {}

    def record(
        self,
        method: str,
        kept_mask: torch.Tensor,
        attn_mask: torch.Tensor,
        *,
        causal_kept_ratio: float,
        layer_idx: int | None = None,
    ) -> None:
        """Record one pruning call.

        ``kept_mask`` is a boolean tensor that is True where the score survives.
        ``causal_kept_ratio`` is the causal-masked ratio produced by the legacy
        ``_eval_overall_sparsity`` helper, kept for continuity with earlier runs.
        """
        if not self.enabled:
            return
        stats = self.methods.setdefault(method, MethodStats())
        with torch.no_grad():
            kept = kept_mask.detach()
            kept_float = kept.to(torch.float32)
            kept_ratio = kept_float.mean().item()
            row_kept = kept_float.sum(dim=-1)
            row_min = row_kept.min().item()
            row_max = row_kept.max().item()
            mean_len = (attn_mask.detach() > -1).to(torch.float32).sum(dim=-1).mean().item()
            entropy = _index_entropy(kept_float)
            occupancy = _block_occupancy(kept, self.block_size)
            profile = _distribution_profile(kept, self.block_size, stats.bins)

        stats.calls += 1
        _accumulate(stats.row_density_histogram, profile["row_density_histogram"])
        _accumulate(stats.block_density_histogram, profile["block_density_histogram"])
        stats.load_imbalance_sum += profile["load_imbalance"]
        stats.column_top1_mass_sum += profile["column_top1_mass"]
        stats.column_top5_mass_sum += profile["column_top5_mass"]
        stats.column_top10_mass_sum += profile["column_top10_mass"]
        stats.kept_ratio_sum += kept_ratio
        stats.causal_kept_ratio_sum += causal_kept_ratio
        stats.mean_len_sum += mean_len
        stats.index_entropy_sum += entropy
        stats.block_occupancy_sum += occupancy
        stats.row_kept_min = min(stats.row_kept_min, row_min)
        stats.row_kept_max = max(stats.row_kept_max, row_max)
        if layer_idx is not None:
            stats.per_layer_kept_ratio_sum[layer_idx] = (
                stats.per_layer_kept_ratio_sum.get(layer_idx, 0.0) + kept_ratio
            )
            stats.per_layer_calls[layer_idx] = stats.per_layer_calls.get(layer_idx, 0) + 1
            stats.per_layer_imbalance_sum[layer_idx] = (
                stats.per_layer_imbalance_sum.get(layer_idx, 0.0) + profile["load_imbalance"]
            )

    def summary(self) -> dict[str, Any]:
        return {name: stats.as_dict() for name, stats in self.methods.items()}

    def dump(self, path: str | Path) -> Path:
        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.summary(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


def _accumulate(target: list[int], addition: list[int]) -> None:
    if not target:
        target.extend(addition)
        return
    for index, value in enumerate(addition):
        target[index] += value


def _distribution_profile(kept: torch.Tensor, block_size: int, bins: int) -> dict[str, Any]:
    """The shape of the sparsity, not its average.

    Densities are normalised by each query row's own causal length: row *i* can
    only attend to *i+1* keys, so an un-normalised histogram would just re-draw
    the causal triangle instead of showing how the pruner behaves.
    """
    length = kept.shape[-1]
    device = kept.device
    positions = torch.arange(1, length + 1, device=device, dtype=torch.float32)
    causal = torch.tril(torch.ones((length, length), device=device, dtype=torch.bool))

    kept_causal = (kept & causal).to(torch.float32)
    row_kept = kept_causal.sum(dim=-1)                     # (..., rows)
    row_density = (row_kept / positions).clamp(0.0, 1.0)

    # Load imbalance is the number a systolic array feels: the busiest row
    # against the average one. 1.0 is perfectly balanced.
    flat = row_kept.reshape(-1)
    mean_kept = flat.mean()
    imbalance = float((flat.max() / mean_kept).item()) if mean_kept > 0 else 0.0

    blocks_per_row = max(1, length // block_size)
    if length % block_size == 0:
        grouped = (kept & causal).reshape(*kept.shape[:-1], blocks_per_row, block_size)
        alive = grouped.any(dim=-1).to(torch.float32)      # (..., rows, blocks)
        available = (positions / block_size).ceil().clamp(min=1.0)
        block_density = (alive.sum(dim=-1) / available).clamp(0.0, 1.0)
    else:
        block_density = row_density

    column_mass = kept_causal.sum(dim=tuple(range(kept_causal.dim() - 1)))
    total = column_mass.sum()
    if total > 0:
        ordered = torch.sort(column_mass, descending=True).values
        def head(fraction: float) -> float:
            count = max(1, int(length * fraction))
            return float((ordered[:count].sum() / total).item())
        top1, top5, top10 = head(0.01), head(0.05), head(0.10)
    else:
        top1 = top5 = top10 = 0.0

    return {
        "row_density_histogram": _histogram(row_density, bins),
        "block_density_histogram": _histogram(block_density, bins),
        "load_imbalance": imbalance,
        "column_top1_mass": top1,
        "column_top5_mass": top5,
        "column_top10_mass": top10,
    }


def _histogram(values: torch.Tensor, bins: int) -> list[int]:
    """Counts over ``bins`` equal buckets of [0, 1]."""
    flat = values.reshape(-1).clamp(0.0, 1.0)
    index = (flat * bins).floor().clamp(max=bins - 1).to(torch.int64)
    counts = torch.bincount(index, minlength=bins)
    return [int(value) for value in counts.tolist()]


def _index_entropy(kept_float: torch.Tensor) -> float:
    """Normalised entropy of the retained-column distribution.

    A value near 1.0 means retained indices are spread evenly across columns; a
    value near 0.0 means every query row keeps the same few columns.
    """
    column_mass = kept_float.sum(dim=tuple(range(kept_float.dim() - 1)))
    total = column_mass.sum()
    if total <= 0:
        return 0.0
    probabilities = column_mass / total
    nonzero = probabilities[probabilities > 0]
    entropy = float(-(nonzero * nonzero.log()).sum().item())
    columns = column_mass.numel()
    if columns <= 1:
        return 0.0
    return entropy / math.log(columns)


def _block_occupancy(kept: torch.Tensor, block_size: int) -> float:
    """Fraction of ``block_size``-wide column blocks that contain any kept value."""
    columns = kept.shape[-1]
    if columns % block_size != 0:
        return float(kept.to(torch.float32).mean().item())
    blocks = kept.reshape(*kept.shape[:-1], columns // block_size, block_size)
    return float(blocks.any(dim=-1).to(torch.float32).mean().item())


_RECORDER: SparsityRecorder | None = None


def get_recorder() -> SparsityRecorder:
    """Return the process-wide recorder, honouring ``DYNAX_SPARSITY_STATS``."""
    global _RECORDER
    if _RECORDER is None:
        enabled = os.environ.get("DYNAX_SPARSITY_STATS", "1").strip().lower() not in {"0", "false", "off"}
        _RECORDER = SparsityRecorder(enabled=enabled)
    return _RECORDER


def reset_recorder() -> SparsityRecorder:
    recorder = get_recorder()
    recorder.reset()
    return recorder


def dump_recorder(path: str | Path) -> Path:
    return get_recorder().dump(path)


# ---------------------------------------------------------------------------
# ★ FAST 新增：Q/K/V 抓取
# ---------------------------------------------------------------------------
#
# 硬件验证需要真实的注意力输入，不是合成数据。稀疏加速器省的是翻转，
# 而翻转率取决于真实 Q/K 的数值分布——用随机数驱动，功耗数字和稀疏度
# 就脱钩了。
#
# 和上面的稀疏统计一样是显式的、默认关闭的钩子：不开启时每次前向只多
# 一次 `is None` 判断。

_TENSOR_SINK = None


def set_tensor_sink(sink) -> None:
    """装一个回调，接收每层每次前向的 (layer_idx, query, key, value)。

    传 None 关闭。张量按原样传出（不复制），调用方要自己决定留哪些——
    一个 22 层的模型跑一遍会调用几十次，全留会吃光内存。
    """
    global _TENSOR_SINK
    _TENSOR_SINK = sink


def capture_qkv(layer_idx, query, key, value) -> None:
    """由 modeling 代码在算 attn_weights 之前调用。"""
    if _TENSOR_SINK is not None:
        _TENSOR_SINK(layer_idx, query, key, value)
