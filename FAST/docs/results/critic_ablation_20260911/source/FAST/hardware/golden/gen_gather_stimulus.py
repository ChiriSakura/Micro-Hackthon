"""把真实的稀疏列索引转成 tb_key_feeder 的取数请求流。

## 分组方式反映硬件的实际请求

阵列每拍要 `regWidth` 个新 K 标量（`repe_row.scala:62` 每拍无条件更新
`reg_cols`）。所以请求是**按 regWidth 分组**发出的，一组齐了阵列才能走一拍。

分组按**行内顺序**而不是把整个 tile 打平重排：调度器是一行一行发的
（`index_scheduler.scala` 的 gather_col 按行组织），跨行重排会人为地把
不同行的索引混在一起，那正好会掩盖或制造 bank 冲突——测出来的就不是
真实调度下的冲突率。

不足 regWidth 的尾组用 -1 补，表示该槽不取。

    python gen_gather_stimulus.py --workload workload_rows32.json \
        --method xm --reg-width 8 --banks 8 --out xm_b8.txt

格式：
    第一行  regWidth bankCount totalCols groupCount
    之后    每行 regWidth 个列索引（-1 = 该槽不用）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--reg-width", type=int, required=True)
    parser.add_argument("--banks", type=int, required=True)
    parser.add_argument("--total-cols", type=int, default=2048,
                        help="存储的总列数；必须和 RTL 的 bankCount*bankDepth 一致")
    parser.add_argument("--max-groups", type=int, default=4096)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.workload.read_text(encoding="utf-8"))
    method = payload["methods"].get(args.method)
    if method is None:
        raise SystemExit(f"{args.workload} 里没有方法 {args.method}；"
                         f"有的是 {sorted(payload['methods'])}")
    tiles = method.get("tile_indices")
    if not tiles:
        raise SystemExit(
            f"{args.workload} 没有 tile_indices。bank 冲突要靠索引本身测，"
            f"光有保留计数测不出来——重跑抓取时加 --emit-indices。")

    groups: list[list[int]] = []
    clipped = 0
    for tile in tiles:
        for row in tile:
            cols = [c for c in row if c < args.total_cols]
            clipped += len(row) - len(cols)
            for start in range(0, len(cols), args.reg_width):
                chunk = cols[start:start + args.reg_width]
                groups.append(chunk + [-1] * (args.reg_width - len(chunk)))
                if len(groups) >= args.max_groups:
                    break
            if len(groups) >= args.max_groups:
                break
        if len(groups) >= args.max_groups:
            break

    if not groups:
        raise SystemExit("没有产生任何请求组")
    if clipped:
        # 说出来而不是默默丢：丢掉的正是分布尾部的索引，而尾部恰好是冲突
        # 行为最不一样的地方。
        print(f"[fast] 警告：{clipped} 个列索引 >= total_cols={args.total_cols}，已丢弃")

    lines = [f"{args.reg_width} {args.banks} {args.total_cols} {len(groups)}"]
    lines += [" ".join(str(c) for c in g) for g in groups]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 解析侧先算一遍冲突，给 RTL 的结果当对照。两者对不上，说明 RTL 的
    # 仲裁和「每个 bank 每拍服务一个请求」这个模型不是一回事。
    total_serial = 0
    for g in groups:
        per_bank: dict[int, int] = {}
        for c in g:
            if c < 0:
                continue
            b = c % args.banks
            per_bank[b] = per_bank.get(b, 0) + 1
        total_serial += max(per_bank.values()) if per_bank else 0
    print(f"[fast] {args.method} banks={args.banks} regWidth={args.reg_width}: "
          f"{len(groups)} 组，解析预测每组 {total_serial / len(groups):.3f} 拍串行 "
          f"(下界 1.0) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
