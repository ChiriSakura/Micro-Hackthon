"""跑真实工具链的门：elaborate -> 金标准 TB -> 综合。

## 模块登记表和 slurm 脚本必须是同一份

`slurm/rtl/fast_rtl_verify_all.slurm` 里有一张同样的表（target | 顶层模块 |
testbench | gen_golden 参数 | gen_ports 参数）。两处各写一份，迟早分叉——
而分叉的后果是「内循环判它过了」而「批量验证判它没过」，两个结论都看起来
正常。所以这里是唯一定义，slurm 脚本应当从这里生成。

## 内循环只有两级；综合不在里面

    elaborate    语法与类型。最便宜，先跑。
    金标准 TB    功能。**「能 elaborate、lint 干净」正是绝不能当作通过的
                 那个状态**——DynaX 的 6 个缺陷里有 2 个就是 lint 干净、
                 只有仿真才暴露的。

**综合默认关闭**（`synthesise=False`），三个理由：

1. **yosys 综合不了 SRAM。** `SyncReadMem` 被映射成 226,703 个触发器、
   530,247 um^2——KeyFeeder 那 27 万 um^2 里绝大部分是那个假存储。带存储的
   模块在这里拿到的面积**本身就没有意义**。最终 PPA 要走 hammer，它的
   nangate45 plugin 映射到 fakeram45 宏。
2. **成本。** 综合每模块几分钟，而内循环是「最多 3 次尝试 x N 个模块」。
3. **职责。** 内循环回答「这份 RTL 能不能用」，那是**正确性**问题。
   时序和面积是**有效性**问题，属于症状检查——由 Critic 派发变异时给出的
   可检验目标来触发，跑在内循环外面。

会因此漏掉什么，要说清楚：线性 reduce 链那个 bug（19.0 ns）**elaborate 和
仿真全过，只有综合报得出来**。所以症状是时序时，症状检查必须开综合
（`synthesise=True`）——它不是可选的，只是不在内循环里。
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

from fast.agents.rtl_mutation import (
    INFRA_PREFIX as _INFRA,
    GateResult,
    contains_word,
)


@dataclass(frozen=True)
class ModuleSpec:
    """一个模块怎么 elaborate、怎么仿真。

    和 `slurm/rtl/fast_rtl_verify_all.slurm` 的 MODULES 表一一对应。
    """

    target: str          # Elaborate.scala 里的目标名
    top: str             # 生成的 Verilog 顶层模块名
    testbench: str       # tb/ 下的 .cpp
    golden_args: tuple[str, ...] = ()
    ports_args: tuple[str, ...] = ()
    sim_args: tuple[str, ...] = ()
    # 这个模块的 Chisel 源文件，相对 `chisel/src/main/scala/`。
    #
    # µArch 的 RTL 变异需要它：`RtlMutator` 要知道改哪个文件。**只有登记了
    # 源文件、而且这张表里有门的模块才允许被变异**——变异的全部价值在于有一个
    # 机械的门来判它能不能用，没有门的改写等于无验证地生成 RTL。
    source: str = ""

    # 有些模块的参照不是「金标准 JSON」而是**真实工作量的激励**
    # （BlockScheduler / KeyFeeder：它们的正确性判据是队列/取数协议在真实
    # 稀疏索引流上的行为，不是一个逐点的数值表）。给了这个就用
    # `golden/gen_workload_stimulus.py` 生成 argv[1]，而不是 `gen_golden.py`。
    stimulus_args: tuple[str, ...] = ()

    # 这个模块**必须保证**的东西，写给改它的模型看。
    #
    # 不写的后果实测过：LLM 三次改写 BlockScheduler 想缩短关键路径，三次都
    # 丢了工作（23760 个保留列只发出 19160 个）。门每次都抓住了，但模型是在
    # 猜这个模块的契约——而契约是设计文档，不是测试内部，本来就该告诉它。
    #
    # **只写不变量，不写 testbench 怎么实现这些检查**：前者是它需要的信息，
    # 后者会诱导它去迎合具体断言。
    contract: str = ""

    #: 这个模块在 Critic 的自然语言里可能被叫成什么。用来把一条
    #: `uarch.<字段>` 变异解析到具体模块——**按内容匹配，不按字段名白名单**
    #: （字段名是模型自由发挥的部分，同一次运行里就出现过两个写法）。
    aliases: tuple[str, ...] = ()


MODULES: dict[str, ModuleSpec] = {
    spec.target: spec
    for spec in (
        ModuleSpec("TopK", "TopK", "tb_topk.cpp", sim_args=("16",),
                   source="predict_unit/topk.scala",
                   contract="""- The block's top-n values must come out in the same order and with the same
  tie-breaking as today. `runnerUpReg` must not be cleared in the same cycle a
  pulse `valid` is forwarding it (that bug dropped the last element of every
  m-wide block and shifted the rest up by one).""",
                   aliases=("topk", "top-k", "top k", "selection", "comparator")),
        ModuleSpec("ExpUnit", "ExpUnitFixPoint", "tb_exp.cpp", ("--module", "ExpUnit"),
                   source="exp_unit/exp_unit.scala",
                   aliases=("exp", "expunit", "exp unit", "exponential")),
        ModuleSpec("PSumSoftmax", "PSumSoftmax", "tb_psum_softmax.cpp",
                   ("--module", "PSumSoftmax"),
                   source="predict_unit/psum_softmax.scala",
                   aliases=("psum", "partial sum", "softmax", "normaliser", "normalizer")),
        ModuleSpec("SRAM", "SRAM", "tb_sram.cpp", ("--module", "SRAM"),
                   source="execute_unit/sram.scala",
                   contract="""- `SyncReadMem` reads one cycle late. The bank multiplexer must select on the
  REGISTERED address (`RegNext(bankAddr)`), not the current one -- selecting on
  the current address returns the wrong bank's data on every crossing read.""",
                   aliases=("sram", "sram bank", "bank conflict")),
        ModuleSpec("Divider", "FixedPointDiv", "tb_divider.cpp",
                   ("--module", "Divider", "--stages", "8"),
                   ("--module", "Divider", "--stages", "8"),
                   source="predict_unit/divider.scala",
                   contract="""- Integer division truncates TOWARD ZERO, not toward -inf. The pipeline depth
  sets the output latency and the testbench expects exactly that latency.""",
                   aliases=("divider", "division", "divide", "reciprocal",
                            "divider_stages", "quotient")),
        ModuleSpec("RePE", "RePE", "tb_repe.cpp", ("--module", "RePE"),
                   source="execute_unit/repe.scala",
                   contract="""- Same numerics, bit for bit: Q8.8 with round-to-nearest on the product
  (`(a*b + (1 << (point-1))) >> point`). Plain truncation is FLOOR in two's
  complement -- its error is never positive and accumulates linearly with
  head_dim (measured -29.8 ticks at head_dim=64).
- The accumulator WRAPS on overflow; it must not saturate.""",
                   aliases=("repe", "mac", "multiplier", "accumulator",
                            "execution array", "execute unit")),
        ModuleSpec("RePERow", "RePERow", "tb_repe_row.cpp",
                   ("--module", "RePERow", "--pe-count", "8", "--reg-width", "8"),
                   source="execute_unit/repe_row.scala",
                   aliases=("repe row", "reperow")),
        ModuleSpec("RePEArray_T", "RePEArray", "tb_repe_array.cpp",
                   ("--module", "RePEArray", "--num-rows", "4", "--pe-count", "2",
                    "--reg-width", "4"),
                   ("--module", "RePEArray", "--rows", "4", "--pes", "2",
                    "--reg-width", "4"),
                   source="execute_unit/repe_array.scala",
                   aliases=("repe array", "execute array", "systolic")),
        ModuleSpec("BlockSched_S4", "BlockScheduler", "tb_block_scheduler.cpp",
                   ports_args=("--module", "BlockScheduler", "--rows", "32",
                               "--pes", "4", "--queue-depth", "4", "--col-bits", "6"),
                   stimulus_args=("--method", "xm", "--pe", "4", "--max-tiles", "64"),
                   source="predict_unit/block_scheduler.scala",
                   contract="""- WORK CONSERVATION is absolute: the number of busy PE-cycles the hardware
  counts must EXACTLY equal the total number of kept columns fed in. Dropping
  work, double-issuing work, or ending early all violate it. A rewrite that
  shortens the critical path but loses even one pass is rejected.
- Every row's passes must all be enqueued; the queue must drain within the
  cycle budget.
- At queue_depth = 0 the utilisation must equal 1/imbalance. That is the
  definition of strict lock-step, and it anchors every deeper measurement.
- The producer enqueues each row's work in tile order, at most one pass per row
  per cycle, and stalls when the queue is full. That stall IS the mechanism the
  depth limit models -- do not remove it to go faster.""",
                   aliases=("blockscheduler", "block scheduler", "scheduler",
                            "queue", "work queue", "queue_depth", "queue depth",
                            "load balancing", "load balance")),
        ModuleSpec("KeyFeeder_B32", "KeyFeeder", "tb_key_feeder.cpp",
                   ports_args=("--module", "KeyFeeder", "--rows", "32", "--pes", "4",
                               "--banks", "32", "--col-bits", "6"),
                   stimulus_args=("--method", "xm", "--pe", "4", "--max-tiles", "64"),
                   source="execute_unit/key_feeder.scala",
                   contract="""- Every requested column must be delivered exactly once, to the right lane.
  A rewrite that drops or reorders deliveries is rejected however fast it is.
- Banks are addressed independently; a conflict costs a cycle. Hashing the bank
  index to break stride aliasing was tried and measured as a REGRESSION.""",
                   aliases=("keyfeeder", "key feeder", "gather", "gather engine",
                            "bank_count", "bank count")),
        ModuleSpec("PrePE_1_2", "PrePE_1_2", "tb_prepe.cpp",
                   ("--module", "PrePE", "--out-bits", "12"),
                   source="predict_unit/prepe_1_2.scala",
                   aliases=("prepe", "predict", "predictor", "approximate")),
        ModuleSpec("PrePEArray_T", "PrePEArray_1_2", "tb_prepe_array.cpp",
                   ("--module", "PrePEArray", "--height", "2", "--width", "8",
                    "--out-bits", "12"),
                   ("--module", "PrePEArray_1_2", "--height", "2", "--width", "8")),
        ModuleSpec("PrePEArray14_T", "PrePEArray_1_4", "tb_prepe_array14.cpp",
                   ("--module", "PrePEArray14", "--height", "2", "--width", "8",
                    "--out-bits", "15"),
                   ("--module", "PrePEArray_1_4", "--height", "2", "--width", "8")),
    )
}



def mutable_modules() -> dict[str, ModuleSpec]:
    """允许被 µArch 变异的模块：**登记了源文件、而且这张表里有门的**。

    变异的全部价值在于有一个机械的门来判改写能不能用。没有门的模块被改写，
    等于无验证地生成 RTL——那正是这个项目从一开始就拒绝的东西。
    """
    return {name: spec for name, spec in MODULES.items() if spec.source}


def resolve_module(text: str, *, subject: str = "") -> tuple[str | None, str]:
    """把 Critic 的一条 µArch 变异解析到具体模块。返回 (模块名, 说明)。

    `subject` 是**变异自己说的话**（字段 + 值），`text` 是连同 Critic 那句
    解释一起的全文。前者优先——因为后者经常拿别的模块作对比：实测的那句
    「the queue's 2.528 ns critical path, which is slower than the **execution
    array**'s 2.230 ns」里，"execution array" 比 "queue" 长，只按最长别名
    打分就会去改 RePE，而要改的是队列。**主语在变异里，对比对象在叙述里。**

    **按内容匹配，不按字段名白名单。** 字段名是模型自由发挥的部分——同一个
    模型在同一次运行里就发过 `uarch.queue` 和 `uarch.queue_rtl`，之前按
    kernel 层字段名白名单也正是这么漏掉过一个完全正确的动作。所以这里把
    变异的字段、值和 Critic 的那句话拼在一起，去撞每个模块的别名。

    匹配不到就返回 None **并说明为什么**，不猜一个模块：改错文件会让门在
    一个和症状无关的地方失败，而那种错很难从结果里看出来。
    """
    haystack = " ".join(str(text or "").lower().split())
    if not haystack:
        return None, "变异没有可解析的文字"

    # **按词边界匹配，不是子串。** 子串匹配在短别名上必然误配：`pe` 命中
    # 「pi**pe**line」和「**pe**riod」，于是一条关于工作队列的变异被解析成
    # 「改 RePE」。改错文件会让门在一个和症状无关的地方失败。
    focus = " ".join(str(subject or "").lower().split())

    best: tuple[tuple[int, int], str, str] | None = None
    for name, spec in mutable_modules().items():
        for alias in (name.lower(), *(a.lower() for a in spec.aliases)):
            if not alias:
                continue
            in_focus = bool(focus and contains_word(focus, alias))
            if not in_focus and not contains_word(haystack, alias):
                continue
            # 先比「是不是出现在变异自己的字段/值里」，再比别名长度。
            score = (1 if in_focus else 0, len(alias))
            if best is None or score > best[0]:
                best = (score, name, alias)
    if best is None:
        known = ", ".join(sorted(mutable_modules()))
        return None, (
            f"这条变异指不到任何一个**有门的**模块（可变异的是 {known}）。"
            f"原文：{haystack[:160]}"
        )
    where = "变异字段" if best[0][0] else "症状叙述"
    return best[1], f"按{where}里的「{best[2]}」匹配到 {best[1]}"


class LocalRtlGate:
    """在本机跑三级门。

    工具全部走 apptainer 容器，和 slurm 脚本用的是同一批镜像——门在两处
    给出不同结论是这个设计里最难查的一类问题，所以工具版本不能有第二个来源。
    """

    def __init__(
        self,
        *,
        repo: Path,
        work_root: Path,
        containers: Path,
        python: str,
        liberty: Path | None = None,
        # 默认关闭。见模块 docstring：yosys 综合不了 SRAM，而且内循环要的是
        # 正确性不是 PPA。症状是时序/面积时由症状检查开启。
        synthesise: bool = False,
        # BlockScheduler / KeyFeeder 的参照是**真实工作量的激励**，不是逐点的
        # 金标准表。没配这个的话它们的门明确失败（「没验证」），不会静默通过。
        workload: Path | None = None,
        # 给了就在综合之后跑 STA。症状是关键路径时，没有它的门**测不到**
        # 这条变异的目标。
        sta_container: Path | None = None,
        clock_period_ns: float = 2.0,
        timeout_seconds: int = 1800,
        env: dict[str, str] | None = None,
    ):
        self.repo = Path(repo)
        self.hardware = self.repo / "FAST" / "hardware"
        self.work_root = Path(work_root)
        self.containers = Path(containers)
        self.python = python
        self.liberty = liberty
        self.synthesise = synthesise
        self.workload = Path(workload) if workload else None
        self.sta_container = Path(sta_container) if sta_container else None
        self.clock_period_ns = clock_period_ns
        self.timeout_seconds = timeout_seconds
        self.env = {**os.environ, **(env or {})}

    def check(self, module_path: Path, target: str) -> tuple[GateResult, ...]:
        spec = MODULES.get(target)
        if spec is None:
            return (GateResult(
                "elaborate", False,
                f"{target} has no module spec; add it to fast/agents/rtl_gate.py "
                f"and to slurm/rtl/fast_rtl_verify_all.slurm together",
            ),)

        work = self.work_root / target
        work.mkdir(parents=True, exist_ok=True)
        results: list[GateResult] = []

        elaborated = self._elaborate(spec, work)
        results.append(elaborated)
        if not elaborated.passed:
            return tuple(results)

        simulated = self._simulate(spec, work)
        results.append(simulated)
        if not simulated.passed:
            return tuple(results)

        if self.synthesise and self.liberty is not None:
            results.append(self._synthesise(spec, work))
        return tuple(results)

    # -- 三级 --------------------------------------------------------------

    def _elaborate(self, spec: ModuleSpec, work: Path) -> GateResult:
        out = work / "rtl"
        # `--workspace` 指到本次的工作目录：不指的话 scala-cli 编译进仓库里的
        # `chisel/.scala-build`，几个并发的 gate/作业会互相踩，表现是随机一个
        # 报 `FAIL: <某个模块>` 而串行重跑全过——看起来像 RTL 坏了。
        done = self._run(
            ["scala-cli", "run", "chisel", "--server=false",
             "--workspace", str(work / "scala-build"),
             "--main-class", "Elaborate", "--", f"LIST:{spec.target}", str(out)],
            cwd=self.hardware,
        )
        verilog = out / spec.target / f"{spec.top}.v"
        if verilog.is_file() and not elaborated_tool_failed(done):
            return GateResult("elaborate", True, "ok")
        # Chisel 的错误已经带了文件名和行号，是最可行动的一类反馈——
        # 原样传回去，不要摘要。
        return GateResult("elaborate", False, _tail(done, 40))

    def _simulate(self, spec: ModuleSpec, work: Path) -> GateResult:
        # 参照有两种形状：逐点的金标准 JSON，和真实工作量的激励。两者都作为
        # argv[1] 传给 testbench，所以下游完全一样。
        # 「门自己跑不起来」和「变异没过门」是两回事。前者重试多少次都一样，
        # 而每次重试都是一次真实的 LLM 调用——实测浪费过 6 次：门用的解释器
        # 没有 torch，`gen_golden.py` 每次都以同一个 ImportError 失败。
        if spec.stimulus_args:
            golden = work / "stimulus.txt"
            if self.workload is None:
                return GateResult("simulate", False, (
                    f"{spec.target} 的参照是真实工作量的激励，但这个门没有配置 "
                    f"workload——传 LocalRtlGate(workload=...)，或先跑 "
                    f"slurm/kernel/dynax_capture_workload.slurm。"
                    f"{_INFRA}**不要把它当成通过**：这是没验证，不是验证过了。"))
            if not self.workload.is_file():
                return GateResult("simulate", False, f"{_INFRA}找不到工作量 {self.workload}")
            made = self._run(
                [self.python, str(self.hardware / "golden" / "gen_workload_stimulus.py"),
                 "--workload", str(self.workload), "--out", str(golden),
                 *spec.stimulus_args],
                cwd=self.hardware, extra_env={"PYTHONPATH": str(self.hardware)},
            )
            if not golden.is_file():
                return GateResult("simulate", False, f"{_INFRA}激励生成失败: {_tail(made, 20)}")
        else:
            golden = work / "golden.json"
            made = self._run(
                [self.python, str(self.hardware / "gen_golden.py"), "--out", str(golden),
                 *spec.golden_args],
                cwd=self.hardware, extra_env={"PYTHONPATH": str(self.hardware)},
            )
            if not golden.is_file():
                return GateResult("simulate", False, f"{_INFRA}golden model failed: {_tail(made, 20)}")

        if spec.ports_args:
            self._run(
                [self.python, str(self.hardware / "tb" / "gen_ports.py"),
                 "--out", str(work / "array_ports.h"), *spec.ports_args],
                cwd=self.hardware,
            )
        for name in (spec.testbench, "golden.h", "drivers.h"):
            source = self.hardware / "tb" / name
            if source.is_file():
                (work / name).write_bytes(source.read_bytes())

        verilog = work / "rtl" / spec.target / f"{spec.top}.v"
        build = self._run(
            ["apptainer", "exec", str(self.containers / "verilator.sif"), "verilator",
             "--cc", "--exe", "--build", "--assert", "-j", "4", "-Wno-fatal",
             "--top-module", spec.top, "-CFLAGS", f"-I{work}",
             str(verilog), spec.testbench, "-o", f"tb_{spec.target}"],
            cwd=work,
        )
        binary = work / "obj_dir" / f"tb_{spec.target}"
        if not binary.exists() or elaborated_tool_failed(build):
            return GateResult("simulate", False, f"verilator build failed: {_tail(build, 30)}")

        run = self._run(
            ["apptainer", "exec", str(self.containers / "verilator.sif"), str(binary),
             str(golden), *spec.sim_args],
            cwd=work,
        )
        if re.search(r"^PASSED", run, re.M) and not elaborated_tool_failed(run):
            measurements = {}
            for line in run.splitlines():
                if line.startswith("MEASURE "):
                    measurements.update({key: float(value) for key, value in
                                         re.findall(r"(\w+)=([0-9.eE+-]+)", line)})
            return GateResult("simulate", True, _head_and_tail(run, 10, 10), measurements)
        # 失配的具体内容就是最有价值的反馈——testbench 打的是槽位、周期、
        # 期望值和实际值，模型靠它定位。全部传回去。
        return GateResult("simulate", False, _head_and_tail(run, 25, 20))

    def _synthesise(self, spec: ModuleSpec, work: Path) -> GateResult:
        """综合走 `YosysSynthesisAdapter`，**不要在这里再写一份 yosys 脚本**。

        我第一版就是自己写的，立刻踩了两个坑：漏了 `opt_clean`，以及只匹配
        「Chip area for **top** module」——而**扁平设计里 yosys 根本不写
        "top"**，ExpUnit 于是被报成「没有面积」，尽管同一个模块在
        `synthesize_modules.py` 里明明拿到过 625.9 um^2。

        适配器里还有两道被咬出来的守卫：面积必须取顶层那一行（取第一个匹配
        会拿到最深的子模块，RePEArray_L 曾被报成 625.9），以及 um^2/单元 的
        下限检查。同一件事两处实现必然分叉，而这里分叉的后果是「门说不过」
        而「批量综合说过」。
        """
        from fast.adapters.synthesis import YosysSynthesisAdapter

        verilog = work / "rtl" / spec.target / f"{spec.top}.v"
        adapter = YosysSynthesisAdapter(
            container=self.containers / "yosys.sif",
            liberty=self.liberty,
            timeout_seconds=self.timeout_seconds,
            work_root=work / "synth",
        )
        netlist = work / "synth" / f"{spec.target}.mapped.v"
        # 目录要先建：yosys 的 `write_verilog` 不会替你造父目录，报的是
        # 「Can't open output file ... No such file or directory」——看起来
        # 像综合失败，其实是路径问题。
        netlist.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = adapter.synthesize(verilog, spec.top, netlist)
        except Exception as exc:
            return GateResult("synthesize", False, f"{type(exc).__name__}: {exc}")
        if not result.success or result.cell_area_um2 is None:
            return GateResult("synthesize", False, result.error or "yosys produced no area")

        metrics = {"area_um2": result.cell_area_um2, "cells": float(result.cell_count or 0)}

        # **时序也要量。** 症状是关键路径时（实测就是：「queue 的 2.528 ns
        # 限制了时钟」），只有面积的门**测不到这条变异的目标**——模型被要求
        # 改进一个门无法观察的数，改完也说不出有没有用。
        #
        # 拿不到 STA 就明说没测，不要让「没有时序数」看起来像「时序没问题」。
        timing_note = ""
        if self.sta_container is not None and netlist.is_file():
            from fast.adapters.timing import OpenStaTimingAdapter

            try:
                timing = OpenStaTimingAdapter(
                    container=self.sta_container, liberty=self.liberty,
                    work_root=work / "sta", timeout_seconds=self.timeout_seconds,
                ).analyse(netlist, spec.top, label=spec.target,
                          period_ns=self.clock_period_ns)
            except Exception as exc:  # noqa: BLE001 - 时序拿不到不该让整个门失败
                timing_note = f"; 时序未测（{type(exc).__name__}: {exc}）"
            else:
                # Component power under the adapter's uniform activity assumption;
                # not workload-annotated or whole-accelerator power.
                if timing.success and timing.total_power_w is not None:
                    metrics['estimated_power_mw'] = timing.total_power_w * 1000
                    if timing.activity is not None:
                        metrics['assumed_activity'] = timing.activity
                if timing.success and timing.timing_credible and timing.critical_path_ns:
                    metrics["critical_path_ns"] = timing.critical_path_ns
                    metrics["sta_period_ns"] = timing.clock_period_ns
                    if timing.slack_ns is not None:
                        metrics["slack_ns"] = timing.slack_ns
                    if timing.max_frequency_mhz is not None:
                        metrics["max_frequency_mhz"] = timing.max_frequency_mhz
                # 时序可信性守卫在适配器里：单级延迟离谱的结果是扇出伪影，
                # 当成测量会让模型去优化一个不存在的问题。
                if not timing.timing_credible:
                    timing_note = (
                        f"; 时序不可信（{timing.worst_stage_cell} "
                        f"{timing.worst_stage_ns} ns，扇出伪影）")
        elif self.sta_container is not None:
            timing_note = "; 时序未测（综合没有写出网表）"

        summary = ", ".join(f"{k}={v:,.3f}" for k, v in metrics.items())
        return GateResult("synthesize", True, f"ok: {summary}{timing_note}", metrics)

    # -- 执行 --------------------------------------------------------------

    def _run(self, command: list[str], *, cwd: Path,
             extra_env: dict[str, str] | None = None) -> str:
        try:
            done = subprocess.run(
                command, cwd=str(cwd), capture_output=True, text=True,
                timeout=self.timeout_seconds,
                env={**self.env, **(extra_env or {})},
            )
        except subprocess.TimeoutExpired:
            return f"[tool-error] timed out after {self.timeout_seconds}s: {' '.join(command[:4])}"
        except FileNotFoundError as exc:
            return f"[tool-error] tool not found: {exc}"
        prefix = f"[tool-error] exit={done.returncode}\n" if done.returncode else ""
        output = f"{prefix}{done.stdout}\n{done.stderr}"
        # Logs are part of the evidence even when a gate passes.
        with (cwd / "tool_commands.log").open("a", encoding="utf-8") as log:
            log.write(f"argv={command!r}\n{output}\n")
        return output


def elaborated_tool_failed(output: str) -> bool:
    return output.startswith("[tool-error]")


def _tail(text: str, lines: int) -> str:
    """留末尾若干行——给工具链的错误用。

    编译器和综合器的输出前面大多是下载与编译噪声，**错误在末尾**。
    """
    kept = [line for line in text.splitlines() if line.strip()]
    return "\n".join(kept[-lines:])


def _head_and_tail(text: str, head: int, tail: int) -> str:
    """首尾都留——给仿真失败用。

    只留末尾会丢掉**第一处分歧**，而那通常是最有信息量的一条：后面的失配
    大多是它的连锁反应。实测的一个例子：

        MISMATCH ramp[0]: rtl_idx=0 (value=-256) golden_idx=63 (value=256)
        ramp         FAIL (0/16 lanes matched)
        zeros        pass (16/16 lanes matched)
        ties         pass (16/16 lanes matched)

    第一行给出具体的槽位与值，后三行的**模式**（排序用例全挂、非排序用例
    全过）把 bug 定位到比较逻辑。两端都要，中间可以丢。
    """
    kept = [line for line in text.splitlines() if line.strip()]
    if len(kept) <= head + tail:
        return "\n".join(kept)
    dropped = len(kept) - head - tail
    return "\n".join(kept[:head] + [f"... ({dropped} lines elided) ..."] + kept[-tail:])
