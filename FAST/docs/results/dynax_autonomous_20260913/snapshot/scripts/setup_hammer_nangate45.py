"""让 hammer 的 nangate45 tech plugin 真的能用。

hammer-vlsi 1.2.0 自带 `hammer.technology.nangate45`，但**它过不了 hammer
自己的 pydantic 校验**——这是上游的缺陷，不是我们的配置问题。这个脚本做两件
事，都是幂等的：修补 tech.json，以及把 PDK 摆成它期望的目录结构。

## 三处 schema 缺陷（共 21 处修补）

1. `Stackup` 对象缺 `grid_unit`（×1）。它在 tech.json 里是顶层键，而
   `hammer/tech/stackup.py` 的模型要求每个 stackup 自带一份。
2. 每个 `Metal` 对象也缺 `grid_unit`（×10），同样的原因。
3. `max_width: 1073741.8235` 不是 `grid_unit`（0.005）的整数倍（×10）。
   那个值是「无上限」的哨兵，但 `widths_must_snap_to_grid` 校验器不认哨兵。

三处都是机械且可逆的。修的是**数据**不是逻辑，所以升级 hammer 后重跑一次
即可，不需要维护一个 fork。

## 为什么要走 hammer

直接驱动 yosys + OpenSTA 已经能拿到面积、时序和功耗（见
`fast/adapters/synthesis.py` 与 `timing.py`），但那是我们自己拼的流程。
hammer 通了之后，`par`（布局布线）、`drc`、`lvs` 这些后端动作可以直接经
CHIA 的 `HammerNode` 调用，不必每一步都自己拼——而布线后的面积和功耗才是
能和论文的 mm² 与 mW 对得上的量级。

    python scripts/setup_hammer_nangate45.py --pdk-root <PDK 目录> [--check]
"""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import shutil
import sys
import urllib.request

# hammer 的 nangate45 期望的目录结构，相对 `technology.nangate45.install_dir`。
#
# tech.json 里写的是 `nangate45/lib/...`，但 installs 段把 id `nangate45`
# 映射到 install_dir——hammer **替换**这个前缀而不是拼接，所以实际路径是
# `<install_dir>/lib/...`。多一层 nangate45/ 会让它找不到文件。
#
# 只有 .lib 是综合必需的；LEF 到布局布线才用得上，GDS 到出版图才用得上。
_ORFS = ("https://raw.githubusercontent.com/The-OpenROAD-Project/"
         "OpenROAD-flow-scripts/master/flow/platforms/nangate45")
LAYOUT: tuple[tuple[str, str, bool], ...] = (
    # (相对路径, 下载地址, 综合是否必需)
    ("lib/NangateOpenCellLibrary_typical.lib",
     f"{_ORFS}/lib/NangateOpenCellLibrary_typical.lib", True),
    ("lef/NangateOpenCellLibrary.tech.lef",
     f"{_ORFS}/lef/NangateOpenCellLibrary.tech.lef", False),
    ("lef/NangateOpenCellLibrary.macro.lef",
     f"{_ORFS}/lef/NangateOpenCellLibrary.macro.lef", False),
)


def patch_tech_json(path: Path) -> dict[str, int]:
    """把三处 schema 缺陷补上。可以重复运行，第二次全为 0。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    grid_unit = data["grid_unit"]
    grid = Decimal(str(grid_unit))
    fixes = {"stackup.grid_unit": 0, "metal.grid_unit": 0, "grid-align": 0}

    for stackup in data.get("stackups", []):
        if "grid_unit" not in stackup:
            stackup["grid_unit"] = grid_unit
            fixes["stackup.grid_unit"] += 1
        for metal in stackup.get("metals", []):
            if "grid_unit" not in metal:
                metal["grid_unit"] = grid_unit
                fixes["metal.grid_unit"] += 1
            for key in ("min_width", "max_width", "pitch", "offset"):
                if key not in metal:
                    continue
                value = Decimal(str(metal[key]))
                if value % grid:
                    # 向最近的网格点取整。max_width 是「无上限」哨兵，取整
                    # 不改变语义；其余字段本来就该落在网格上。
                    metal[key] = float((value / grid).quantize(Decimal(1)) * grid)
                    fixes["grid-align"] += 1

    if sum(fixes.values()):
        path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return fixes


def stage_pdk(pdk_root: Path, source_lib: Path | None) -> list[tuple[str, str]]:
    """把 PDK 文件摆到 hammer 期望的位置，返回每个文件的状态。"""
    report = []
    for relative, url, required in LAYOUT:
        target = pdk_root / relative
        if target.is_file() and target.stat().st_size > 0:
            report.append((relative, "已存在"))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)

        # 已经下过的 .lib 直接复用，不重复下载 6.4MB。
        if source_lib and source_lib.is_file() and relative.endswith(source_lib.name):
            shutil.copy2(source_lib, target)
            report.append((relative, f"从 {source_lib} 复制"))
            continue

        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                target.write_bytes(response.read())
            report.append((relative, f"已下载 {target.stat().st_size // 1024} KB"))
        except Exception as error:  # noqa: BLE001 - 报告而不是中断
            report.append((
                relative,
                f"{'缺失（综合必需）' if required else '缺失（布局布线才用）'}："
                f"{type(error).__name__}",
            ))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdk-root", type=Path, required=True,
                        help="technology.nangate45.install_dir 指向的目录")
    parser.add_argument("--source-lib", type=Path, default=None,
                        help="已有的 .lib，避免重复下载")
    parser.add_argument("--check", action="store_true",
                        help="只验证 plugin 能否加载，不做修改")
    args = parser.parse_args()

    try:
        import hammer.technology.nangate45 as plugin
    except ImportError:
        print("hammer-vlsi 未安装：pip install hammer-vlsi", file=sys.stderr)
        return 2

    tech_json = Path(plugin.__file__).parent / "nangate45.tech.json"

    if not args.check:
        print(f"修补 {tech_json}")
        fixes = patch_tech_json(tech_json)
        total = sum(fixes.values())
        if total:
            for name, count in fixes.items():
                if count:
                    print(f"  {name:<20} {count} 处")
        else:
            print("  已是修补后的状态（幂等）")

        print(f"\n布置 PDK 到 {args.pdk_root}")
        for relative, status in stage_pdk(args.pdk_root, args.source_lib):
            print(f"  {relative:<52} {status}")

    print("\n验证 plugin 能否加载")
    try:
        from hammer.tech import HammerTechnology

        tech = HammerTechnology.load_from_module("hammer.technology.nangate45")
        print(f"  ✅ schema 通过，libraries={len(tech.config.libraries)}")
    except Exception as error:  # noqa: BLE001
        print(f"  ❌ {str(error).splitlines()[0][:160]}")
        return 1

    required = args.pdk_root / LAYOUT[0][0]
    if not required.is_file():
        print(f"  ⚠️  综合必需的 .lib 还不在 {required}")
        return 1
    print(f"  ✅ 综合必需的 .lib 就位")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
