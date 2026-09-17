"""把 capture_row_workload.py 的输出转成 tb_block_scheduler 读的激励。

分成两步而不是让 testbench 直接读 JSON，是因为 testbench 里的 JSON 解析
是**测量代码的一部分**：解析错了不会有任何断言失败，只会让利用率变成另一个
数。文本格式一行一个 tile，肉眼能核对。

    python gen_workload_stimulus.py --workload workload_rows32.json \
        --method xm --pe 4 --out xm_32x4.txt

格式：
    第一行  numRows peCountPerRow tileCount
    之后    每行 numRows 个整数 = 某个 tile 里各行的保留列数
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--pe", type=int, required=True, help="peCountPerRow")
    parser.add_argument("--max-tiles", type=int, default=512,
                        help="截断 tile 数：Verilator 每 tile 要走十几拍，"
                             "2000 个 tile 的扫描没必要")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.workload.read_text(encoding="utf-8"))
    if args.method not in payload["methods"]:
        raise SystemExit(f"{args.workload} 里没有方法 {args.method}；"
                         f"有的是 {sorted(payload['methods'])}")
    tiles = payload["methods"][args.method]["tiles"][: args.max_tiles]
    rows = payload["tile"]["rows"]
    if any(len(t) != rows for t in tiles):
        raise SystemExit("tile 的行数不一致——工作量文件和它自己的 tile.rows 对不上")

    lines = [f"{rows} {args.pe} {len(tiles)}"]
    lines += [" ".join(str(v) for v in t) for t in tiles]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(sum(t) for t in tiles)
    print(f"{args.method}: {len(tiles)} tiles x {rows} rows, 共 {total} 个保留列 -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
