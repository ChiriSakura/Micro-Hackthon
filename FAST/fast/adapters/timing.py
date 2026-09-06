"""时序与功耗：EDP 里的 delay 项和 power 项，来自工具而不是模型。

`synthesis.py` 把面积从「猜的」变成「量的」。这个适配器补上另外两项，
用的是同一个综合网表和同一次 OpenSTA 调用。

## 时序

`report_checks` 给关键路径和 slack。有了它，协同优化器的时钟周期假设
（`ArchSpecs.target_mhz` 默认 500 MHz）第一次可以被证伪——一个 slack 为负
的设计，它的 EDP 里那个 delay 项是假的。

## 功耗，以及为什么 α 是全部

功耗 = 泄漏 + 内部 + 翻转。泄漏由单元构成决定，是个常数；后两项**严格正比
于翻转率 α**。实测（ExpUnitFixPoint，Nangate45）：

    α = 0.05  ->  1.199 mW
    α = 0.20  ->  4.751 mW      (4.0x)
    α = 0.50  -> 11.854 mW     (10.0x)

泄漏全程 14.8 uW 不变。所以**用工具默认的 α 等于给出一个任意数**——更糟的
是，那个数和稀疏度完全无关，而 DynaX 省的恰恰就是翻转。拿它做协同优化，
等于让优化器看不见稀疏化的主要收益。

因此这里的 α 不是猜的，是从**实际施加的激励**里数出来的：
`activity_from_stimulus()` 数金标准向量里每个输入位每周期翻转多少次。

**当前的边界必须说清楚**：现在的激励是**验证向量**（随机控制走查、饱和
边界、平局），不是真实注意力工作负载的轨迹。所以这里的功耗是「该验证激励
下的功耗」，`fidelity` 里也这么写。要得到随稀疏配置变化的功耗，需要用真实
Q/K 数据生成激励——那是下一步，接口已经留好：`activity` 是入参。

## 精度层级

OpenSTA 支持 `read_power_activities -vcd`，可以从门级 VCD 得到每个内部节点
的真实翻转。那需要 Nangate45 的 Verilog 单元模型（当前拿不到）加上能跑
UDP 的仿真器。所以这里用 vectorless 估计：给输入端口实测的 α，由 OpenSTA
向内传播。内部节点的活动是**传播出来的，不是测出来的**，evidence 里注明。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import subprocess
import time

# report_checks 末尾的 slack 行；MET 为正、VIOLATED 为负。
_SLACK = re.compile(r"^\s*(-?[0-9.]+)\s+slack\s+\((MET|VIOLATED)\)", re.MULTILINE)
# 关键路径的到达时间。
_ARRIVAL = re.compile(r"^\s*([0-9.]+)\s+data arrival time", re.MULTILINE)
# report_power 的 Total 行：内部、翻转、泄漏、总计（瓦特）。
_POWER = re.compile(
    r"^Total\s+([0-9.e+-]+)\s+([0-9.e+-]+)\s+([0-9.e+-]+)\s+([0-9.e+-]+)",
    re.MULTILINE,
)
# 路径上每一级的增量延迟，用于合理性检查。
_STAGE = re.compile(r"^\s+([0-9.]+)\s+[0-9.]+\s+[v^]\s+\S+\s+\(([A-Z][A-Z0-9_]*)\)",
                    re.MULTILINE)

# Nangate45 的单个标准单元在正常负载下约 20-100 ps。**综合后的网表没有插过
# 缓冲**——那是布局布线干的活——所以一个广播到上千个负载的控制信号会让
# 单级延迟算出几十甚至几百 ns。
#
# 这不是设计的关键路径，是缺了缓冲的伪影。实测遇到过：PrePEArray_1_4 里一个
# NOR2_X1 报出 196 ns（真实值约 0.02 ns，差 4000 倍），起点是广播给全部 512
# 个 PE 的 io_array_state。同一次跑里 RePEArray 的 43 级路径 2.22 ns 是可信的，
# 因为它起点是低扇出的 per-PE 信号。
#
# 阈值取 1 ns：真实单元延迟离它有一个数量级的余量，而伪影通常超它几十倍。
_MAX_CREDIBLE_STAGE_NS = 1.0


@dataclass(frozen=True)
class TimingResult:
    """一次 STA 跑出来的时序与功耗。"""

    success: bool
    top_module: str
    technology: str
    clock_period_ns: float
    # 关键路径的数据到达时间，ns。最高频率由它决定，不是由 slack。
    critical_path_ns: float | None = None
    slack_ns: float | None = None
    # 施加的输入翻转率。动态功耗严格正比于它，所以它必须跟着结果走。
    activity: float | None = None
    # 路径上最慢的一级，以及它是哪个单元。用来判断这条路径可不可信：
    # 综合后没有插缓冲，高扇出网会让单级延迟离谱。
    worst_stage_ns: float | None = None
    worst_stage_cell: str = ""
    # 时序是否可信。False 意味着这条路径由扇出主导，得等布局布线插了缓冲
    # 才有意义——功耗和面积仍然可用。
    timing_credible: bool = True
    internal_power_w: float | None = None
    switching_power_w: float | None = None
    leakage_power_w: float | None = None
    total_power_w: float | None = None
    wall_seconds: float = 0.0
    log_uri: str = ""
    error: str | None = None

    @property
    def max_frequency_mhz(self) -> float | None:
        """关键路径决定的最高频率。

        用到达时间而不是 `1/(period - slack)`：后者在 slack 为正时给出的是
        「当前周期还能收紧多少」，不是电路本身的上限。
        """
        if self.critical_path_ns is None or self.critical_path_ns <= 0:
            return None
        return 1000.0 / self.critical_path_ns


def activity_from_stimulus(cases: list[dict], bits_per_field: int = 16) -> float:
    """从金标准激励里数出输入翻转率。

    α 定义为「每个输入位每周期翻转的次数」。它是这里唯一一个能让功耗随
    工作负载变化的量，所以必须从真正施加的激励里数，而不是取一个默认常数。

    Args:
        cases: 金标准 JSON 里的 cases，每个含 `input_ticks`（逐周期展平的
            输入向量）。
        bits_per_field: 每个字段按多少位计。取 16 是数据通路宽度；控制位
            按同样宽度计会稍微低估 α，但偏保守。

    Returns:
        [0, 1] 区间的翻转率。
    """
    transitions = 0
    comparisons = 0
    mask = (1 << bits_per_field) - 1

    for case in cases:
        ticks = case.get("input_ticks", [])
        if len(ticks) < 2:
            continue
        for previous, current in zip(ticks, ticks[1:]):
            # 异或后数 1 的个数，就是这一步翻转了多少位。
            transitions += bin((int(previous) ^ int(current)) & mask).count("1")
            comparisons += bits_per_field

    if comparisons == 0:
        return 0.0
    return transitions / comparisons


@dataclass
class OpenStaTimingAdapter:
    """在 Nangate45 上做 STA 与功耗分析。

    Args:
        container: OpenSTA 的 apptainer 镜像。二进制在 `/OpenSTA/build/sta`，
            不在 PATH 里——镜像的 entrypoint 直接指向它。
        liberty: 标准单元库 `.lib`。
        netlist_dir: 综合写出的映射网表所在目录。时序和功耗都必须跑在
            **映射后**的网表上，RTL 上没有单元延迟可言。
    """

    container: Path
    liberty: Path
    launcher: tuple[str, ...] = ()
    technology: str = "nangate45"
    sta_binary: str = "/OpenSTA/build/sta"
    timeout_seconds: int = 3600
    work_root: Path | None = None
    _cache: dict[tuple[str, str, float, float], TimingResult] = field(
        default_factory=dict, repr=False
    )

    def script(self, netlist: Path, top_module: str, period_ns: float,
               activity: float) -> str:
        """OpenSTA 的 Tcl。时序和功耗一次跑完，因为它们共用同一次 link。"""
        return "\n".join([
            f"read_liberty {self.liberty}",
            f"read_verilog {netlist}",
            f"link_design {top_module}",
            f"create_clock -name clk -period {period_ns} [get_ports clock]",
            # 输入输出延迟取周期的 5%：不设的话 STA 会假定 0，把 I/O 路径
            # 报得比实际乐观。
            f"set_input_delay {period_ns * 0.05} -clock clk [all_inputs -no_clocks]",
            f"set_output_delay {period_ns * 0.05} -clock clk [all_outputs]",
            "report_checks -path_delay max -digits 4",
            # 输入端口给实测 α，内部由 OpenSTA 传播——vectorless 估计。
            f"set_power_activity -input -activity {activity} -duty 0.5",
            "report_power -digits 6",
            "exit",
        ])

    def analyse(self, netlist: Path, top_module: str, *,
                period_ns: float = 2.0, activity: float = 0.2,
                label: str | None = None) -> TimingResult:
        """Args:
            label: 日志文件名用的标识。默认用 `top_module`，但同一个模块在
                不同尺寸下会重名——RePEArray_S 和 RePEArray_L 顶层都叫
                RePEArray，日志会互相覆盖，结果没法追溯到具体配置。
        """
        key = (str(netlist), top_module, period_ns, activity)
        if key in self._cache:
            return self._cache[key]

        if not Path(netlist).is_file():
            return self._fail(top_module, period_ns, f"no such netlist: {netlist}")
        if not Path(self.liberty).is_file():
            return self._fail(top_module, period_ns, f"no such liberty: {self.liberty}")

        root = Path(self.work_root) if self.work_root else Path("/tmp")
        root.mkdir(parents=True, exist_ok=True)
        name = label or top_module
        tcl = root / f"sta_{name}.tcl"
        tcl.write_text(self.script(Path(netlist), top_module, period_ns, activity),
                       encoding="utf-8")

        environment = dict(os.environ)
        environment.setdefault("APPTAINER_TMPDIR", "/tmp")

        started = time.time()
        try:
            completed = subprocess.run(
                [*self.launcher, "apptainer", "exec", str(self.container),
                 self.sta_binary, "-no_splash", "-exit", str(tcl)],
                capture_output=True, text=True,
                timeout=self.timeout_seconds, env=environment,
            )
        except subprocess.TimeoutExpired:
            return self._fail(top_module, period_ns,
                              f"STA exceeded {self.timeout_seconds}s",
                              time.time() - started)

        elapsed = time.time() - started
        text = completed.stdout + completed.stderr
        log_uri = self._save_log(name, text)

        arrival = _ARRIVAL.search(text)
        power = _POWER.search(text)
        if completed.returncode != 0 or arrival is None:
            tail = (text.strip().splitlines() or ["(no output)"])[-1][:200]
            result = self._fail(
                top_module, period_ns,
                f"STA produced no timing (rc={completed.returncode}): {tail}",
                elapsed, log_uri,
            )
            self._cache[key] = result
            return result

        slack_match = _SLACK.search(text)
        stages = [(float(d), cell) for d, cell in _STAGE.findall(text)]
        worst = max(stages, default=(0.0, ""))
        credible = worst[0] <= _MAX_CREDIBLE_STAGE_NS

        result = TimingResult(
            success=True,
            top_module=top_module,
            technology=self.technology,
            clock_period_ns=period_ns,
            critical_path_ns=float(arrival.group(1)),
            slack_ns=float(slack_match.group(1)) if slack_match else None,
            activity=activity,
            worst_stage_ns=worst[0] or None,
            worst_stage_cell=worst[1],
            timing_credible=credible,
            internal_power_w=float(power.group(1)) if power else None,
            switching_power_w=float(power.group(2)) if power else None,
            leakage_power_w=float(power.group(3)) if power else None,
            total_power_w=float(power.group(4)) if power else None,
            wall_seconds=elapsed,
            log_uri=log_uri,
            error=None if credible else (
                f"时序不可信：单级 {worst[1]} 报出 {worst[0]:.3f} ns，"
                f"而 45nm 标准单元约 0.02-0.1 ns。这条路径由未插缓冲的高扇出"
                f"主导，要等布局布线才有意义。面积与功耗不受影响。"
            ),
        )
        self._cache[key] = result
        return result

    def _fail(self, top_module: str, period_ns: float, error: str,
              elapsed: float = 0.0, log_uri: str = "") -> TimingResult:
        return TimingResult(
            success=False, top_module=top_module, technology=self.technology,
            clock_period_ns=period_ns, wall_seconds=elapsed,
            log_uri=log_uri, error=error,
        )

    def _save_log(self, top_module: str, text: str) -> str:
        if self.work_root is None:
            return ""
        root = Path(self.work_root)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"sta_{top_module}.log"
        path.write_text(text, encoding="utf-8")
        return path.as_uri()
