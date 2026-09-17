"""Pre-layout timing and power estimation on a mapped standard-cell netlist.

Timing acceptance requires nonnegative setup slack at the requested period.
The reported frequency estimate keeps external I/O delays fixed; it is not a
post-layout maximum frequency. Power applies one activity and duty factor
globally in OpenSTA. Even when derived from an RTL workload's average activity,
this is a uniform approximation, not per-net gate-level activity annotation.
Clock-tree, extracted interconnect and memory activity are not included here.
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


#: 没有实测活动率时用的值。
#:
#: **不是 0.2。** 0.2 是个从来没被验证过的假设，而从真实 VCD 数出来的是
#: 0.0213（AttentionTileTop 跑一个真实 tile：1710 个信号、212 周期、
#: 111,043 次翻转）——**差 9.4 倍**。
#:
#: 两个错误叠加的后果是功耗高估 8.07 倍：同一个设计，
#: `-input + α=0.2` 报 113.4 mW，`-global + α=0.0213` 报 14.05 mW。
#:
#: 这个默认值仍然是**假设**，只是换成了一个有实测依据的假设。真要用，
#: 就跑 `fast.adapters.vcd_activity.activity_from_vcd()` 数自己工作负载的。
DEFAULT_ACTIVITY = 0.0213


@dataclass(frozen=True)
class TimingResult:
    """一次 STA 跑出来的时序与功耗。"""

    success: bool
    top_module: str
    technology: str
    clock_period_ns: float
    # 关键路径的数据到达时间，ns；频率估计还需包含 setup/I/O 约束，见下方属性。
    critical_path_ns: float | None = None
    slack_ns: float | None = None
    # 全局施加的翻转率；记录它以区分不同活动率假设下的功耗估计。
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
        """Setup-aware estimate with the current external I/O delays fixed.

        Arrival alone omits setup/output delay. Acceptance must use nonnegative
        slack in a fresh STA run at the requested clock, not this estimate.
        """
        if self.slack_ns is None or not self.timing_credible:
            return None
        required_period = self.clock_period_ns - self.slack_ns
        return 1000.0 / required_period if required_period > 0 else None


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
            # 对全网使用同一个 α 的 vectorless 估计。
            # **必须是 `-global`，不是 `-input`。**
            #
            # `-input` 只设输入端口，指望 OpenSTA 把活动率传播到内部网——
            # 实测它做不到：α 从 0.02 扫到 0.9（45 倍），总功耗在
            # 0.1079-0.1183 W 之间**非单调抖动**（±5%），也就是这个旋钮对
            # 结果没有控制力。`-global` 是单调近似线性的
            # （0.0137 -> 0.0566 -> 0.2234 W）。
            #
            # 换过来在同一个 α 上把功耗改变约 2 倍，**项目此前全部功耗标定
            # 都是用 `-input` 做的**，那些锚点反映的是 OpenSTA 的默认内部
            # 活动率而不是指定值，需要重测。
            #
            # 代价：`-global` 对所有网一视同仁，忽略组合路径的衰减，会**高估**
            # 深层逻辑。消除它要门级 VCD，而当前 PDK 目录只有 `.lib`，
            # 没有 Nangate45 的 Verilog 单元模型。这个限制跟着数走。
            f"set_power_activity -global -activity {activity} -duty 0.5",
            "report_power -digits 6",
            "exit",
        ])

    def analyse(self, netlist: Path, top_module: str, *,
                period_ns: float = 2.0, activity: float = DEFAULT_ACTIVITY,
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
