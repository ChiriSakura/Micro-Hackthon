"""综合：把面积从「一阶模型猜的」变成「工具量的」。

`analytical.py` 的面积是 `codesign.py` 里的一阶公式算出来的——乘法器面积按
bits² 缩放之类。那个模型能排序，但它没有任何东西校准过：一个把面积算错 3 倍
的公式，在 Pareto 前沿上看起来和正确的公式一模一样。这个适配器跑真实综合，
给出可以校准它的数字。

**它测的不是论文的 28nm。** DynaX 报的是 28nm 商业工艺，我们没有那个 PDK。
这里用 Nangate45（开源 45nm 预测库），所以：

  * 绝对面积**不能**和论文的 1.08 / 6.05 mm² 比
  * 设计之间的**相对**面积可以比，而这正是协同优化器需要的
  * `fidelity` 标为 `L2-synthesis-nangate45`，工艺名写进标签里，
    避免下游把它当成 28nm 数据

调用路径经 CHIA（`fast/runtime/chia_nodes.py:synthesis_node`），所以同一段
代码可以落在本地、Slurm 计算节点或 GCP worker 上——综合是 CPU 密集且彼此
独立的，正是 CHIA 的资源路由该管的事。

为什么不是 hammer：CHIA 提供了 `HammerNode`（`chia/vlsi/hammer.py`），
hammer-vlsi 1.2.0 也确实自带 `synthesis.yosys` 和 `technology.nangate45`。
但那个组合当前跑不通——hammer 自带的 `nangate45.tech.json` 过不了 hammer
**自己的** pydantic 校验：`grid_unit` 是顶层键而校验器要求它在每个 metal 里，
补上之后又卡在 `max_width 1073741.8235 is not aligned to the grid unit`。
两处都在上游，不在我们的配置里。所以这里直接驱动 yosys；等有了可用的 PDK
和 tech plugin，`HammerNode` 是原位替换。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import subprocess
import time

# 层次化设计里 `stat -liberty` 会**逐个子模块**打印面积，最后才打印顶层总和：
#
#     Chip area for module '\ExpUnitFixPoint': 625.898000      <- 子模块
#     Chip area for module '\RePE': 2210.194000                <- 子模块
#     Chip area for top module '\RePEArray': 1591880.192000    <- 总和
#
# 只认「top module」那一行。取第一个匹配会拿到最深的子模块——RePEArray_L 因此
# 一度被报成 625.9 um^2（那是 ExpUnitFixPoint 的面积），而它真实是 1.59 mm^2。
_TOP_AREA = re.compile(r"Chip area for top module '\\?([^']+)': ([0-9.]+)")
# 退路：设计是扁平的（没有子模块）时 yosys 不写 "top"。
_ANY_AREA = re.compile(r"Chip area for module '\\?([^']+)': ([0-9.]+)")
# 单元总数；取最后一次 stat，即 abc 映射之后、顶层那一段。
_CELLS = re.compile(r"Number of cells:\s+(\d+)")

# Nangate45 的标准单元大致在 0.5-6 um^2；一个「面积/单元数」远低于此的结果
# 说明两个数字来自不同的模块段，不是一次可信的测量。这道检查是被上面那个
# 提取错误咬过之后加的——它当时给出的是 226703 个单元、311.8 um^2。
_MIN_UM2_PER_CELL = 0.2


@dataclass(frozen=True)
class SynthesisResult:
    """一次综合跑出来的东西。"""

    success: bool
    top_module: str
    technology: str
    cell_area_um2: float | None
    cell_count: int | None
    # 单元名 -> 个数。看得出面积花在哪：ExpUnitFixPoint 的 XNOR2/XOR2 占比高，
    # 因为它的关键路径是那个乘法器。
    cell_histogram: dict[str, int] = field(default_factory=dict)
    # 映射后的网表路径，如果要求写出的话。时序与功耗分析的输入。
    netlist_uri: str = ""
    wall_seconds: float = 0.0
    log_uri: str = ""
    error: str | None = None


@dataclass
class YosysSynthesisAdapter:
    """在 Nangate45 上综合一个模块，返回真实的单元面积。

    Args:
        container: yosys 的 apptainer 镜像。项目里和 `verilator.sif` 并列
            放在同一个 containers 目录，理由一样——集群上没有 root，
            容器是唯一能拿到自带 abc 的真实 yosys 的方式。
            （`yowasp-yosys` 装得上但用不了：WASI 起不了外部进程，
            综合会在 ABC 那一步静默停下并返回 0。）
        liberty: 标准单元库 `.lib` 的路径。
        launcher: 如何执行。默认直接调 apptainer；传
            `("srun", "-n1")` 之类可以丢给调度器。
    """

    container: Path
    liberty: Path
    launcher: tuple[str, ...] = ()
    technology: str = "nangate45"
    timeout_seconds: int = 3600
    work_root: Path | None = None
    _cache: dict[tuple[str, str], SynthesisResult] = field(
        default_factory=dict, repr=False
    )

    def script(self, verilog: Path, top_module: str,
               netlist_out: Path | None = None) -> str:
        """yosys 脚本。分成四步而不是一句 `synth`，因为顺序有讲究。

        `synth` 自己会跑一次 abc，但那是映射到通用门的；要拿到标准单元面积，
        必须在它之后再用 liberty 重新做时序映射，`dfflibmap` 先把触发器
        映射掉，否则 abc 会把它们留成通用 `$_DFF_`，最后的 `stat -liberty`
        就少算了一大块面积。
        """
        steps = [
            f"read_verilog {verilog}",
            f"synth -top {top_module}",
            f"dfflibmap -liberty {self.liberty}",
            f"abc -liberty {self.liberty}",
            "opt_clean",
            f"stat -liberty {self.liberty}",
        ]
        if netlist_out is not None:
            # 时序和功耗都必须跑在映射后的网表上——RTL 上没有单元延迟可言。
            # 写在 stat 之后，这样面积报的和 STA 读的是同一份网表。
            steps.append(f"write_verilog -noattr {netlist_out}")
        return "; ".join(steps)

    def synthesize(self, verilog: Path, top_module: str,
                   netlist_out: Path | None = None) -> SynthesisResult:
        key = (str(verilog), top_module)
        if key in self._cache:
            return self._cache[key]

        if not Path(verilog).is_file():
            return self._fail(top_module, f"no such Verilog: {verilog}", 0.0)
        if not Path(self.liberty).is_file():
            return self._fail(top_module, f"no such liberty: {self.liberty}", 0.0)

        environment = dict(os.environ)
        # VAST 装不下 apptainer 的解包临时文件（system.nfs4_dacl 删不掉），
        # 和 verilator 那条流程踩过同一个坑。
        environment.setdefault("APPTAINER_TMPDIR", "/tmp")

        started = time.time()
        try:
            completed = subprocess.run(
                [*self.launcher, "apptainer", "exec", str(self.container),
                 "yosys", "-p", self.script(Path(verilog), top_module, netlist_out)],
                capture_output=True, text=True,
                timeout=self.timeout_seconds, env=environment,
            )
        except subprocess.TimeoutExpired:
            return self._fail(
                top_module, f"synthesis exceeded {self.timeout_seconds}s",
                time.time() - started,
            )

        elapsed = time.time() - started
        text = completed.stdout + completed.stderr
        log_uri = self._save_log(top_module, text)

        area = _TOP_AREA.search(text) or _last(_ANY_AREA, text)
        if completed.returncode != 0 or area is None:
            tail = (text.strip().splitlines() or ["(no output)"])[-1][:200]
            result = self._fail(
                top_module, f"yosys produced no area (rc={completed.returncode}): {tail}",
                elapsed, log_uri,
            )
            self._cache[key] = result
            return result

        counts = _CELLS.findall(text)
        # 最后一次 stat 才是映射到标准单元之后的顶层那一段；前面那些是子模块
        # 和通用门。
        cell_count = int(counts[-1]) if counts else None
        cell_area = float(area.group(2))

        if cell_count and cell_area / cell_count < _MIN_UM2_PER_CELL:
            result = self._fail(
                top_module,
                f"面积与单元数不自洽：{cell_area:.1f} um^2 / {cell_count} 单元 = "
                f"{cell_area / cell_count:.4f} um^2 每单元，低于 {_MIN_UM2_PER_CELL}。"
                f"两个数字多半来自不同的模块段。",
                elapsed, log_uri,
            )
            self._cache[key] = result
            return result

        result = SynthesisResult(
            success=True,
            top_module=top_module,
            technology=self.technology,
            cell_area_um2=cell_area,
            cell_count=cell_count,
            cell_histogram=_histogram(text),
            netlist_uri=str(netlist_out) if netlist_out else "",
            wall_seconds=elapsed,
            log_uri=log_uri,
        )
        self._cache[key] = result
        return result

    def _fail(self, top_module: str, error: str, elapsed: float,
              log_uri: str = "") -> SynthesisResult:
        return SynthesisResult(
            success=False, top_module=top_module, technology=self.technology,
            cell_area_um2=None, cell_count=None,
            wall_seconds=elapsed, log_uri=log_uri, error=error,
        )

    def _save_log(self, top_module: str, text: str) -> str:
        if self.work_root is None:
            return ""
        root = Path(self.work_root)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"yosys_{top_module}.log"
        path.write_text(text, encoding="utf-8")
        return path.as_uri()


def _last(pattern: re.Pattern[str], text: str) -> re.Match[str] | None:
    matches = list(pattern.finditer(text))
    return matches[-1] if matches else None


def _histogram(text: str) -> dict[str, int]:
    """最后一段 stat 里的「单元名 个数」两列。"""
    tail = text.rsplit("Printing statistics", 1)[-1]
    counts: dict[str, int] = {}
    for line in tail.splitlines():
        parts = line.split()
        # 标准单元行长这样：`     NAND2_X1    69`；通用门以 `$_` 开头，跳过。
        if len(parts) == 2 and parts[1].isdigit() and not parts[0].startswith("$"):
            counts[parts[0]] = int(parts[1])
    return counts
