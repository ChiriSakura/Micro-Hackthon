"""综合已验证的模块，并把结果和一阶面积模型对照。

这个脚本的产出不是「面积是多少」，而是**一阶模型错得有多离谱**。
`fast/agents/codesign.py` 的面积公式（乘法器按 bits² 缩放之类）从来没有被
任何工具校准过；协同优化器却在用它排序。一个把面积算错 3 倍的公式，在
Pareto 前沿上和正确公式看起来一模一样——除非拿真实综合去比。

    python scripts/synthesize_modules.py --rtl <elaborate 输出目录> --out report.json

工艺是 Nangate45（开源 45nm），不是论文的 28nm 商业工艺。绝对值不能和论文的
1.08 / 6.05 mm² 比；能比的是设计之间的相对关系，而那正是协同优化器需要的。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from fast.adapters.synthesis import YosysSynthesisAdapter
from fast.adapters.timing import OpenStaTimingAdapter, activity_from_stimulus
from fast.agents.templates import TemplateRegistry, topk_area_units, array_area_units

# elaborate 目标 -> (顶层模块名, 对应的模板 id)。
# 顺序按预期规模从小到大，这样大模块超时也已经拿到了小模块的数字。
MODULES: tuple[tuple[str, str, str | None], ...] = (
    ("ExpUnit", "ExpUnitFixPoint", "exp_unit"),
    ("FixedPointDiv", "FixedPointDiv", None),
    # 流水化除法器的取舍曲线。上游的组合除法是整个系统的瓶颈
    # （14.83 ns / 67 MHz，而执行阵列能跑 450 MHz），这几个点用来量出
    # 「多花多少面积换多少频率」，让协同优化器能在上面选。
    ("DivPipe1", "FixedPointDivPipelined", None),
    ("DivPipe4", "FixedPointDivPipelined", None),
    ("DivPipe8", "FixedPointDivPipelined", None),
    ("DivPipe12", "FixedPointDivPipelined", None),
    ("DivPipe24", "FixedPointDivPipelined", None),
    # 工作队列的面积曲线。pe_utilisation() 对 queue_depth 单调递增，而
    # area_units() 完全不收它的面积——只有收益没有成本，优化器必然选最深
    # 的那个。这几个点是那笔交易的成本侧。
    ("BlockSched_S0", "BlockScheduler", None),
    ("BlockSched_S2", "BlockScheduler", None),
    ("BlockSched_S4", "BlockScheduler", None),
    ("BlockSched_S8", "BlockScheduler", None),
    ("BlockSched_S16", "BlockScheduler", None),
    ("BlockSched_L0", "BlockScheduler", None),
    ("BlockSched_L8", "BlockScheduler", None),
    ("BlockSched_L16", "BlockScheduler", None),
    # 按稀疏索引取 K 列的引擎。bank 数越多冲突越少，但 regWidth x bankCount
    # 的选择网络不是免费的——这几个点量出那笔交易的成本侧。
    ("KeyFeeder_S4", "KeyFeeder", None),
    ("KeyFeeder_S8", "KeyFeeder", None),
    ("KeyFeeder_S16", "KeyFeeder", None),
    ("KeyFeeder_S32", "KeyFeeder", None),
    ("KeyFeeder_SH8", "KeyFeeder", None),
    ("KeyFeeder_SH16", "KeyFeeder", None),
    ("PSumSoftmax", "PSumSoftmax", "psum_softmax"),
    ("SRAMBank", "SRAMBank", None),
    ("SRAM", "SRAM", "sram"),
    ("PrePE_1_2", "PrePE_1_2", "prepe"),
    ("PrePE_1_4", "PrePE_1_4", None),
    ("RePE", "RePE", "repe"),
    ("TopK_S", "TopK", None),
    ("TopK", "TopK", "topk"),
    ("RePERow", "RePERow", None),
    ("RePEArray_S", "RePEArray", "repe_array"),
    ("PrePEArray_S", "PrePEArray_1_2", "prepe_array"),
    ("RePEArray_L", "RePEArray", None),
    ("PrePEArray_L", "PrePEArray_1_4", None),
)

# 一阶模型对同一批模块的预测，用于对照。只覆盖模型真的有公式的那几个；
# 其余留空——「模型没有说法」和「模型说错了」是两件事。
def _model_area_units(target: str) -> float | None:
    if target == "TopK":
        return topk_area_units(m=64, n=16, bits=16)
    if target == "TopK_S":
        return topk_area_units(m=32, n=8, bits=16)
    if target == "RePEArray_S":
        return array_area_units(num_rows=32, pe_per_row=4, bits=16, reg_width=8)
    if target == "RePEArray_L":
        return array_area_units(num_rows=64, pe_per_row=8, bits=16, reg_width=16)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtl", type=Path, required=True,
                        help="Elaborate 的输出目录（每个目标一个子目录）")
    parser.add_argument("--container", type=Path, required=True)
    parser.add_argument("--liberty", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument("--only", nargs="*", default=None,
                        help="只综合这些 elaborate 目标")
    parser.add_argument("--sta-container", type=Path, default=None,
                        help="OpenSTA 镜像；给了就一并跑时序与功耗")
    parser.add_argument("--period-ns", type=float, default=2.0,
                        help="STA 的时钟周期；论文是 500 MHz 即 2ns")
    parser.add_argument("--golden-dir", type=Path, default=None,
                        help="金标准目录，用于从实际激励数出翻转率 alpha")
    args = parser.parse_args()

    # 网表要写进 log_dir，所以它必须在第一个模块跑之前就存在——否则
    # yosys 的 write_verilog 会 "Can't open output file ... No such file"，
    # 而且只有第一个模块会中招，看起来像是那个模块的问题。
    if args.log_dir:
        args.log_dir.mkdir(parents=True, exist_ok=True)

    adapter = YosysSynthesisAdapter(
        container=args.container, liberty=args.liberty, work_root=args.log_dir
    )
    timing = None
    if args.sta_container:
        timing = OpenStaTimingAdapter(
            container=args.sta_container, liberty=args.liberty,
            work_root=args.log_dir,
        )
    registry = TemplateRegistry()

    selected = [m for m in MODULES if args.only is None or m[0] in args.only]
    rows = []
    print(f"{'目标':<16}{'单元数':>9}{'面积 um^2':>12}{'耗时':>8}  {'来源':<20}证据")
    print("-" * 92)

    for target, top_module, template_id in selected:
        verilog = args.rtl / target / f"{top_module}.v"
        netlist = (args.log_dir / f"{target}.mapped.v") if args.log_dir else None
        result = adapter.synthesize(verilog, top_module, netlist_out=netlist)

        template = registry.by_id(template_id) if template_id else None
        provenance = template.provenance if template else "-"
        # 一个模块「验过没有」和「面积多少」是两件独立的事，但报告里必须
        # 并排出现：没有仿真证据的模块，它的面积数字也不该被当作结论。
        evidence = (
            "verified" if template and template.verified
            else ("unverified" if template else "无对应模板")
        )

        if result.success:
            print(f"{target:<16}{result.cell_count:>9}{result.cell_area_um2:>12.1f}"
                  f"{result.wall_seconds:>7.0f}s  {provenance:<20}{evidence}")
        else:
            print(f"{target:<16}{'FAILED':>9}{'-':>12}{result.wall_seconds:>7.0f}s  "
                  f"{provenance:<20}{result.error[:40] if result.error else ''}")

        # 时序与功耗跑在同一份映射网表上。alpha 从实际施加的激励里数出来，
        # 而不是取工具默认值——动态功耗严格正比于它，默认值等于给出一个和
        # 稀疏度无关的任意数。
        timing_row: dict = {}
        if timing and result.success and netlist and netlist.is_file():
            alpha = _activity_for(args.golden_dir, target)
            measured = timing.analyse(
                netlist, top_module, period_ns=args.period_ns, activity=alpha,
                # 用 elaborate 目标而不是顶层模块名：RePEArray_S 和 _L 的
                # 顶层同名，日志会互相覆盖。
                label=target,
            )
            timing_row = {
                "critical_path_ns": measured.critical_path_ns,
                "slack_ns": measured.slack_ns,
                "max_frequency_mhz": measured.max_frequency_mhz,
                "activity": measured.activity,
                "activity_source": (
                    "golden vectors" if args.golden_dir else "default"
                ),
                "total_power_w": measured.total_power_w,
                "leakage_power_w": measured.leakage_power_w,
                "timing_error": measured.error,
            }
            timing_row["timing_credible"] = measured.timing_credible
            timing_row["worst_stage_ns"] = measured.worst_stage_ns
            timing_row["worst_stage_cell"] = measured.worst_stage_cell
            power_mw = (measured.total_power_w or 0) * 1e3
            if measured.success and measured.timing_credible:
                print(f"{'':16}{'':9}{'':12}{'':8}  时序 {measured.critical_path_ns:.3f}ns "
                      f"({measured.max_frequency_mhz:.0f} MHz, slack "
                      f"{measured.slack_ns:+.3f}ns)  功耗 {power_mw:.3f} mW @ a={alpha:.3f}")
            elif measured.success:
                # 面积和功耗仍然可用，只有时序被扇出主导。
                print(f"{'':16}{'':9}{'':12}{'':8}  时序不可信"
                      f"（{measured.worst_stage_cell} 单级 "
                      f"{measured.worst_stage_ns:.1f}ns，未插缓冲）"
                      f"  功耗 {power_mw:.3f} mW @ a={alpha:.3f}")
            else:
                print(f"{'':16}  STA 失败：{(measured.error or '')[:60]}")

        rows.append({
            "target": target,
            "top_module": top_module,
            "template_id": template_id,
            "provenance": provenance,
            "verified": bool(template and template.verified),
            "success": result.success,
            "cell_count": result.cell_count,
            "cell_area_um2": result.cell_area_um2,
            "model_area_units": _model_area_units(target),
            "wall_seconds": round(result.wall_seconds, 1),
            "error": result.error,
            "cell_histogram": result.cell_histogram,
            **timing_row,
        })

    _report_model_gap(rows)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "technology": adapter.technology,
            "liberty": str(args.liberty),
            "note": (
                "Nangate45 开源 45nm，不是 DynaX 论文的 28nm 商业工艺。"
                "绝对面积不可与论文的 1.08 / 6.05 mm^2 比较；"
                "设计之间的相对面积可以。"
            ),
            "modules": rows,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\n写入 {args.out}")

    return 0 if all(r["success"] for r in rows) else 1


def _activity_for(golden_dir: Path | None, target: str) -> float:
    """从该模块的金标准激励里数出翻转率。

    没有金标准时退回 0.2。那是个**假设**，不是测量——报告里的
    activity_source 字段会这么写，因为一个和工作负载无关的功耗数字对
    稀疏加速器没有意义。
    """
    if golden_dir is None:
        return 0.2
    path = golden_dir / f"{target}.json"
    if not path.is_file():
        return 0.2
    payload = json.loads(path.read_text(encoding="utf-8"))
    measured = activity_from_stimulus(payload.get("cases", []))
    return measured if measured > 0 else 0.2


# 每个模型公式覆盖哪些 elaborate 目标。分族是必要的：族内比值一致说明公式
# 的**形式**对，族间比值不一致说明**相对权重**错——两者的修法完全不同。
_FAMILIES = {
    "topk_area_units": ("TopK_S", "TopK"),
    "array_area_units": ("RePEArray_S", "RePEArray_L"),
}


def _report_model_gap(rows: list[dict]) -> None:
    """一阶模型 vs 真实综合。

    模型的单位是任意的「area units」，绝对值本来就没法比。要看的是**比值在
    哪一层散开**：

      族内一致、族间不一致 → 公式形式对，相对权重错。协同优化器在用
        `kept_per_block` 换阵列规模，权重错就是取舍做错了。
      族内也不一致        → 公式形式本身就错，不是缩放能救的。
    """
    by_target = {r["target"]: r for r in rows
                 if r["success"] and r["model_area_units"] and r["cell_area_um2"]}
    if len(by_target) < 2:
        return

    print("\n一阶面积模型 vs 实测（Nangate45）")
    print(f"{'目标':<16}{"模型(um^2)":>13}{'实测(um^2)':>13}{'um^2/unit':>12}")

    family_scales: dict[str, list[float]] = {}
    for family, targets in _FAMILIES.items():
        present = [by_target[t] for t in targets if t in by_target]
        if not present:
            continue
        print(f"  [{family}]")
        for r in present:
            scale = r["cell_area_um2"] / r["model_area_units"]
            family_scales.setdefault(family, []).append(scale)
            print(f"    {r['target']:<14}{r['model_area_units']:>13.1f}"
                  f"{r['cell_area_um2']:>13.1f}{scale:>12.1f}")

    print()
    means = []
    for family, scales in family_scales.items():
        within = max(scales) / min(scales) if len(scales) > 1 else 1.0
        mean = sum(scales) / len(scales)
        means.append(mean)
        verdict = "形式正确" if within < 1.25 else "形式可疑"
        print(f"  {family:<20} 族内一致性 {within:.2f}x（{verdict}），"
              f"标定 {mean:.1f} um^2/unit")

    if len(means) > 1:
        skew = max(means) / min(means)
        print(f"\n  族间相对权重偏差 {skew:.1f}x")
        if skew < 1.25:
            print("  模型的相对权重可用，只差一个全局缩放。")
        else:
            print("  相对权重错了：模型低估了执行阵列相对于预测单元的面积。")
            print("  协同优化器正是在用 kept_per_block 换阵列规模，"
                  "所以这个偏差直接改变它选出的点。")

    sram = next((r for r in rows if r["target"] == "SRAM" and r["success"]), None)
    if sram:
        print(f"\n  注：SRAM 实测 {sram['cell_area_um2']:.0f} um^2 不用于标定。"
              f"yosys 没有存储器宏编译器，把 SyncReadMem 映射成了 "
              f"{sram['cell_count']} 个触发器；真实芯片会用 SRAM 宏，面积小"
              f"一到两个数量级。这个数字反映的是综合流程的缺失，不是设计的面积。")


if __name__ == "__main__":
    raise SystemExit(main())
