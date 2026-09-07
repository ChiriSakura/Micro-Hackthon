"""★ FAST 新增，非 DynaX 上游文件。

从真实模型的一次前向传播里抓出一个 attention tile 的 Q/K/V，量化到加速器
的定点格式，并算出 PyTorch 的参照输出。

这是回答「模型的一部分注意力能不能在这个加速器上跑」的输入端。判据不是
「RTL 自洽」——那只能证明 RTL 等于它自己——而是**同一组真实 Q/K/V 下，
硬件的输出和 PyTorch 的注意力对不对得上**。

    python capture_attention_tile.py --model TinyLlama/... --layer 10 --head 0 \
        --tile-q 4 --tile-k 32 --head-dim 8 --kept 8 --out tile.json

输出的 JSON 同时包含：

  * 定点化的 Q/K/V（精确通路用 Q8.8，预测通路用 4-bit）
  * PyTorch 在**同一批定点值**上算出的稠密注意力输出
  * PyTorch 在 top-n 稀疏化之后的输出——这才是硬件应该复现的那个

第二个参照是关键：加速器做的是稀疏注意力，它不该复现稠密结果。把稠密
当参照会得出「硬件错了」的错误结论，而真正的问题是参照选错了。
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch


def quantise(values: torch.Tensor, bits: int, point: int) -> torch.Tensor:
    """落到加速器的定点网格上，这样比较是精确的而不是「接近」。"""
    scale = float(1 << point)
    limit = float(1 << (bits - 1))
    return torch.round(values * scale).clamp(-limit, limit - 1) / scale


def quantise_predict(values: torch.Tensor, bits: int) -> torch.Tensor:
    """预测通路的低位宽**有符号**量化。

    和 DynaX 自己的软件一致：quant_utils.py 的
    calc_max_quant_value(bits) = 2^(bits-1) - 1，4-bit 即 ±7，按全张量的
    最大幅值定标（get_dynamic_scale）。

    这里曾经是无符号的，因为上游 RTL 的端口是 UInt(4.W)。那条通路现已改为
    有符号（见 prepe_1_2.scala 的 ★ 注释）——丢符号会把和 query 反相关的
    key 抬到最前面，实测让 top-8 选择质量从 75% 掉到 31%。
    """
    peak = values.abs().max()
    if peak <= 0:
        return torch.zeros_like(values)
    limit = (1 << (bits - 1)) - 1
    return torch.round(values / peak * limit).clamp(-limit, limit)


def sparse_attention_reference(
    query: torch.Tensor, key: torch.Tensor, value: torch.Tensor, kept: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """PyTorch 的 top-n 稀疏注意力：加速器应该复现的就是这个。

    Returns:
        (输出, 每行保留的列下标)
    """
    scores = query @ key.transpose(-2, -1)
    keep = min(kept, scores.shape[-1])
    top = torch.topk(scores, keep, dim=-1)

    masked = torch.full_like(scores, float("-inf"))
    masked.scatter_(-1, top.indices, top.values)
    weights = torch.softmax(masked, dim=-1)
    return weights @ value, top.indices


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T")
    parser.add_argument("--layer", type=int, default=10)
    parser.add_argument("--head", type=int, default=0)
    parser.add_argument("--seq-len", type=int, default=128)
    parser.add_argument("--tile-q", type=int, default=4)
    parser.add_argument("--tile-k", type=int, default=32)
    parser.add_argument("--head-dim", type=int, default=8,
                        help="截取的头维度；PrePEA 的 width")
    parser.add_argument("--kept", type=int, default=8, help="每行保留几列")
    parser.add_argument("--bits", type=int, default=16)
    parser.add_argument("--point", type=int, default=8)
    parser.add_argument("--predict-bits", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260906)
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    from models.utils.sparsity_stats import set_tensor_sink

    captured: dict[str, torch.Tensor] = {}

    def sink(layer_idx, query, key, value):
        # 只留目标层的第一次调用；一个 22 层的模型跑一遍会调几十次。
        if layer_idx == args.layer and "query" not in captured:
            captured["query"] = query.detach().float().cpu()
            captured["key"] = key.detach().float().cpu()
            captured["value"] = value.detach().float().cpu()

    print(f"加载 {args.model} ...")
    from transformers import AutoTokenizer

    from models.llama_modeling import LlamaForCausalLM

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    # 必须强制 eager：默认是 sdpa（llama_modeling.py:771 的注释写着
    # "defalut: sdpa"），而 sdpa 分支把 QK^T 和 softmax 一起丢给
    # torch.nn.functional.scaled_dot_product_attention，中间张量根本不落地——
    # 抓取钩子和 DynaX 自己的稀疏化都在 eager 分支里，sdpa 下两者都不生效。
    model = LlamaForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.float32, attn_implementation="eager"
    )
    model.eval()

    text = ("Static timing analysis reports the critical path of a circuit. "
            "The divider dominates the softmax normaliser. ") * 32
    ids = tokenizer(text, return_tensors="pt").input_ids[:, : args.seq_len]

    set_tensor_sink(sink)
    try:
        with torch.no_grad():
            model(ids)
    finally:
        set_tensor_sink(None)

    if "query" not in captured:
        print(f"第 {args.layer} 层没有被调用到", flush=True)
        return 1

    # [batch, heads, seq, head_dim] -> 取一个头的一个 tile
    head = args.head
    q_full = captured["query"][0, head]
    k_full = captured["key"][0, head]
    v_full = captured["value"][0, head]
    print(f"抓到第 {args.layer} 层第 {head} 头：Q{tuple(q_full.shape)} "
          f"K{tuple(k_full.shape)} V{tuple(v_full.shape)}")

    # 取 tile：query 取最后 tile_q 行（它们能看到最多的 key），
    # key/value 取前 tile_k 行，头维度截前 head_dim 列。
    #
    # **把 1/sqrt(d) 折进 Q**。注意力算的是 QK^T/sqrt(d)，而硬件只算 q·k——
    # 缩放必须在别处完成，折进 Q 是真实加速器的做法（省一个除法器）。
    #
    # 这一步不是可选的。漏掉它，分数会大 sqrt(d) 倍：实测下最大分数从 2.12
    # 变成 6.00，越过 exp 在 Q8.8 的饱和阈值 ln(128)=4.85，4 个 query 位置
    # 里 2 个的 exp 饱和、1 个的 exp 求和溢出成负数。那看起来像硬件缺陷，
    # 其实是输入没按注意力的定义缩放。
    query = q_full[-args.tile_q:, : args.head_dim] / math.sqrt(args.head_dim)
    key = k_full[: args.tile_k, : args.head_dim]
    value = v_full[: args.tile_k, : args.head_dim]

    # 精确通路：Q8.8。参照必须算在**量化后**的值上，否则差异里混进了
    # 量化误差，分不清是硬件错了还是精度不够。
    q_fixed = quantise(query, args.bits, args.point)
    k_fixed = quantise(key, args.bits, args.point)
    v_fixed = quantise(value, args.bits, args.point)

    dense = (torch.softmax(q_fixed @ k_fixed.transpose(-2, -1), dim=-1)) @ v_fixed
    sparse, kept_idx = sparse_attention_reference(q_fixed, k_fixed, v_fixed, args.kept)

    # 预测通路：无符号低位宽。它只决定「挑哪些列」，不进最终结果。
    q_predict = quantise_predict(query, args.predict_bits)
    k_predict = quantise_predict(key, args.predict_bits)

    scale = 1 << args.point
    payload = {
        "module": "AttentionTile",
        "source": {
            "model": args.model, "layer": args.layer, "head": head,
            "seq_len": args.seq_len, "tokens": int(ids.shape[1]),
        },
        "params": {
            "tile_q": args.tile_q, "tile_k": args.tile_k,
            "head_dim": args.head_dim, "kept": args.kept,
            "bits": args.bits, "point": args.point,
            "predict_bits": args.predict_bits,
        },
        "reference": "PyTorch top-n 稀疏注意力，算在量化后的 Q/K/V 上",
        # 精确通路的定点值（tick）
        "q_ticks": [[int(round(float(x) * scale)) for x in row] for row in q_fixed],
        "k_ticks": [[int(round(float(x) * scale)) for x in row] for row in k_fixed],
        "v_ticks": [[int(round(float(x) * scale)) for x in row] for row in v_fixed],
        # 预测通路的有符号低位宽值
        "q_predict": [[int(x) for x in row] for row in q_predict],
        "k_predict": [[int(x) for x in row] for row in k_predict],
        # 参照：稀疏的那个才是硬件该复现的
        "expected_sparse": [[int(round(float(x) * scale)) for x in row] for row in sparse],
        "expected_dense": [[int(round(float(x) * scale)) for x in row] for row in dense],
        "expected_kept_idx": [[int(i) for i in row] for row in kept_idx],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    drift = (sparse - dense).abs().mean().item()
    print(f"写入 {args.out}")
    print(f"  tile: Q[{args.tile_q}x{args.head_dim}] K/V[{args.tile_k}x{args.head_dim}] "
          f"每行保留 {args.kept}/{args.tile_k}")
    peak_score = (q_fixed @ k_fixed.transpose(-2, -1)).max().item()
    print(f"  稀疏 vs 稠密的平均偏差 {drift:.5f}"
          f"（这是算法的代价，不是硬件的误差）")
    print(f"  最大分数 {peak_score:.2f}（exp 在 Q8.8 的饱和阈值是 "
          f"{math.log(1 << (args.bits - 1 - args.point)):.2f}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
