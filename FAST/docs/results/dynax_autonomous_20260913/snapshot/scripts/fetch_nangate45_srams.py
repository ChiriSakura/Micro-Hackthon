"""把 Nangate45 的 SRAM 宏取下来，解析成面积/时序/功耗表。

## 为什么需要它

`fast/agents/templates.py` 的 `sram_area_units()` 一直是 `sram_bytes * 0.1`，
一个没有任何支撑的系数。直接综合拿不到真值：yosys 没有存储器宏编译器，
把 `SyncReadMem` 映射成 22 万个触发器（530k um^2）——那个数字反映的是综合
流程缺一环，不是设计的面积。

hammer 的 nangate45 tech plugin 自带一个 SRAM generator，但它**不是编译器
而是查表**：映射到 OpenROAD-flow-scripts 里的 `fakeram45_*` 宏。关键在于
那些宏和我们已经在用的 Nangate45 标准单元库**同一个仓库、同一个节点**，
所以面积可以直接和阵列的面积相加，不存在混节点的问题。

`flow/platforms/nangate45/` 下有 26 个宏，覆盖 32x32 到 2048x39。

## 证据等级：不是综合

`fakeram` 是**解析生成**的宏，不是硅上表征的。它是 OpenROAD 自己发布
benchmark 结果时用的东西，节点对得上，比 `0.1` 那个系数强得多——但它是
`L1-analytical-vendor-model`，不是 `L2-synthesis-nangate45`。输出里带上这个
标记，免得下游把它当成实测报出去。

    python scripts/fetch_nangate45_srams.py --out pdk/nangate45/srams.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import urllib.request

REPO = "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master"
LIB_DIR = f"{REPO}/flow/platforms/nangate45/lib"
TREE_API = ("https://api.github.com/repos/The-OpenROAD-Project/"
            "OpenROAD-flow-scripts/git/trees/master?recursive=1")

# 已知的 26 个宏。写死而不是每次问 GitHub API：这个列表是**输入数据的
# 身份**，上游加删宏时我们应该察觉到并重新标定，而不是静默地换一批数据
# 重新拟合。`--discover` 可以列出上游当前实际有哪些，用来对账。
MACROS: tuple[str, ...] = (
    "fakeram45_1024x32", "fakeram45_128x116", "fakeram45_128x256", "fakeram45_128x32",
    "fakeram45_128x64", "fakeram45_2048x39", "fakeram45_256x16", "fakeram45_256x32",
    "fakeram45_256x34", "fakeram45_256x48", "fakeram45_256x95", "fakeram45_256x96",
    "fakeram45_32x32", "fakeram45_32x64", "fakeram45_512x64", "fakeram45_64x124",
    "fakeram45_64x15", "fakeram45_64x21", "fakeram45_64x25", "fakeram45_64x256",
    "fakeram45_64x28", "fakeram45_64x32", "fakeram45_64x62", "fakeram45_64x64",
    "fakeram45_64x7", "fakeram45_64x96",
)

_AREA = re.compile(r"^\s*area\s*:\s*([\d.]+)\s*;", re.M)
_LEAKAGE = re.compile(r"^\s*cell_leakage_power\s*:\s*([\d.eE+-]+)\s*;", re.M)
# 第一个 internal_power 块里的 rise_power：读端口每次翻转的内部功耗。
_RISE_POWER = re.compile(r"rise_power\(scalar\)\s*\{\s*values\s*\(\"([\d.eE+-]+)\"\)", re.S)
# clock 端口之后的第一个 cell_rise：从时钟沿到数据有效，也就是访问时间。
_CELL_RISE = re.compile(r"cell_rise\(scalar\)\s*\{\s*values\s*\(\"([\d.eE+-]+)\"\)", re.S)


def fetch(url: str, timeout: int = 60) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def discover() -> list[str]:
    """问上游当前实际有哪些宏，用于和写死的 MACROS 对账。"""
    tree = json.loads(fetch(TREE_API, timeout=120))
    pattern = re.compile(r"platforms/nangate45/lib/(fakeram45_\d+x\d+)\.lib$")
    found = {m.group(1) for path in tree.get("tree", [])
             if (m := pattern.search(path["path"]))}
    return sorted(found)


def parse(name: str, text: str) -> dict:
    """从一个 .lib 里取出面积、访问时间、读功耗和漏电。

    取不到就留 None 而不是填 0：**「没测到」和「是 0」是两件事**，
    填 0 会让下游把一个缺失的量当成一个真实的零成本。
    """
    depth, width = (int(v) for v in re.search(r"_(\d+)x(\d+)$", name).groups())

    def first(pattern: re.Pattern[str]) -> float | None:
        match = pattern.search(text)
        return float(match.group(1)) if match else None

    area = first(_AREA)
    return {
        "name": name,
        "depth": depth,
        "width_bits": width,
        "bytes": depth * width / 8.0,
        "area_um2": area,
        "um2_per_byte": (area / (depth * width / 8.0)) if area else None,
        # ns，从时钟沿到读数据有效。它可能是系统时钟的又一个下界。
        "access_time_ns": first(_CELL_RISE),
        # 一次读端口翻转的内部功耗（.lib 的单位，Nangate45 是 pW·s = fJ 量级）
        "read_internal_power": first(_RISE_POWER),
        "leakage_power": first(_LEAKAGE),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--discover", action="store_true",
                        help="列出上游当前实际有的宏，和写死的列表对账")
    args = parser.parse_args()

    macros = list(MACROS)
    drift: dict[str, list[str]] = {}
    if args.discover:
        upstream = discover()
        drift = {
            "added_upstream": sorted(set(upstream) - set(MACROS)),
            "removed_upstream": sorted(set(MACROS) - set(upstream)),
        }
        if drift["added_upstream"] or drift["removed_upstream"]:
            print(f"[fast] 上游宏列表已变：{drift}")
        macros = upstream

    entries = []
    for name in macros:
        try:
            entries.append(parse(name, fetch(f"{LIB_DIR}/{name}.lib")))
            print(f"  {name:24s} {entries[-1]['area_um2']:>10.1f} um^2 "
                  f"{entries[-1]['um2_per_byte']:>6.2f} um^2/B", flush=True)
        except Exception as error:  # noqa: BLE001 - 单个宏取不到不该中断全表
            print(f"  {name:24s} 取失败: {error}", flush=True)

    payload = {
        "source": {
            "repo": "The-OpenROAD-Project/OpenROAD-flow-scripts",
            "path": "flow/platforms/nangate45/lib",
            "generator": "fakeram",
        },
        # 这不是综合结果。fakeram 是解析生成的宏，不是硅上表征的——它是
        # OpenROAD 自己发布 benchmark 时用的东西，节点和我们的标准单元库
        # 一致，但等级低于 yosys 实测。
        "evidence": "L1-analytical-vendor-model",
        "drift": drift,
        "macros": entries,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[fast] {len(entries)}/{len(macros)} 个宏 -> {args.out}")
    return 0 if len(entries) == len(macros) else 1


if __name__ == "__main__":
    raise SystemExit(main())
