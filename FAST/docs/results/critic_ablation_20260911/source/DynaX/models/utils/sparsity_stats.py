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
    # 每个阵列高度一条：tile 内不均衡度是随高度变的。
    tile_imbalance_sum: dict[str, float] = field(default_factory=dict)
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
            # 阵列真正感受到的那个：{阵列高度: tile 内 max/mean 的均值}。
            # pe_utilisation() 消费的是这个，不是上面那个全局量。
            "mean_tile_load_imbalance": {
                rows: total / self.calls for rows, total in sorted(self.tile_imbalance_sum.items())
            },
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
        block_size: int | None = None,
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
            measured_block = self.block_size if block_size is None else block_size
            occupancy = _block_occupancy(kept, measured_block)
            profile = _distribution_profile(kept, measured_block, stats.bins)

        stats.calls += 1
        _accumulate(stats.row_density_histogram, profile["row_density_histogram"])
        _accumulate(stats.block_density_histogram, profile["block_density_histogram"])
        stats.load_imbalance_sum += profile["load_imbalance"]
        for rows, value in profile["tile_load_imbalance"].items():
            stats.tile_imbalance_sum[rows] = stats.tile_imbalance_sum.get(rows, 0.0) + value
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



# 阵列高度候选。论文的两个配置是 DynaX-S 32 行、DynaX-L 64 行；不均衡度随
# tile 高度上升（32 行 4.13 -> 64 行 6.16），所以不能只记一个。
TILE_ROW_HEIGHTS: tuple[int, ...] = (4, 8, 16, 32, 64)


def _tile_imbalance(kept_causal: torch.Tensor, rows: int, block_size: int) -> float:
    """阵列真正感受到的负载不均衡：一个 tile 内 max_row / mean_row 的平均。

    tile = (rows 个 query 行) x (block_size 个 key 列)，和 RePEArray 实际吃的
    形状一一对应。切错了，算出来的利用率和硬件面对的不是同一件事。

    全零 tile 跳过：那落在因果掩码之外，硬件根本不会调度它。把它算进平均
    会把不均衡度稀释成一个假的好看数字。

    均值的分母用 tile 的**全部** rows 行（含空行）——一个没活干的 PE 行也
    占着阵列，它对利用率的拖累是真实的。

    ## 聚合方式：总量之比，不是逐 tile 比值的平均

    利用率 = 总工作 / (行数 x 总周期)，本身就是一个**比值之和**。逐 tile
    算 max/mean 再平均，会给短 tile 和长 tile 同样的权重，而长 tile 花的
    周期多得多。实测数据上两者差 6 个百分点（xm 32 行：0.708 vs 0.666），
    足以让标定偏到错误的那一侧。

    ## 和硬件数字的已知差别

    这里按**保留列数**算，硬件按**趟数** `ceil(kept / peCountPerRow)` 算。
    向上取整会把不均衡度略微放大（一个只保留 1 列的行也要占满一趟）。
    所以这个数是 pe=1 的极限，是个偏乐观的下界；RTL 实测的那条曲线才是
    某个具体 pe 下的真值。
    """
    plane = kept_causal.reshape(-1, *kept_causal.shape[-2:]).to(torch.float32)
    q_len, k_len = plane.shape[-2], plane.shape[-1]
    work_total, cycle_total = 0.0, 0.0
    for row_start in range(0, q_len, rows):
        rows_here = plane[:, row_start:row_start + rows, :]
        pad = rows - rows_here.shape[1]
        if pad > 0:
            rows_here = torch.nn.functional.pad(rows_here, (0, 0, 0, pad))
        for col_start in range(0, k_len, block_size):
            tile = rows_here[:, :, col_start:col_start + block_size]
            per_row = tile.sum(dim=-1)                 # (planes, rows)
            work_total += float(per_row.sum().item())
            # 锁步下一个 tile 花 max_row 拍；全零 tile 的 max 是 0，自然不计。
            cycle_total += float(per_row.max(dim=-1).values.sum().item())
    if work_total <= 0 or cycle_total <= 0:
        return 1.0
    return (cycle_total * rows) / work_total


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

    # ★ FAST 注记：下面这个 `load_imbalance` **不是**脉动阵列感受到的那个量。
    #
    # 它取的是整行、全序列、跨头拍平后的 max/mean。因果掩码下第 0 行只有
    # 1 个候选、最后一行有 seq_len 个，所以这个比值主要在反映因果斜坡；
    # 而且是全局极值统计，会随序列长度增长。
    #
    # 阵列真正感受到的是**共享同一个 tile 的那 numRows 行之间**的差异：
    # 所有行共用一个 K 列寄存器窗口，窗口推进到下一个 tile 之前，先算完的
    # 行只能空转。tile 之外的行长差异，阵列碰不到。
    #
    # 实测这两个量连**排序**都不一样（TinyLlama L10, wiki, seq=512, 32 行 tile，
    # 两边都用总量之比聚合）：
    #
    #     方法          tile 内   这个全局量
    #     sanger         1.95       4.92
    #     topk:64        1.68       1.07   ← 实际最差之一，却被报成几乎完美
    #     xm             1.46       3.26
    #     nm:16:64       1.00       1.83   ← N:M 按构造完美均衡，却被报成不均衡
    #
    # 全局量把 nm 排在 topk 之前，实际正好相反；量级也放大了 2-3 倍。
    #
    # 保留原字段是为了和早先的运行结果可比；`tile_load_imbalance` 才是
    # `pe_utilisation()` 应该消费的那个。
    flat = row_kept.reshape(-1)
    mean_kept = flat.mean()
    imbalance = float((flat.max() / mean_kept).item()) if mean_kept > 0 else 0.0

    tile_imbalance = {
        str(rows): _tile_imbalance(kept & causal, rows, block_size)
        for rows in TILE_ROW_HEIGHTS
    }

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
        "tile_load_imbalance": tile_imbalance,
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
