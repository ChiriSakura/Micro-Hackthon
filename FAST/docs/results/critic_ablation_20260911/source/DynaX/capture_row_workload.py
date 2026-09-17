"""★ FAST 新增，非 DynaX 上游文件。

抓出真实稀疏模式下**同一个阵列 tile 内各 query 行保留了多少列**，
供 block scheduler 的利用率测量使用。

## 为什么需要真实分布而不是合成的

`fast/agents/codesign.py` 的 `pe_utilisation()` 是这样一个公式：

    utilisation = 1 / (1 + (imbalance - 1) / (1 + queue_depth))

它的注释自己写着「这是模型不是测量」。而 `queue_depth` 是协同优化器的一个
**搜索维度**——一个没有测量支撑的维度，优化器可能在上面选错。除法器那次
已经证明过：模型缺了时钟周期这一项，44 倍的 EDP 差异完全看不见。

要测利用率，需要真实的行工作量分布。**合成的均匀分布测不出东西**：动态
稀疏的全部问题就在于不同 query 行保留的列数差别很大，一行长、邻行短，
长的那行拖住整个阵列。这个差别是模型和数据决定的，假设不出来。

## tile 的切法必须和硬件一致

不均衡度不是「整行 vs 整行」，而是**共享同一个 RePEArray 的那 height 行
之间**的差异——阵列要等最慢的那行走完才能换 tile。所以这里按
`(height 个 query 行) × (m 个 key 列)` 切块，和 RePEArray 实际吃的 tile
一一对应。切错了，测出来的利用率和硬件面对的不是同一件事。

    python capture_row_workload.py --methods xm,nm:16:64,topk:64 \
        --layer 10 --seq-len 512 --rows 32 --block 64 --out workload.json

## 复用已验证的抓取路径

spy / 模型加载 / 配置切换全部从 `plot_attention_masks.py` 引入，而不是重写。
那份代码已经踩平了三个坑，重写等于重新踩：

1. 钩子要挂在 `models.llama_modeling` 上，不是 `models.utils.sparse_attention`。
   模型是 `from ... import prune_attn_scores` 拿到的符号，改源模块没有任何效果。
2. 掩码是**加性 bias**：0 表示保留，-inf 表示剪掉。直接 `mask.sum()` 数出来的
   是完全错的东西。
3. `set_dynax_config` 是整体替换而不是打补丁，只塞 `{"sparse_method": ...}`
   会让其余每一个键都消失（而且上游的键名是 `sparse_methed`，带拼写错误）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch
from transformers import AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataUtil import get_dataset  # noqa: E402
from plot_attention_masks import capture, load_model  # noqa: E402
from run_eval_matrix import BASE_CONFIG, method_config  # noqa: E402


def tile_workloads(kept: np.ndarray, rows: int, block: int) -> list[list[int]]:
    """把一个 head 的保留掩码切成硬件 tile，数每个 tile 内各行保留几列。

    `kept` 是 [q, k] 的布尔数组，True = 该列进入 RePE 精算。

    只留下**至少有一行有活干**的 tile：全零 tile 落在因果掩码之外，硬件
    根本不会调度它，把它算进平均会把不均衡度稀释成假的好看数字。
    """
    q_len, k_len = kept.shape
    tiles: list[list[int]] = []
    for row_start in range(0, q_len, rows):
        row_slice = kept[row_start:row_start + rows]
        for col_start in range(0, k_len, block):
            tile = row_slice[:, col_start:col_start + block]
            per_row = tile.sum(axis=-1).astype(int).tolist()
            if any(per_row):
                tiles.append(per_row)
    return tiles


def global_row_imbalance(kept: np.ndarray) -> float:
    """sparsity_stats.py 用的那个定义，照抄过来做对照。

    `flat.max() / flat.mean()`，其中 flat 是**整行、全序列、跨头拍平**的
    保留数。它和 tile 内的不均衡度是两个不同的量：因果掩码下第 0 行只有
    1 个候选、最后一行有 seq_len 个，这个比值主要在反映因果斜坡；而且
    取的是全局最大值，是个极值统计，会随序列长度增长。

    `pe_utilisation()` 现在吃的就是这个数。两者差多少，是这次测量要回答的
    问题之一。
    """
    causal = np.tril(np.ones(kept.shape[-2:], dtype=bool))
    row_kept = (kept & causal).sum(axis=-1).reshape(-1).astype(np.float64)
    mean = row_kept.mean()
    return float(row_kept.max() / mean) if mean > 0 else 0.0


def tile_indices(kept: np.ndarray, rows: int, block: int, limit: int) -> list[list[list[int]]]:
    """每个 tile 里各行**保留了哪些列**（绝对列号），不只是保留了几列。

    bank 冲突取决于索引本身而不是索引的个数：`bank = col % bankCount` 下，
    聚簇的索引（xm 按块保留）和分散的索引（topk 全局取大）撞 bank 的方式
    完全不同。**只有计数就测不出这件事。**

    列号取绝对值而不是 tile 内相对值：bank 映射作用在存储地址上。
    """
    q_len, k_len = kept.shape
    tiles: list[list[list[int]]] = []
    for row_start in range(0, q_len, rows):
        row_slice = kept[row_start:row_start + rows]
        for col_start in range(0, k_len, block):
            tile = row_slice[:, col_start:col_start + block]
            per_row = [(np.flatnonzero(tile[r]) + col_start).tolist()
                       for r in range(tile.shape[0])]
            if any(per_row):
                # 行数不足 rows 的边缘 tile 补空行，保持形状一致。
                per_row += [[]] * (rows - len(per_row))
                tiles.append(per_row)
                if len(tiles) >= limit:
                    return tiles
    return tiles


def imbalance(tiles: list[list[int]]) -> float:
    """负载不均衡度 = 行数 x 锁步总周期 / 总工作量。

    ## 聚合方式：总量之比，不是逐 tile 比值的平均

    利用率 = 总工作 /（行数 x 总周期），本身就是一个**比值之和**。逐 tile 算
    max/mean 再平均，会给短 tile 和长 tile 同样的权重，而长 tile 花的周期多
    得多。两者在这份数据上差得很远（xm 32 行：1.41 vs 4.13），而 RTL 实测的
    深度 0 利用率精确落在**前者**的倒数上（0.70787 vs 0.7079）。

    这个函数早先用的是后者。留着两个聚合方式在同一个仓库里，就是在等着
    某天有人把两个不同的量当成同一个量来比。

    分母用 tile 的**全部**行（含 0 行）：一个没活干的 PE 行也占着阵列。
    """
    work = sum(sum(rows) for rows in tiles)
    cycles = sum(max(rows) if rows else 0 for rows in tiles)
    if work <= 0 or cycles <= 0:
        return 1.0
    rows_per_tile = len(tiles[0]) if tiles else 1
    return cycles * rows_per_tile / work


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T")
    parser.add_argument("--methods", default="xm,xm:32:16:64,nm:16:64,topk:64,sanger")
    parser.add_argument("--dataset", default="wiki", choices=["wiki", "ptb", "c4"])
    parser.add_argument("--layer", type=int, default=10)
    parser.add_argument("--head", type=int, default=None, help="Capture one fixed head; default all heads")
    parser.add_argument("--seq-len", type=int, default=512)
    parser.add_argument("--rows", type=int, default=32, help="RePEArray 高度（一个 tile 的 query 行数）")
    parser.add_argument("--block", type=int, default=64, help="TopK 的 m（一个 tile 的 key 列数）")
    parser.add_argument("--max-tiles", type=int, default=4096, help="每种方法最多留多少个 tile")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--emit-indices", type=int, default=0,
                        help="另外导出多少个 tile 的真实列索引（0 = 不导）。"
                             "bank 冲突要靠索引本身测，光有计数测不出来。")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    device = torch.device(
        ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    )
    torch.manual_seed(args.seed)

    tokenizer = AutoTokenizer.from_pretrained(args.model, legacy=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model, model_type, _ = load_model(args.model, torch.float32, tokenizer)
    model.to(device).eval()

    tokens = get_dataset(tokenizer, seqlen=args.seq_len, dataset=args.dataset).input_ids
    window = tokens[:, : args.seq_len]
    if window.shape[-1] != args.seq_len:
        raise ValueError("not enough input tokens for the requested task")
    print(f"[fast] window = {window.shape[-1]} tokens, tile = {args.rows}x{args.block}", flush=True)

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    results: dict[str, dict] = {}

    for method in methods:
        config = method_config(method, {"topk": min(BASE_CONFIG["topk"], args.seq_len // 8)})
        sink = capture(model, window, config, model_type, args.layer, device)
        kept_all = sink["kept"][0].numpy()  # [heads, q, k]
        heads = list(range(kept_all.shape[0])) if args.head is None else [args.head]
        if any(h < 0 or h >= kept_all.shape[0] for h in heads):
            raise ValueError("requested attention head does not exist")

        tiles: list[list[int]] = []
        for head in heads:
            tiles.extend(tile_workloads(kept_all[head], args.rows, args.block))
            if len(tiles) >= args.max_tiles:
                break
        tiles = tiles[: args.max_tiles]

        flat = [v for t in tiles for v in t]
        results[method] = {
            "config": config,
            "complete_task": args.head is not None and len(tiles) < args.max_tiles,
            "tiles": tiles,
            "tile_count": len(tiles),
            "load_imbalance": imbalance(tiles),
            # 严格锁步（queue_depth=0）下的利用率，也就是 1/imbalance。
            # RTL 实测精确落在这个值上，是 testbench 的第二条判据。
            "lockstep_utilisation": 1.0 / imbalance(tiles),
            "kept_mean": float(np.mean(flat)) if flat else 0.0,
            "kept_max": int(np.max(flat)) if flat else 0,
        }
        results[method]["global_row_imbalance"] = global_row_imbalance(kept_all)
        if args.emit_indices:
            idx: list[list[list[int]]] = []
            for head in heads:
                idx.extend(tile_indices(kept_all[head], args.rows, args.block,
                                        args.emit_indices - len(idx)))
                if len(idx) >= args.emit_indices:
                    break
            results[method]["tile_indices"] = idx
        r = results[method]
        print(f"[fast] {method:16s} tiles={r['tile_count']:5d} "
              f"imbalance={r['load_imbalance']:.3f} "
              f"kept/行 均值 {r['kept_mean']:.1f} 最大 {r['kept_max']} | "
              f"sparsity_stats 定义 {r['global_row_imbalance']:.3f}", flush=True)

    payload = {
        "source": {"model": args.model, "dataset": args.dataset, "layer": args.layer,
                   "seq_len": args.seq_len, "seed": args.seed, "head": args.head,
                   "token_sha256": hashlib.sha256(window.cpu().numpy().tobytes()).hexdigest()},
        "tile": {"rows": args.rows, "block": args.block},
        "evidence": "L2-model-capture",
        "methods": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    print(f"[fast] 写入 {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
