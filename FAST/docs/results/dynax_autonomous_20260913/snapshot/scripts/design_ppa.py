"""Legacy component-area inventory for a CompilerSchedule.

This script sums separately synthesised blocks and analytical fakeram45 SRAM.
It is not an integrated accelerator PPA measurement. Its legacy target paths
must already match the plan; memory port width is fixed to data_width * 4.
OpenSTA power uses assumed activity=0.2, not a measured workload trace.

For exact candidate dimensions, independent banks, explicit activity sensitivity
and a fresh scheduler check at the target clock, use run_final_inventory.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fast.adapters.synthesis import YosysSynthesisAdapter
from fast.adapters.timing import OpenStaTimingAdapter
from fast.agents.templates import plan_sram, sram_leakage_mw


def synthesise(adapter, verilog: Path, top: str, netlist: Path | None,
               *, has_memory: bool = False):
    """综合一个模块，失败时返回 None 而不是抛异常。

    一个模块综合不出来不该让整份报告消失——报告要能说出「哪一块拿到了、
    哪一块没拿到」，那正是下一步该去查的地方。
    """
    if not verilog.is_file():
        return None, f"{verilog.name} not found"
    try:
        result = adapter.synthesize(verilog, top, netlist, has_memory=has_memory)
    except Exception as error:  # noqa: BLE001
        return None, f"{type(error).__name__}: {error}"
    if not result.success or result.cell_area_um2 is None:
        return None, result.error or "yosys produced no area"
    return result, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True,
                        help="CompilerSchedule 的 JSON（scripts/plan_to_json.py 的输出）")
    parser.add_argument("--rtl-dir", type=Path, required=True,
                        help="elaborate 的输出根目录")
    parser.add_argument("--container", type=Path, required=True)
    parser.add_argument("--liberty", type=Path, required=True)
    parser.add_argument("--sta-container", type=Path, default=None)
    parser.add_argument("--period-ns", type=float, default=2.5)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    args.work.mkdir(parents=True, exist_ok=True)

    syn = YosysSynthesisAdapter(
        container=args.container, liberty=args.liberty, work_root=args.work / "syn"
    )
    sta = (
        OpenStaTimingAdapter(container=args.sta_container, liberty=args.liberty,
                             work_root=args.work / "sta")
        if args.sta_container else None
    )

    # 逻辑：三块分开报。合成一个数会掩盖「哪一块没拿到」。
    # 第四个字段：这一块带不带 SyncReadMem。
    #
    # 带存储的模块要把 `$mem` 留成黑盒——yosys 会把它展开成触发器
    # （DynaX 的 SRAM 因此报 226,703 个触发器、530,247 um^2），那个数不是
    # 设计的面积。存储面积由 fakeram45 宏算，这里只量**取数逻辑**。
    blocks = [
        ("AttentionTile", args.rtl_dir / "Plan" / "AttentionTile.v", "AttentionTile", False),
        ("KeyFeeder", args.rtl_dir / "KeyFeeder" / "KeyFeeder.v", "KeyFeeder", True),
        ("BlockScheduler", args.rtl_dir / "BlockScheduler" / "BlockScheduler.v",
         "BlockScheduler", False),
    ]
    logic: dict[str, dict] = {}
    for name, verilog, top, has_memory in blocks:
        netlist = args.work / f"{name}.mapped.v"
        result, error = synthesise(syn, verilog, top, netlist, has_memory=has_memory)
        entry: dict[str, object] = {"error": error}
        if result is not None:
            entry = {
                "area_um2": result.cell_area_um2, "cells": result.cell_count,
                # 带存储的块报的是**逻辑**面积——存储被留成黑盒。不标出来
                # 的话，这个数会被当成整块的面积。
                "scope": "logic only (memory left as a black box)" if has_memory else "full",
            }
            # 带存储的块跑不了 STA：网表里的 `$mem_v2` 是黑盒，OpenSTA 读到
            # 那一行直接语法错。这是把存储留成黑盒的**已知代价**——不是
            # 「这块跑 0 赫兹」。说清楚，不要给一个看起来像测量的空值。
            if has_memory:
                entry["timing_skipped"] = (
                    "OpenSTA cannot parse the black-boxed $mem_v2 cell; "
                    "run this block with memory mapped if you need its timing"
                )
            elif sta is not None and netlist.is_file():
                timing = sta.analyse(netlist, top, period_ns=args.period_ns, label=name)
                # 时序可信性守卫已经在适配器里：单级延迟离谱的结果是扇出
                # 伪影，报出来会让人以为设计慢了两个数量级。
                entry["critical_path_ns"] = timing.critical_path_ns
                entry["max_frequency_mhz"] = (
                    1000.0 / timing.critical_path_ns if timing.critical_path_ns else None
                )
                entry["timing_trusted"] = timing.timing_credible
                entry["worst_stage"] = (
                    f"{timing.worst_stage_cell} {timing.worst_stage_ns} ns"
                    if not timing.timing_credible else ""
                )
                entry["power_mw"] = (
                    timing.total_power_w * 1000.0 if timing.total_power_w else None
                )
        logic[name] = entry

    # 存储：查真实宏，不综合。
    sram_plan = plan_sram(plan["sram_bytes"], port_width_bits=plan["data_width"] * 4)
    memory = {
        "bytes": plan["sram_bytes"],
        "macro": list(sram_plan.macro) if sram_plan else None,
        "count": sram_plan.count if sram_plan else 0,
        "area_um2": sram_plan.area_um2 if sram_plan else 0.0,
        "leakage_mw": sram_leakage_mw(plan["sram_bytes"]),
        "read_energy_pj": sram_plan.read_energy_pj if sram_plan else 0.0,
        "access_ns": sram_plan.access_ns if sram_plan else None,
    }

    logic_area = sum(
        float(item.get("area_um2", 0.0) or 0.0) for item in logic.values()
    )
    missing = [name for name, item in logic.items() if item.get("error")]

    payload = {
        "plan": plan,
        # 布局前。布线后面积通常会涨（利用率不可能 100%），时序也会变。
        # 这一句必须跟着数字走，否则它会被当成流片前的最终数。
        "stage": "pre-layout",
        "evidence": "L2-synthesis-nangate45 (logic) + L1-analytical-vendor-model (SRAM macros)",
        "logic": logic,
        "memory": memory,
        "totals": {
            "logic_area_um2": logic_area,
            "memory_area_um2": memory["area_um2"],
            "area_um2": logic_area + memory["area_um2"],
            # 逻辑综合不出来的块不计入总面积，但要点名——一个「总面积」
            # 悄悄少了一块，比没有总面积更糟。
            "incomplete": missing,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"{'块':<16s} {'面积 um^2':>12s} {'MHz':>6s}  备注")
    for name, item in logic.items():
        if item.get("error"):
            print(f"{name:<16s} {'-':>12s} {'-':>6s}  {item['error'][:50]}")
        else:
            mhz = item.get("max_frequency_mhz")
            trusted = item.get("timing_trusted", True)
            # 没测到就打 "-"，不打 0——0 看起来像一个测量结果。
            shown = f"{mhz:>6.0f}{'' if trusted else '*'}" if mhz else f"{'-':>6s}"
            note = item.get("cells", 0)
            suffix = f"{note:,} cells"
            if item.get("scope", "full") != "full":
                suffix += "（仅逻辑）"
            if item.get("timing_skipped"):
                suffix += "，时序未测"
            print(f"{name:<16s} {item['area_um2']:>12,.0f} {shown}  {suffix}")
    print(f"{'SRAM 宏':<16s} {memory['area_um2']:>12,.0f} {'-':>6s}  "
          f"{memory['count']} x {memory['macro']}, 漏电 {memory['leakage_mw']:.1f} mW")
    print(f"{'合计':<16s} {payload['totals']['area_um2']:>12,.0f}")
    if missing:
        print(f"⚠ 未计入：{', '.join(missing)}——总面积偏小")
    print("* = 时序不可信（扇出伪影）；stage=pre-layout，布线后会变")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
