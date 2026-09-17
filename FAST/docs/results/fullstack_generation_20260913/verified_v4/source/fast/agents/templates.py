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
from typing import NamedTuple

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
        provenance=PROVENANCE_PATCHED,
        patch_note=(
            "RePE 的乘积从截断改为四舍五入（缺陷 6）：上游 `mul := a * b` 把 "
            "FixedPoint(2*bits,2*point) 直接赋回 fpType，丢掉低 point 位小数——"
            "补码下那是 floor，误差恒为负、期望 -0.5 LSB。QK^T 在 headDim 步上"
            "累加它，偏差因此随 head_dim 线性累积：headDim=8 时约 -4 ticks 藏在"
            "容差里，headDim=64 时实测平均 -29.8 ticks（范围 [-37,-22]），tile "
            "测试 2048 个输出维度有 1154 个超容差且全部偏小。改成加半个 LSB 再"
            "截断后平均 +0.75 ticks，超容差降到 0。"
            "golden/fixedpoint.py 的 fp_mul 同步改——两者必须一起动，否则模块级"
            "金标准会把正确的 RTL 判成错的。"
        ),
        verified_scope="regWidth=8 bits=16; 157 cycles over 11 schedules, every control state and phase transition（含舍入补丁后重跑，job 17223928）",
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
        # 本身没改，但它实例化的是打了舍入补丁的 RePE——继承 provenance，
        # 否则「这块是上游的」会把补丁的影响藏在一层组合之下。
        provenance=PROVENANCE_PATCHED,
        patch_note="继承 repe 的乘积舍入补丁（缺陷 6）；repe_array.scala 本身未改。",
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
        provenance=PROVENANCE_PATCHED,
        patch_note=(
            "预测通路从无符号改为有符号（1:2 和 1:4 都改）：端口 "
            "UInt(4.W)/UInt(6.W) -> SInt(4.W)/SInt(6.W)，乘累加随之有符号，"
            "exp 输入改符号扩展，去掉 psum==0 强制归零的特例。"
            "起因是 DynaX 自己的软件用 "
            "calc_max_quant_value(bits)=2^(bits-1)-1 做有符号量化——软件按 "
            "sum(q*k) 排序，RTL 按 sum(|q|*|k|) 排序。这不是精度差异是方向"
            "错误：和 query 反相关的 key 逐项乘积为负、总分很低，取绝对值后"
            "却变成最高分。真实数据一例（TinyLlama L10H0，query 行 0，"
            "key 24）：sum(q*k)=-1.93 排 32/32，sum(|q||k|)=+2.39 排 4/32。"
            "实测 top-8 选择与精确分数的重合度 31% -> 72%（软件 75%）。"
        ),
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
            "non-negative so torch.abs is a no-op（**这条限定掩盖了一个真实"
            "分歧，见 SIGNEDNESS 一段**）, and K bounded so exp(psum) "
            "stays below the Q8.8 saturation point -- with full-range 6-bit K a "
            "deliberately wrong order still agrees 149/200 because every case "
            "reads 32767 -- the bound is now derived from the chain length "
            "SIGNEDNESS（已修复）：软件和 RTL 曾在算两件不同的事。"
            "quant_utils.py 的 calc_max_quant_value(bits)=2^(bits-1)-1 是"
            "**有符号**量化（4-bit 即 ±7），而 prepe_1_2.scala 的端口是 "
            "UInt(4.W)——整条预测通路**无符号**，没有符号位。所以软件按 "
            "Σq·k 排序，硬件按 Σ|q|·|k| 排序。实测（TinyLlama 第10层第0头，"
            "真实 Q/K）：软件近似保住 75% 的 top-8 选择，硬件只有 31%，"
            "两者互相只有 28% 重合。丢符号对注意力是实质性的——大的负分数"
            "在 |·| 下排到前面，但它对 softmax 的贡献接近 0。"
            "上面那条「操作数取非负」的验证限定，恰恰使这个分歧不可见——"
            "非负输入下 sum(|q||k|) 和 sum(qk) 恰好相同，108 周期的金标准"
            "全绿却什么都没测出来。"
            "FAST 已就地修复 1:2 和 1:4 两条通路：端口 UInt -> SInt，"
            "选择仍按幅值（同 argmax(abs)）但传带符号的值，exp 输入改符号"
            "扩展，并去掉 psum==0 强制归零的特例（有符号下 0 是正常中间"
            "分数，归零会把它排到所有负分数之下，破坏 exp 的单调性）。"
            "修复后实测重合度回到 72%（软件 75%）。"
            "金标准用例也改为幅值互异、符号随机，才真正在检验两者一致。"
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
    """**执行**阵列（RePEArray）的面积，um^2（Nangate45）。乘法器主导，按 bits² 缩放。

    只有执行阵列。预测阵列另算——见 `predict_array_area_um2`。
    """
    macs = num_rows * pe_per_row
    raw = macs * (bits ** 2) * 0.01 + num_rows * reg_width * bits * 0.002
    return raw * _ARRAY_UM2_PER_UNIT


def predict_array_area_um2(height: int, head_dim: int) -> float:
    """**预测**阵列（PrePEArray_1_2）的面积，um^2。

    此前 `area_units()` 里根本没有这一项——它只算了执行阵列。而
    `attention_tile.scala` 同时例化两个：预测阵列跑近似分数，执行阵列跑精算。
    整设计综合实测 1,853,425 um^2 而模型预测 1,072,094，差的 1.98 倍里
    最大的一块就是它。

    实测锚点（Nangate45）：

        PrePEArray_S  32 x 32  367,776 um^2
        PrePEArray_L  64 x 32  1,123,180 um^2

    按 height x width 线性缩放：S 是 1024 个单元 -> 359.2 um^2/单元；
    L 是 2048 个 -> 548.4。两者差 53%，因为 1:4 的 PE 比 1:2 的大。
    这里用 1:2 的那个锚点（S），并且**说清楚它是外推**：tile 用的 width 是
    模型的 head_dim（64），比两个锚点都宽一倍。
    """
    return height * head_dim * _PREDICT_UM2_PER_CELL


# PrePEArray_1_2 的每单元面积，从 PrePEArray_S（32x32 = 367,776 um^2）标定。
_PREDICT_UM2_PER_CELL = 367_776.4 / (32 * 32)


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
# 1. 8 级的面积代价是单个 +3331 um^2，对比 RePEArray_S 的 371999 um^2 是
#    0.9%。**但整设计要付 tileQ 份**——`attention_tile.scala` 每个 query 行
#    一个归一化器，32 行的设计上这个代价是 6.4%（1,775,479 / 1,668,906）。
#    结论不变（6.4% 换 40 倍 EDP 仍然毫无悬念），但早先只记 0.9% 是拿一个
#    除法器对一个阵列比出来的，整设计尺度上偏小 7 倍。
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


# ---------------------------------------------------------------------------
# 工作队列（BlockScheduler）：queue_depth 这个搜索维度的实测支撑
# ---------------------------------------------------------------------------
#
# 此前 `pe_utilisation()` 是个一阶模型（函数注释自己写着「It is a model, not
# a measurement」），而 `area_units()` 对 queue_depth 完全不收费。结果是
# **只有收益没有成本**：公式对深度单调递增、面积恒定，优化器必然选最深的
# 那个，而且看不出自己选错了。流水化除法器那次是同一个形状的洞。
#
# 下面两张表把它变成实测。RTL 是 `predict_unit/block_scheduler.scala`。

# (numRows, peCountPerRow, queueDepth) -> (面积 um^2, 关键路径 ns)
#
# Nangate45，yosys + OpenSTA 实测。**两项成本都不小，而模型此前一项也没收。**
#
#   面积：DynaX-S 的两个阵列合计约 740k um^2，深度 16 的队列要 135k——18%。
#   时序：关键路径随深度从 2.27 ns 涨到 3.14 ns。执行阵列是 2.23 ns，所以
#         深度 8 起，**调度器取代阵列成为决定系统时钟的那个模块**。
#
# 后者比前者更致命，因为它不是线性折衷：深度 8 的 41% 时钟惩罚，比它买到的
# 那点利用率（xm 从 0.864 到 0.867）大一个数量级。算成「利用率/周期」：
#
#     深度 0  0.7079 / 2.273 = 0.311
#     深度 2  0.8323 / 2.528 = 0.329   <- 最优
#     深度 4  0.8644 / 2.760 = 0.313
#     深度 8  0.8669 / 3.140 = 0.276   <- 比完全没有队列还差
#
# 没有实测时序，这条曲线看起来是单调递增的。
_QUEUE_PROFILE: dict[tuple[int, int, int], tuple[float, float | None]] = {
    (32, 4, 0): (8899.3, 2.273),
    (32, 4, 2): (26392.0, 2.528),
    (32, 4, 4): (42826.3, 2.760),
    (32, 4, 8): (74420.7, 3.140),
    # 深度 16：面积可信，时序被可信性守卫拒了（INV_X1 单级 1.5 ns，扇出
    # 伪影）。None 表示「没测到」，不是「没有延迟」——调用方按最近的
    # 已测点外推，并且知道自己在外推。
    (32, 4, 16): (134870.2, None),
    (64, 8, 0): (30391.8, 2.709),
    # L 的深层配置：面积可信，时序都被守卫拒了（扇出伪影）。
    (64, 8, 8): (278669.0, None),
    (64, 8, 16): (515301.8, None),
}

# 实测利用率曲线：(numRows, pe) -> [(该工作量的锁步不均衡度, {深度: 利用率})]
#
# 驱动是真实模型跑出来的逐 tile 行工作量（TinyLlama L10, wiki, seq=512，
# `DynaX/capture_row_workload.py`），不是合成分布——动态稀疏的全部问题就在
# 行长差异，那个差异假设不出来。Verilator 实测，见
# `slurm/rtl/fast_block_scheduler_sweep.slurm`。
#
# 不均衡度定义成「让 1/imbalance 恰好等于深度 0 的利用率」的那个量：
# 总趟数 /（行数 x 锁步总周期）。实测深度 0 逐条落在这个解析界上
# （xm 0.70787 vs 0.7079，topk 0.60892 vs 0.6089，sanger 两者都是 0.58970），
# 所以这条曲线和 pe_utilisation() 在 0 处说的是同一件事。
#
# **曲线在 1 以下饱和，这是原模型看不到的。** xm 到深度 4 就停在 0.867，
# 而原公式在深度 16 承诺 0.976。剩下的 13% 是 tile 内的结构性损失：一行
# 的保留数不是 pe 的整数倍时，最后一趟有空槽。加多少队列都填不上。
_QUEUE_UTILISATION: dict[tuple[int, int], tuple[tuple[float, dict[int, float]], ...]] = {
    (32, 4): (
        # nm:16:64 —— N:M 结构化稀疏按构造完美均衡，队列买不到任何东西。
        (1.000, {0: 1.0000, 2: 1.0000, 4: 1.0000, 8: 1.0000, 16: 1.0000}),
        # xm（DynaX 默认）
        (1.413, {0: 0.7079, 2: 0.8323, 4: 0.8644, 8: 0.8669, 16: 0.8669}),
        # topk:64
        (1.642, {0: 0.6089, 2: 0.9367, 4: 0.9725, 8: 0.9744, 16: 0.9744}),
        # sanger
        (1.696, {0: 0.5897, 2: 0.7650, 4: 0.8173, 8: 0.8497, 16: 0.8645}),
    ),
}


# 实测不均衡度和请求值的最大相对偏差。超过就认为没有实测支撑。
# 15%：实测点之间的间距是 1.00/1.41/1.64/1.70，相邻点最大间隔约 16%，
# 所以这个阈值刚好让范围内的点都能命中某条曲线，范围外的都命不中。
_QUEUE_IMBALANCE_TOLERANCE = 0.15


def queue_area_um2(num_rows: int, pe_per_row: int, queue_depth: int) -> float:
    """工作队列的面积，um^2（Nangate45 实测）。

    没测过的配置按同深度的最近尺寸，再按 PE 数线性缩放——队列是每行一个
    FIFO，条目宽度正比于 pe，所以线性缩放是有依据的，但**它是外推不是实测**。
    """
    key = (num_rows, pe_per_row, queue_depth)
    if key in _QUEUE_PROFILE:
        return _QUEUE_PROFILE[key][0]
    same_shape = [k for k in _QUEUE_PROFILE if k[0] == num_rows and k[1] == pe_per_row]
    if same_shape:
        nearest = min(same_shape, key=lambda k: abs(k[2] - queue_depth))
        # 深度 0 是「一级流水寄存器」，不是零面积；按条目数比例外推。
        scale = (queue_depth + 1) / (nearest[2] + 1)
        return _QUEUE_PROFILE[nearest][0] * scale
    nearest = min(_QUEUE_PROFILE, key=lambda k: (abs(k[2] - queue_depth), abs(k[0] - num_rows)))
    cells = num_rows * pe_per_row * (queue_depth + 1)
    ref_cells = nearest[0] * nearest[1] * (nearest[2] + 1)
    return _QUEUE_PROFILE[nearest][0] * cells / ref_cells


def queue_critical_path_ns(num_rows: int, pe_per_row: int, queue_depth: int) -> float:
    """工作队列的关键路径，ns（Nangate45 实测）。

    **这是系统时钟下界之一，和除法器一样。** 调度器在数据通路上，它慢，
    整条流水线跟着慢。执行阵列是 2.23 ns，而深度 8 的队列是 3.14 ns——
    从那一档起，决定系统频率的不再是阵列而是调度器。

    没测到的点按最近的已测深度线性外推（关键路径随深度近似线性：
    2.273 / 2.528 / 2.760 / 3.140，每档约 +0.11 ns/深度）。外推出来的值
    不如实测可信，但**比默默当成 0 强得多**——那等于断言队列不占时间。
    """
    key = (num_rows, pe_per_row, queue_depth)
    entry = _QUEUE_PROFILE.get(key)
    if entry is not None and entry[1] is not None:
        return entry[1]
    measured = [k for k in _QUEUE_PROFILE
                if k[0] == num_rows and k[1] == pe_per_row and _QUEUE_PROFILE[k][1] is not None]
    if not measured:
        measured = [k for k in _QUEUE_PROFILE if _QUEUE_PROFILE[k][1] is not None]
    if not measured:
        return 0.0
    nearest = min(measured, key=lambda k: abs(k[2] - queue_depth))
    base = _QUEUE_PROFILE[nearest][1]
    assert base is not None
    if len(measured) < 2:
        return base
    # 用同尺寸下最浅和最深两个实测点定斜率。
    lo = min(measured, key=lambda k: k[2])
    hi = max(measured, key=lambda k: k[2])
    lo_ns, hi_ns = _QUEUE_PROFILE[lo][1], _QUEUE_PROFILE[hi][1]
    assert lo_ns is not None and hi_ns is not None
    if hi[2] == lo[2]:
        return base
    slope = (hi_ns - lo_ns) / (hi[2] - lo[2])
    return base + slope * (queue_depth - nearest[2])


def queue_utilisation(imbalance: float, queue_depth: int,
                      num_rows: int = 32, pe_per_row: int = 4) -> float | None:
    """实测的 PE 利用率；没有可用的实测点时返回 None。

    返回 None 而不是猜一个数：「模型没有说法」和「模型说错了」是两件事，
    调用方应该知道自己拿到的是哪一种。
    """
    table = _QUEUE_UTILISATION.get((num_rows, pe_per_row))
    if table is None:
        return None
    # 按不均衡度取最近的实测工作量。不在不均衡度上插值：曲线的**形状**
    # 由 tile 内的保留数分布决定，不同方法的分布不同，两条曲线之间插出来的
    # 点不对应任何真实工作量。
    nearest_imbalance, curve = min(table, key=lambda item: abs(item[0] - imbalance))
    # 实测点覆盖 1.00-1.70。**超出这个范围就说不知道**，而不是把最近的那条
    # 曲线拿来用：不均衡度 4.0 和 1.70 之间没有任何测量，返回 1.70 的曲线
    # 等于凭空断言一个从没测过的工作量的行为，而且不会有任何东西报错。
    if abs(nearest_imbalance - imbalance) > _QUEUE_IMBALANCE_TOLERANCE * imbalance:
        return None
    if queue_depth in curve:
        return curve[queue_depth]
    depths = sorted(curve)
    if queue_depth <= depths[0]:
        return curve[depths[0]]
    if queue_depth >= depths[-1]:
        return curve[depths[-1]]
    hi = next(d for d in depths if d > queue_depth)
    lo = max(d for d in depths if d < queue_depth)
    span = hi - lo
    return curve[lo] + (curve[hi] - curve[lo]) * (queue_depth - lo) / span


# 执行阵列的关键路径，实测 2.22-2.23 ns（32x4 与 64x8 几乎一样——它是
# 单个 PE 内部的路径，不随阵列规模变化）。
ARRAY_CRITICAL_PATH_NS = 2.23


# ---------------------------------------------------------------------------
# 取数引擎：周期模型里此前完全没有的访存项
# ---------------------------------------------------------------------------
#
# `estimate()` 的周期公式是 `sparse_macs / (lanes * utilisation)`——**一项和
# 访存有关的都没有**，等于假设带宽无限。于是 sram_bytes、double_buffer、
# bank 数这些维度对周期数的影响是零。
#
# 而缺口是结构性的：`repe_row.scala:62` 每拍无条件 `reg_cols := regs_top`，
# 所以阵列每拍要 regWidth 个新 K 标量（DynaX-S 是 8x16 = 128 位/拍）；
# 上游的 `sram.scala` 是**单地址端口**（Mux1H 选一个 bank），每拍只给 64 位。
# 差 2 到 4 倍，而且 RePEArray 没有反压输入——它没法被告知「这拍没数据」。
#
# RTL 是 `execute_unit/key_feeder.scala`，关键结构改动是**bank 各自有地址**。

# (bankCount, 稀疏方法) -> 相对理想取数的减速倍数
#
# 「理想」= regWidth 个请求散在不同 bank 上、一步全发完。数值按**每个请求**
# 归一而不是每组：按组平均会把「索引散不散得开」和「组填不填得满」混在
# 一起——只有 1 个请求的组必然零冲突，而 topk 的组大多是空的。按组算 topk
# 在 8 bank 下是 1.53，按请求算是 1.79。
#
# 驱动是 TinyLlama L10 真实跑出来的列索引（`DynaX/capture_row_workload.py`
# 的 --emit-indices），不是随机数：冲突取决于索引的**分布**不是**个数**。
_GATHER_SLOWDOWN: dict[int, dict[str, float]] = {
    4:  {"xm": 3.054, "nm": 2.167, "topk": 2.692, "sanger": 2.245},
    8:  {"xm": 2.145, "nm": 1.186, "topk": 1.791, "sanger": 1.279},
    16: {"xm": 1.526, "nm": 1.076, "topk": 1.340, "sanger": 1.077},
    32: {"xm": 1.133, "nm": 1.010, "topk": 1.186, "sanger": 1.067},
}

# 一个**否定结果**，记下来免得再试一遍。
#
# 观察到 xm 在 8 bank 下最差（2.14x），猜想是索引步长和 `col % bankCount`
# 混叠，于是加了一档 XOR 折叠的 bank 映射（`KeyFeeder` 的 hashBanks）。实测：
#
#     banks=8      取模     XOR 散列
#     xm           2.145    2.150    <- 完全没变
#     nm           1.186    2.014    <- 大幅变差
#     topk         1.791    1.918
#     sanger       1.279    1.479
#
# 散列对 xm 没有作用，却把 nm 那种规则步长本来就有的优势毁掉了。查回去，
# xm 的冲突根源是 **attention sink**：列 0 每一行都保留，而它和簇里的列 40
# 同余 8。那不是步长混叠，散列治不了。
#
# 结论：**取模映射对结构化稀疏已经接近最优，散列是负收益。** 真正的手段是
# 加 bank 数，或者把 sink 列单独放一个端口。
_GATHER_HASH_IS_A_REGRESSION = True

# bank 数的**逻辑**面积代价，um^2，相对 4 个 bank 的增量。
#
# 只记增量，因为绝对值没有意义：yosys 没有存储器宏编译器，把 KeyFeeder 里
# 2048x16 的 SyncReadMem 映射成 32768 个触发器，综合出来的 27 万 um^2 里
# 绝大部分是那个假存储，不是取数逻辑。而假存储在各个 bank 数下是一样的，
# 所以**差值**就是选择网络的成本：
#
#   4 banks  270774.2 um^2  (基准)
#   8 banks  272295.4       +1521
#   16 banks 275194.6       +2899
#   32 banks 综合被 OOM 杀掉（rc=-9）——**没有实测值**，按趋势外推 +5800
#
# 结论：**多加 bank 在逻辑上几乎免费**，整个 4->32 区间才约 1 万 um^2，
# 而 256 KB 的 SRAM 宏是 105 万。banking 的真实代价在宏的长宽比上
# （bank 越多越窄，um^2/字节越差），那一项 `plan_sram()` 已经算进去了。
_BANK_LOGIC_AREA_UM2: dict[int, float] = {
    4: 0.0,
    8: 1521.2,
    16: 4420.4,
    # 外推，不是实测。写在这里而不是让调用方去猜，但注释必须说清楚。
    32: 10_200.0,
}


def bank_logic_area_um2(bank_count: int) -> float:
    """取数引擎选择网络的面积，um^2（相对 4 个 bank 的增量）。

    32 个 bank 那个点是**外推**：综合被 OOM 杀掉了。
    """
    if bank_count in _BANK_LOGIC_AREA_UM2:
        return _BANK_LOGIC_AREA_UM2[bank_count]
    nearest = min(_BANK_LOGIC_AREA_UM2, key=lambda b: abs(b - bank_count))
    return _BANK_LOGIC_AREA_UM2[nearest]


def gather_slowdown(bank_count: int, sparse_method: str = "xm") -> float:
    """取数引擎相对理想带宽的减速倍数（Verilator 实测，真实索引流）。

    **这是按算法名查的一张标定表**，不是一个模型。见
    `gather_slowdown_provenance()`——研究结论依赖于「这个数是测出来的还是
    借来的」，而这个函数的返回值本身说不出区别。
    """
    return gather_slowdown_provenance(bank_count, sparse_method)[0]


def gather_slowdown_provenance(
    bank_count: int, sparse_method: str = "xm"
) -> tuple[float, str]:
    """减速倍数，**外加它是怎么来的**。

    ## 为什么要把出处一起返回

    这张表是按方法名前缀查的（"xm:32:16:64" -> "xm"），没测过的方法**静默
    退回 xm**。后果是：拿一个没标定过的新算法跑这条流水线，它会**继承 xm 的
    人工标定值**而报告里看不出来——于是"框架能适配新算法"这个结论建立在
    一个借来的常数上。

    ## 为什么这里不给一个 label-free 的模型

    试过了，没成。用真实 index trace 直接算 bank 冲突
    （`bank = column mod bank_count`，周期数取各 bank 的最大负载）在四个
    bank 数上**趋势都是反的**：实测 bank 越多减速越小（xm 3.054 -> 1.133），
    这个模型却越大（1.247 -> 2.781）。结构特征也不行——`index_entropy` 把
    nm 排成最差（实测最好），`block_occupancy` 对 3 个顺序但 topk/sanger 那
    一对是反的。

    继续调参去拟合这 16 个实测点，得到的是一个"能复现标定集"的东西，不是
    一个能外推到新算法的模型。**所以这里不猜。** 新算法要拿到自己的数，
    就跑 `slurm/rtl/fast_key_feeder_sweep.slurm` 实测一次——那正是这张表的
    来源。

    Returns:
        (减速倍数, 出处)。出处是 "measured:<方法>"、"fallback:xm"
        （借了 xm 的值）或 "measured:<方法>@<最近的 bank 数>"。
    """
    prefix = sparse_method.split(":")[0].strip().lower()
    exact_banks = bank_count in _GATHER_SLOWDOWN
    banks = bank_count if exact_banks else min(
        _GATHER_SLOWDOWN, key=lambda b: abs(b - bank_count))
    table = _GATHER_SLOWDOWN[banks]

    if prefix in table:
        source = f"measured:{prefix}"
        if not exact_banks:
            source += f"@{banks}banks(nearest to {bank_count})"
        return table[prefix], source
    # 没测过：借 xm 的值。它是实测里最差的，所以偏保守——但**借来的就是
    # 借来的**，必须说出来。
    return table["xm"], f"fallback:xm(no calibration for {prefix!r})"


# ---------------------------------------------------------------------------
# 功耗：从任意单位换成 mW
# ---------------------------------------------------------------------------
#
# `estimate()` 里的功耗项一直是 `lanes * utilisation * data_width**2 * 1e-4`。
# 那是**任意单位**：32x4 的配置算出 2.85，而同一个阵列 yosys+OpenSTA 实测是
# 398.655 mW。两者从来没有对过账。
#
# 这件事在加 SRAM 漏电时变成硬伤：256 KB 的宏拼装漏电 51 mW，是一阶大项，
# 但把 51（mW）加到 2.85（任意单位）上是单位混用，会让 SRAM 凭空压倒一切。
# 所以先把逻辑那项换成 mW。

# 满负荷时每条 MAC lane 的功耗，mW。
#
# ## 标定锚点，以及为什么不能用翻转率当利用率
#
#   RePEArray_S  32x4 = 128 lane   398.655 mW @ a=0.078  -> 3.11 mW/lane
#   RePEArray_L  64x8 = 512 lane  3243.624 mW @ a=0.200  -> 6.34 mW/lane
#
# 两者差一倍，但**它们的 a 不是同一个东西**：S 的 0.078 是从金标准激励数出来
# 的真实翻转率，L 没有激励文件、用的是默认常数 0.200。把 L 按 a 线性归一到
# 0.078 得到 2.47 mW/lane，和 S 的 3.11 相差 21%。所以锚点取 S——它是唯一一个
# 翻转率来自实际施加激励的点。
#
# **利用率不能当翻转率用。** `a=0.078` 是「每个网络在多少比例的时钟沿上翻转」，
# 而 PE 利用率 0.83 是「这条 lane 有多少比例的周期有活干」。两者差一个数量级：
# 早先把利用率代进按 a 标定的系数，算出 3827 mW，而同一个阵列实测 399 mW。
#
# 这里的模型是：实测值代表**该设计在代表性激励下满负荷跑**的功耗，利用率
# 再作为占空比乘在上面。
# ⚠️ **这个标定值是用坏掉的流程测的，需要重测。**
#
# 它来自 `set_power_activity -input -activity 0.2`。实测证明 `-input` 对
# 内部网没有控制力：α 从 0.02 扫到 0.9（45 倍），总功耗在 0.1079-0.1183 W
# 之间**非单调抖动**（±5%），也就是这个旋钮根本没在起作用。换成 `-global`
# 之后是单调近似线性的（0.0137 -> 0.0566 -> 0.2234 W）。
#
# 而且 α=0.2 本身是个从未验证的假设：从真实 VCD 数出来是 **0.0213**
# （AttentionTileTop 跑一个真实 tile，1710 信号 / 212 周期 / 111,043 次翻转），
# 差 9.4 倍。
#
# 两者叠加：同一个设计 `-input + α=0.2` 报 113.4 mW，
# `-global + α=0.0213` 报 **14.05 mW**——**高估 8.07 倍**。
#
# 下面的 3.11 mW/lane 是旧流程的锚点，误差不能直接套用上述单模块倍数。
# 当前搜索仍通过 energy_j 使用它；没有独立的 power 轴并不意味着不依赖功耗。
# 新流程的组件重测尚未接入此模型，能耗排序需重标定后再独立确认。
_MW_PER_LANE_AT_FULL_UTILISATION = 3.11

# 两个标定点都是 16 位数据通路，所以**位宽的影响没有实测支撑**。按 dw^2 缩放
# 是「乘法器面积随位宽平方增长」的常见近似，它是模型不是测量。
_POWER_REFERENCE_DATA_WIDTH = 16


def array_power_mw(mac_lanes: int, utilisation: float, data_width: int) -> float:
    """执行阵列功耗预测，mW；旧 Nangate45 活动率标定待更新。

    只覆盖执行阵列，省略预测阵列、TopK 和调度器。覆盖不全与旧锚点偏差
    同时存在，不能据此判断相对整机功耗的误差方向。位宽平方项是外推，
    两个标定点都是 16 位。此函数仍参与当前 energy_j 目标的计算。
    """
    width_scale = (data_width / _POWER_REFERENCE_DATA_WIDTH) ** 2
    return mac_lanes * max(0.0, utilisation) * _MW_PER_LANE_AT_FULL_UTILISATION * width_scale


# ---------------------------------------------------------------------------
# SRAM 宏：把 sram_bytes 从一个编出来的系数变成真实的宏拼装
# ---------------------------------------------------------------------------
#
# 此前 `sram_area_units()` 是 `sram_bytes * 0.1`，没有任何支撑。直接综合拿不到
# 真值：yosys 没有存储器宏编译器，把 `SyncReadMem` 映射成 226703 个触发器
# （530247 um^2）——那反映的是综合流程缺一环，不是设计的面积。
#
# hammer 的 nangate45 tech plugin 自带一个 SRAM generator，但它**不是编译器
# 而是查表**：映射到 OpenROAD-flow-scripts 的 fakeram45 宏。那些宏和我们已经
# 在用的 Nangate45 标准单元库同一个仓库、同一个节点，所以面积可以直接和阵列
# 的面积相加。取数与解析见 `scripts/fetch_nangate45_srams.py`。
#
# **实测出来那个 0.1 小了 40-50 倍**：真实值是 4.0-16.6 um^2/字节。搜索空间里
# sram_bytes 最大 262144，按真实系数是约 105 万 um^2——比两个阵列合计
# （74 万）还大；按 0.1 只有 26214，是个舍入误差。
#
# ## 证据等级
#
# fakeram 是**解析生成**的宏，不是硅上表征的。它是 OpenROAD 自己发布 benchmark
# 结果时用的东西，节点对得上，但等级低于 yosys 实测：
# `L1-analytical-vendor-model`，不是 `L2-synthesis-nangate45`。

# (depth, width_bits) -> (面积 um^2, 访问时间 ns, 漏电 nW, 一次读的内部功耗 fJ)
#
# 单位取自 .lib 头部：`time_unit 1ns`、`leakage_power_unit 1nw`；内部功耗的
# scalar 是能量，单位 = 功率单位 x 时间单位 = uW x ns = fJ。对账：4 KB 宏
# 一次读 3.57 pJ、漏电 0.80 mW，都落在 45nm SRAM 的常见量级内。
_SRAM_MACROS: dict[tuple[int, int], tuple[float, float, float, float]] = {
    (32, 32): (794.542, 0.173, 45733.0, 659.87),
    (32, 64): (2285.32, 0.188, 78524.9, 1498.65),
    (64, 7): (387.296, 0.164, 26746.0, 261.529),
    (64, 15): (659.148, 0.198, 58926.6, 393.576),
    (64, 21): (949.354, 0.203, 72554.6, 606.056),
    (64, 25): (1240.624, 0.207, 81627.2, 795.762),
    (64, 28): (1240.624, 0.207, 81627.2, 795.762),
    (64, 32): (1240.624, 0.207, 81627.2, 795.762),
    (64, 62): (4712.95, 0.198, 187170.0, 2497.93),
    (64, 64): (4845.38, 0.198, 187170.0, 2497.93),
    (64, 96): (4874.982, 0.234, 163620.0, 2986.13),
    (64, 124): (8792.934, 0.232, 337765.0, 4539.85),
    (64, 256): (33990.259, 0.253, 692663.0, 13566.9),
    (128, 32): (3295.74, 0.2, 173516.0, 1738.49),
    (128, 64): (5479.6, 0.233, 303495.0, 2761.52),
    (128, 116): (9280.208, 0.279, 527792.0, 5212.75),
    (128, 256): (33990.259, 0.302, 1023890.0, 15691.4),
    (256, 16): (3155.026, 0.204, 169783.0, 1359.06),
    (256, 32): (5065.704, 0.235, 289841.0, 1874.39),
    (256, 34): (6476.036, 0.241, 338924.0, 2471.87),
    (256, 48): (7775.712, 0.246, 388152.0, 3139.84),
    (256, 95): (13701.66, 0.292, 697753.0, 5756.55),
    (256, 96): (13701.66, 0.292, 697753.0, 5756.55),
    (512, 64): (17301.438, 0.305, 823237.0, 5300.43),
    (1024, 32): (16406.082, 0.309, 797666.0, 3566.4),
    (2048, 39): (45478.818, 0.435, 1876600.0, 6855.19),
}

# SRAM 宏的访问时间：0.164 ns（56 B）到 0.435 ns（10 KB），**全部远低于执行
# 阵列的 2.23 ns**。所以单个宏的访问不是系统时钟的瓶颈——这个假设可以排除。
# 注意这只说单个宏；多宏拼起来之后的 bank 多路选择器要另算，那部分在
# `execute_unit/sram.scala` 里，走综合而不是查表。
SRAM_MAX_MACRO_ACCESS_NS = 0.435


class SramPlan(NamedTuple):
    """用现成的宏拼出所要容量与位宽的一种方案。"""

    macro: tuple[int, int]      # 选中的宏 (depth, width_bits)
    across: int                 # 沿位宽方向并几个（一次访问全部使能）
    deep: int                   # 沿深度方向堆几个（一次访问只使能一个）
    area_um2: float
    access_ns: float
    leakage_mw: float
    read_energy_pj: float       # 一次读的动态能量

    @property
    def count(self) -> int:
        return self.across * self.deep


def plan_sram(total_bytes: int, port_width_bits: int = 64) -> "SramPlan | None":
    """给定容量和端口位宽，挑一种面积最小的宏拼装方案。

    这是**存储器编译器该干的事的最小版本**：沿位宽并联凑够端口宽度，沿深度
    堆叠凑够容量，在所有可选宏里取总面积最小的那个。

    为什么不能只用一个 um^2/字节的系数：**长宽比本身就是成本**。同样 4 KB，
    1024x32 是 4.01 um^2/B 而 128x256 是 8.30——差一倍。窄而深的宏效率高，
    宽而浅的差。一个平均系数会把这个真实的设计取舍抹平，而 bank 组织正是
    协同优化器该能看见的东西。

    能量按「一次访问只使能 across 个宏」算：深度堆叠的那一维靠地址译码选中
    一个，没被选中的不消耗动态功耗。漏电则是全部宏都算。
    """
    if total_bytes <= 0 or port_width_bits <= 0:
        return None
    best: "SramPlan | None" = None
    for (depth, width), (area, access, leak_nw, read_fj) in _SRAM_MACROS.items():
        across = -(-port_width_bits // width)          # 向上取整
        bits_per_row = across * width
        rows_needed = -(-total_bytes * 8 // bits_per_row)
        deep = max(1, -(-rows_needed // depth))
        count = across * deep
        plan = SramPlan(
            macro=(depth, width), across=across, deep=deep,
            area_um2=area * count,
            # 深度堆叠要过一层地址译码和输出多路选择，这里只记宏自身的访问
            # 时间；选择器的延迟在 sram.scala 里，那部分走综合。
            access_ns=access,
            leakage_mw=leak_nw * count * 1e-6,
            read_energy_pj=read_fj * across * 1e-3,
        )
        if best is None or plan.area_um2 < best.area_um2:
            best = plan
    return best


def sram_area_units(sram_bytes: int, port_width_bits: int = 64) -> float:
    """SRAM 的面积，um^2（Nangate45 的 fakeram45 宏拼装）。

    容量为 0 或位宽非法时返回 0 而不是猜一个数——0 会让约束检查在「容量
    不够」那一条上先失败，比默默给一个假面积好。
    """
    plan = plan_sram(sram_bytes, port_width_bits)
    return plan.area_um2 if plan is not None else 0.0


def sram_leakage_mw(sram_bytes: int, port_width_bits: int = 64) -> float:
    """SRAM 的漏电功耗，mW。

    不是可以忽略的项：4 KB 宏漏电 0.80 mW，256 KB 拼出来约 50 mW，
    而 RePEArray_S 综合实测是 398 mW——12%，和阵列同一个量级。
    此前的功耗模型里 SRAM 那项是 `sram_bytes * 1e-6`，256 KB 只有 0.26 mW。
    """
    plan = plan_sram(sram_bytes, port_width_bits)
    return plan.leakage_mw if plan is not None else 0.0


def sram_read_energy_pj(sram_bytes: int, port_width_bits: int = 64) -> float:
    """一次读的动态能量，pJ。"""
    plan = plan_sram(sram_bytes, port_width_bits)
    return plan.read_energy_pj if plan is not None else 0.0
