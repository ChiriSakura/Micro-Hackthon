"""The verified-template registry the µArch Agent composes from.

The proposal's appendix is explicit: the µArch Agent "guarantees hardware
validity by composing verified Chisel modules rather than unrestricted RTL
generation". So generation is retrieval plus parameterisation over this registry,
and a template that has not passed an independent test cannot be instantiated.

Every entry below describes a module that really exists, and every
``blocking_issue`` records a *measured* reason rather than "untested":
``FAST/hardware`` builds all of them through Chisel 3.6 and Verilator
(``slurm/rtl/fast_rtl_elaborate_all.slurm``). All 16 configurations now elaborate
and lint clean, which took five fixes -- three of them to make the DynaX
release compile at all, and one whole module it does not ship.

``provenance`` is therefore load-bearing, not bookkeeping. A result measured on
``exp_unit`` is a result about FAST's reconstruction of a module DynaX describes
but does not release, and calling that a DynaX baseline would be false. The
Critic reads this field when attributing a number to a layer.

Elaboration is necessary, not sufficient: a template is ``verified`` only once
it agrees with an independent reference in simulation. Two do so far
(``topk``, ``exp_unit``); the rest carry the testbench they still need.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from fast.schemas.models import ArchSpecs


@dataclass(frozen=True)
class ParameterRange:
    """Legal values for one Chisel parameter."""

    name: str
    choices: tuple[int, ...]

    def admits(self, value: int) -> bool:
        return value in self.choices


# Where a template's RTL actually came from. The distinction survives into the
# Critic's attribution: "DynaX measured 97% utilisation" and "our reconstruction
# of the module DynaX omitted measured 97% utilisation" are different claims.
PROVENANCE_UPSTREAM = "dynax-upstream"        # released source, used as-is
PROVENANCE_PATCHED = "dynax-patched"          # released source, defect fixed by FAST
PROVENANCE_RECONSTRUCTED = "fast-reconstruction"  # not in the release at all


@dataclass(frozen=True)
class TemplateRecord:
    """One Chisel module the µArch Agent may instantiate."""

    template_id: str
    digest: str
    manifest_uri: str
    verified: bool
    source: str = ""
    role: str = ""
    parameters: tuple[ParameterRange, ...] = ()
    blocking_issue: str = ""
    provenance: str = PROVENANCE_UPSTREAM
    # What FAST changed, when provenance is not upstream. Empty for upstream.
    patch_note: str = ""
    # Which configuration the simulation actually covered. `verified` is a claim
    # about evidence, and the evidence has a size: RePEArray was checked as a
    # 4x2 array, not as the 64x8 the paper reports, and saying so is the
    # difference between a verified template and an overclaimed one.
    verified_scope: str = ""

    def admits(self, **values: int) -> tuple[str, ...]:
        """Parameter assignments this template cannot legally take."""
        ranges = {item.name: item for item in self.parameters}
        problems = []
        for name, value in values.items():
            allowed = ranges.get(name)
            if allowed is None:
                continue
            if not allowed.admits(value):
                problems.append(f"{self.template_id}.{name}={value} not in {allowed.choices}")
        return tuple(problems)


DYNAX_TEMPLATES: tuple[TemplateRecord, ...] = (
    TemplateRecord(
        template_id="exp_unit",
        digest="sha256:exp-unit-shift-lut-g4",
        manifest_uri="file://FAST/hardware/src/main/scala/exp_unit/exp_unit.scala",
        # Verified: 116 points, 7 cases, bit-exact against the datapath spec --
        # both saturation edges, all 16 LUT slots, the sign boundary and 64
        # random inputs (slurm/rtl/fast_rtl_verify.slurm, job 17003507).
        verified=True,
        source="FAST/hardware/src/main/scala/exp_unit/exp_unit.scala",
        role="exponential",
        parameters=(
            ParameterRange("bits", (8, 16, 32)),
            ParameterRange("fracBits", (3, 4, 5, 6)),
        ),
        blocking_issue="",
        provenance=PROVENANCE_RECONSTRUCTED,
        verified_scope="bits=16 point=8 fracBits=4; 116 points over both saturation edges, all 16 LUT slots and the sign boundary",
        patch_note=(
            "repe.scala, prepe_1_2.scala and prepe_1_4.scala all import "
            "exp_unit.ExpUnitFixPoint, which DynaX does not ship; five of its "
            "eight sources cannot elaborate without it. FAST supplies a "
            "shift-and-LUT exponential matching the call signature. Any RePEA or "
            "PrePEA number therefore depends on OUR exponential unit."
        ),
    ),
    TemplateRecord(
        template_id="topk",
        digest="sha256:topk-fixed-boundary",
        manifest_uri="file://FAST/hardware/src/main/scala/predict_unit/topk.scala",
        # Verified: elaborated with Chisel 3.6.1, verilated with Verilator 5.052
        # and checked against torch.topk on the module's own fixed-point grid --
        # 8 cases, 128 lanes, zero mismatches (job 17003045).
        verified=True,
        source="FAST/hardware/src/main/scala/predict_unit/topk.scala",
        role="predict",
        parameters=(
            ParameterRange("m", (16, 32, 64)),
            ParameterRange("n", (4, 8, 16, 32, 64)),
            ParameterRange("bits", (8, 16)),
        ),
        blocking_issue="",
        provenance=PROVENANCE_PATCHED,
        verified_scope="m=64 n=16 bits=16; 8 blocks x 16 lanes against torch.topk",
        patch_note=(
            "TopFirst and TopStage cleared runnerUpReg in the same cycle they "
            "pulsed valid; last-assignment-wins wiped the value being forwarded, "
            "so every m-wide block lost its final element and all lower ranks "
            "shifted up by one. Upstream still carries this."
        ),
    ),
    TemplateRecord(
        template_id="repe",
        digest="sha256:repe-schedule-derived",
        manifest_uri="file://FAST/hardware/src/main/scala/execute_unit/repe.scala",
        # Verified: 157 cycles across 11 schedules, cycle-by-cycle on io.out --
        # dot products, the exponential phase, AV drain, the zero-column escape,
        # accumulator wrap and three random control walks (job 17004012).
        verified=True,
        source="FAST/hardware/src/main/scala/execute_unit/repe.scala",
        role="execute_pe",
        parameters=(
            ParameterRange("regWidth", (4, 8, 16, 32, 64)),
            ParameterRange("bits", (8, 16)),
        ),
        blocking_issue="",
        provenance=PROVENANCE_UPSTREAM,
        verified_scope="regWidth=8 bits=16; 157 cycles over 11 schedules, every control state and phase transition",
    ),
    TemplateRecord(
        template_id="repe_array",
        digest="sha256:repe-array-elaborated",
        manifest_uri="file://FAST/hardware/src/main/scala/execute_unit/repe_array.scala",
        verified=True,
        source="FAST/hardware/src/main/scala/execute_unit/repe_array.scala",
        role="execute",
        parameters=(
            ParameterRange("numRows", (4, 8, 16, 32, 64)),
            ParameterRange("peCountPerRow", (4, 8, 16, 32)),
            ParameterRange("regWidth", (8, 16, 32, 64)),
            ParameterRange("bits", (8, 16)),
            ParameterRange("colSelectBits", (4, 5, 6, 7)),
        ),
        # RePERow and RePEArray both agreed with a structural model composed
        # from the verified RePE: the row's two latencies and adder tree over
        # 87 cycles, the array's inter-row skew over 56. The control schedule
        # they were checked against is derived rather than documented -- neither
        # the sources nor the paper state one -- so the reference is FAST's
        # reading of the datapath, recorded in gen_golden.py's RePEModel.
        blocking_issue="",
        provenance=PROVENANCE_UPSTREAM,
        verified_scope=(
            "RePERow peCount=8 regWidth=8 (87 cycles), and RePEArray at three "
            "sizes: 4x2 regWidth=4 (56 cycles) for iteration, plus BOTH paper "
            "configurations -- DynaX-S 32x4 regWidth=8 (112 cycles) and DynaX-L "
            "64x8 regWidth=16 (176 cycles), slurm/rtl/fast_rtl_verify_paper.slurm. "
            "The reference is a structural model composed from the verified RePE; "
            "the control schedule it encodes is derived from the datapath rather "
            "than documented, since neither the sources nor the paper state one."
        ),
    ),
    TemplateRecord(
        template_id="prepe",
        digest="sha256:prepe-1-2-verified",
        manifest_uri="file://FAST/hardware/src/main/scala/predict_unit/prepe_1_2.scala",
        # Verified: 116 cycles across 8 schedules, all five registered outputs
        # compared every cycle -- both halves of the 1:2 select, the input
        # counter's two-cycle sampling rate, and psum wrap (job 17004090).
        verified=True,
        source="FAST/hardware/src/main/scala/predict_unit/prepe_1_2.scala",
        role="predict_pe",
        parameters=(ParameterRange("outBits", (8, 12, 16)),),
        blocking_issue="",
        provenance=PROVENANCE_UPSTREAM,
        verified_scope="outBits=12; 116 cycles over 8 schedules, both halves of the 1:2 select",
    ),
    TemplateRecord(
        template_id="prepe_array",
        digest="sha256:prepe-array-elaborated",
        manifest_uri="file://FAST/hardware/src/main/scala/predict_unit/prepe_1_4.scala",
        verified=True,
        source="FAST/hardware/src/main/scala/predict_unit/prepe_1_2.scala",
        role="predict_quant",
        parameters=(
            ParameterRange("width", (16, 32, 64)),
            ParameterRange("height", (16, 32, 64)),
            ParameterRange("bits", (8, 16)),
        ),
        # Elaborates at both configurations. Note the psum width constraint the
        # sources impose but do not state: prepe_*.scala zero-extend the partial
        # sum with Cat(0.U((bits - internalBits - append).W), ...), so
        # internalBits + append <= bits or elaboration fails on a negative width.
        # The array is where the 1:2 pruning decision is made, and the arbiter
        # for it is not a mirror of the RTL but DynaX's own software: this
        # accelerator exists to run quant_qk_matmul("1_2_4bit"), so that is what
        # it has to reproduce. It does -- under one condition, recorded in
        # verified_scope below, that the sources never state.
        blocking_issue="",
        provenance=PROVENANCE_UPSTREAM,
        verified_scope=(
            "Both pruning paths at height=2 width=8, each against DynaX's own "
            "quant_qk_matmul rather than a mirror of the RTL: PrePEArray_1_2 "
            "(outBits=12, 108 cycles, vs '1_2_4bit') and PrePEArray_1_4 "
            "(outBits=15, 108 cycles, vs '1_4_6bit'). "
            "USAGE CONSTRAINT, the same in both and stated in neither: a group's "
            "selection index runs OPPOSITE to its arrival order, so each group "
            "must be presented in DESCENDING index order for a kept Q to meet "
            "its own K. Over 200 random inputs the correct order agrees with the "
            "software 200/200 and the reversed order 4/200 (1:2) and 12/200 "
            "(1:4). Stimulus limits: no ties within a group (the software keeps "
            "the lowest index, the RTL's strict `>` keeps the highest), operands "
            "non-negative so torch.abs is a no-op, and K bounded so exp(psum) "
            "stays below the Q8.8 saturation point -- with full-range 6-bit K a "
            "deliberately wrong order still agrees 149/200 because every case "
            "reads 32767 -- the bound is now derived from the chain length "
            "rather than fixed, because the paper sizes have chains 4-8x longer. "
            "VERIFIED AT THE PAPER SIZES: DynaX-S PrePEA 32x32 (516 cycles) and "
            "DynaX-L PrePEA 64x32 (672 cycles), slurm/rtl/fast_rtl_verify_paper.slurm. "
            "Reaching them needed the settling window to scale as height + chain "
            "length -- the systolic latency itself, which a 2-row instance hides."
        ),
    ),
    TemplateRecord(
        template_id="psum_softmax",
        digest="sha256:psum-softmax-resize-fix",
        manifest_uri="file://FAST/hardware/src/main/scala/predict_unit/psum_softmax.scala",
        verified=True,
        source="FAST/hardware/src/main/scala/predict_unit/psum_softmax.scala",
        role="normalize",
        parameters=(ParameterRange("bitWidth", (8, 16)),),
        # Verified: 31 points across 7 cases, bit-exact including the widths it
        # truncates at (job 17003842).
        blocking_issue="",
        provenance=PROVENANCE_PATCHED,
        verified_scope="bitWidth=16 point=8; 31 points including both overflow paths",
        patch_note=(
            "psum_softmax.scala:26 called .resize() on an SInt, which chisel3 "
            "3.6 does not provide -- the file does not compile as released. "
            "Replaced with .pad(resultWidth), a no-op at the current widths."
        ),
    ),
    TemplateRecord(
        template_id="sram",
        digest="sha256:sram-mux1h-fix",
        manifest_uri="file://FAST/hardware/src/main/scala/execute_unit/sram.scala",
        verified=True,
        source="FAST/hardware/src/main/scala/execute_unit/sram.scala",
        role="memory",
        parameters=(
            ParameterRange("bankCount", (2, 4, 8, 16)),
            ParameterRange("bankWidth", (64, 128, 256)),
        ),
        # Verified: 22 checked reads across 4 cases (job 17004013), after the
        # second defect below was fixed.
        blocking_issue="",
        provenance=PROVENANCE_PATCHED,
        verified_scope="bankCount=4 bankDepth=256 bankWidth=64; 22 reads, with and without bank crossings",
        patch_note=(
            "Two defects. sram.scala:52 called the two-argument Mux1H with a "
            "Seq[(Bool, UInt)], which matches no overload -- the file does not "
            "compile as released. And the bank multiplexer selected with the "
            "address being presented rather than the one that issued the read, "
            "so every read crossing a bank boundary returned the wrong bank's "
            "data; SyncReadMem has one cycle of latency, so the select needs a "
            "RegNext. Isolated by tb_sram.cpp: single_bank and repeat_read pass "
            "without the fix, bank_switch fails every read."
        ),
    ),
)


@dataclass
class TemplateRegistry:
    """Retrieval over the template library: the 'RAG' half of the µArch Agent.

    With a library this small, retrieval is filtering, and that is the point:
    the agent selects among modules that exist rather than emitting RTL, so a
    parameter it cannot satisfy surfaces as a refusal instead of as unsynthesisable
    Verilog.
    """

    templates: tuple[TemplateRecord, ...] = field(default_factory=lambda: DYNAX_TEMPLATES)

    def by_id(self, template_id: str) -> TemplateRecord | None:
        return next((item for item in self.templates if item.template_id == template_id), None)

    def for_role(self, role: str, *, verified_only: bool = True) -> tuple[TemplateRecord, ...]:
        return tuple(
            item for item in self.templates
            if item.role == role and (item.verified or not verified_only)
        )

    def unverified(self) -> tuple[TemplateRecord, ...]:
        return tuple(item for item in self.templates if not item.verified)

    def blocking_issues(self) -> dict[str, str]:
        """Why each unverified template cannot be used yet."""
        return {item.template_id: item.blocking_issue for item in self.unverified()}


def required_col_select_bits(block_m: int) -> int:
    """A column index inside an m-wide block, as ``TopK`` computes it."""
    return max(1, math.ceil(math.log2(max(block_m, 2))))


# --------------------------------------------------------------------------
# 面积模型：形式来自结构，系数来自实测
# --------------------------------------------------------------------------
#
# 这些公式原本用的是任意的「area units」，从未被任何工具校准过。协同优化器
# 却在用它们做取舍——拿 kept_per_block（预测单元面积）换阵列规模（执行单元
# 面积）——所以两族之间的**相对**权重直接决定它选出哪个点。
#
# yosys + Nangate45 的实测（slurm/rtl/fast_synthesis.slurm，job 17018014）：
#
#     TopK(32,8,16)          模型   72.0 units    实测   3141.7 um^2   43.6
#     TopK(64,16,16)         模型  137.6 units    实测   6468.9 um^2   47.0
#     RePEArray(32,4,16,8)   模型  335.9 units    实测 371999.9 um^2 1107.6
#     RePEArray(64,8,16,16)  模型 1343.5 units    实测1591880.2 um^2 1184.9
#
# 读法很明确：**族内一致（1.07-1.08x），族间差 25.3x**。族内一致说明公式的
# 形式是对的（面积确实按 n、按 MAC 数缩放）；族间不一致说明相对权重错了——
# 模型把执行阵列相对预测单元低估了 25 倍。
#
# 所以修法不是换公式，是给两族各自乘上实测的标定系数，让二者都以 um^2 为
# 单位。之后同一个数字既能排序也能和综合结果直接比。
#
# 工艺是 Nangate45（开源 45nm），不是论文的 28nm 商业工艺——绝对值不可与
# 论文的 1.08 / 6.05 mm^2 比较。换工艺只需重跑综合并更新这两个常数。
_TOPK_UM2_PER_UNIT = 45.3
_ARRAY_UM2_PER_UNIT = 1146.2


def topk_area_units(m: int, n: int, bits: int) -> float:
    """TopK 的面积，um^2（Nangate45）。

    ``TopK`` 由 ``TopFirst`` 加 ``n - 1`` 个 ``TopStage`` 组成，跨 m 宽的块，
    所以面积随保留数增长而不是随稀疏率——一个每块保留更多的 kernel 会花掉
    预测单元的面积，即便它的执行单元工作量下降了。
    """
    raw = float(n) * bits * 0.5 + math.log2(max(m, 2)) * bits * 0.1
    return raw * _TOPK_UM2_PER_UNIT


def array_area_units(num_rows: int, pe_per_row: int, bits: int, reg_width: int) -> float:
    """RePEArray 的面积，um^2（Nangate45）。乘法器主导，按 bits² 缩放。"""
    macs = num_rows * pe_per_row
    raw = macs * (bits ** 2) * 0.01 + num_rows * reg_width * bits * 0.002
    return raw * _ARRAY_UM2_PER_UNIT


# softmax 除法器的实测曲线（Nangate45，slurm job 17085953）。
#
#   级数   面积 um^2   关键路径    频率      延迟
#     0      2081.4    14.780 ns   68 MHz    0 拍   ← 上游的组合除法
#     1      2887.2    10.895 ns   92 MHz    1 拍
#     4      4160.0     3.269 ns  306 MHz    4 拍
#     8      5411.8     1.980 ns  505 MHz    8 拍   ← 第一个越过 500 MHz
#    12      6367.5     1.546 ns  647 MHz   12 拍
#    24      9321.2    （时序不可信，扇出主导）      收益已饱和
#
# 三件事从这条曲线上读出来：
#
# 1. 8 级的面积代价是 +3331 um^2，对比 RePEArray_S 的 371999 um^2 只有
#    **0.9%**——用不到 1% 的系统面积把时钟从 68 MHz 提到阵列决定的 450 MHz。
# 2. 功耗**下降**（81.0 -> 15.9 mW）。组合除法的长链会产生大量毛刺，插了
#    寄存器把毛刺截断了。所以这不是「面积换频率」，是面积换频率**加**功耗。
# 3. 曲线在 12 级附近拐弯，24 级收益饱和而面积还在涨。
_DIVIDER_PROFILE: dict[int, tuple[float, float]] = {
    # 级数 -> (面积 um^2, 关键路径 ns)
    0: (2081.4, 14.780),
    1: (2887.2, 10.895),
    4: (4160.0, 3.269),
    8: (5411.8, 1.980),
    12: (6367.5, 1.546),
}


def divider_area_um2(stages: int) -> float:
    """除法器面积，um^2（Nangate45 实测）。未测过的级数按最近的插值。"""
    if stages in _DIVIDER_PROFILE:
        return _DIVIDER_PROFILE[stages][0]
    nearest = min(_DIVIDER_PROFILE, key=lambda s: abs(s - stages))
    return _DIVIDER_PROFILE[nearest][0]


def divider_critical_path_ns(stages: int) -> float:
    """除法器的关键路径，ns（Nangate45 实测）。

    这是**整个系统时钟的下界之一**：softmax 归一化在数据通路上，它慢，
    整条流水线就得跟着慢。协同优化器必须把它和阵列的关键路径一起取 max。
    """
    if stages in _DIVIDER_PROFILE:
        return _DIVIDER_PROFILE[stages][1]
    nearest = min(_DIVIDER_PROFILE, key=lambda s: abs(s - stages))
    return _DIVIDER_PROFILE[nearest][1]


# 执行阵列的关键路径，实测 2.22-2.23 ns（32x4 与 64x8 几乎一样——它是
# 单个 PE 内部的路径，不随阵列规模变化）。
ARRAY_CRITICAL_PATH_NS = 2.23


def sram_area_units(sram_bytes: int) -> float:
    """SRAM 的面积，um^2——**未经标定**。

    实测拿不到有意义的值：yosys 没有存储器宏编译器，把 ``SyncReadMem`` 映射
    成了 226703 个触发器，530247 um^2。真实芯片会用 SRAM 宏，面积小一到两个
    数量级。那个数字反映的是综合流程缺一环，不是设计的面积。

    这里保留原来的系数并按每字节 ~0.1 um^2 换算——一个 45nm 下 SRAM 宏的
    粗略量级。它是**估计**，和上面两个不同：那两个有实测支撑。
    """
    return sram_bytes * 0.1
