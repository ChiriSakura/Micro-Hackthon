"""从 VCD 数出真实的翻转率 α。

## 为什么需要它

功耗模型里的 α 一直是个假设值。两个标定锚点里 `RePEArray_L` 明确记录用的是
**默认常数 0.200** 而不是激励——只有 `_S` 是真实翻转率数出来的。来源不一
正是拒绝把预测阵列功耗加进帕累托轴的理由。

## 为什么不用 OpenSTA 的 read_vcd

试过。VCD 来自 RTL 仿真，STA 跑在综合后的网表上，内部网名对不上，
`read_vcd` 只能标注边界，报出来的功耗和假设 α=0.2 只差 2.9%——**在噪声里**。

更糟的是 `set_power_activity -input` 本身对内部网没有控制力：实测 α 从 0.02
扫到 0.9（45 倍），总功耗在 0.1079-0.1183 W 之间**非单调抖动**（±5%）。
而 `-global` 是单调近似线性的（0.0137 -> 0.2234 W，16 倍）。

所以流程是：**这里数出 α，再用 `-global` 施加**。

## 这个 α 是什么，不是什么

**是**：RTL 仿真里所有被记录信号的平均每周期翻转率。
**不是**：逐网的活动率，也不是门级网表上的活动率。深层逻辑的活动率通常
低于输入（组合路径有衰减），`-global` 一视同仁会**高估**深层逻辑的功耗。

门级 VCD 才能消除这个偏差，但那需要 Nangate45 的 Verilog 单元模型，
当前 PDK 目录里只有 `.lib`。这个限制要跟着数走。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ActivityMeasurement:
    """一次 VCD 分析的结果。"""

    #: 平均每周期每信号的翻转次数，[0, 1] 截断前的原始值。
    alpha: float
    #: 参与统计的信号数。
    signals: int
    #: 覆盖的时钟周期数。
    cycles: float
    #: 总翻转次数。
    transitions: int
    #: 这是 RTL 级还是门级。门级才能逐网精确。
    level: str = "rtl"

    @property
    def clamped(self) -> float:
        """施加给 STA 的值，夹在 (0, 1]。"""
        return min(1.0, max(1e-4, self.alpha))

    def describe(self) -> str:
        return (f"α={self.clamped:.4f}（{self.level} 级，{self.signals} 个信号，"
                f"{self.cycles:.0f} 周期，{self.transitions} 次翻转）")


_VAR = re.compile(r"^\$var\s+\S+\s+(\d+)\s+(\S+)\s+(\S+)")


def activity_from_vcd(path: str | Path, *, clock_name: str = "clock",
                      level: str = "rtl") -> ActivityMeasurement:
    """数出 VCD 里的平均翻转率。

    多位信号按**位**计：一个 16 位总线翻 3 位算 3 次翻转、16 个信号-周期。
    按信号计会让宽总线和单比特控制信号权重相同，而功耗跟的是位。

    时钟本身不计入——它每周期必翻两次，混进去会把 α 拉向一个与工作负载
    无关的常数。
    """
    path = Path(path)
    ids: dict[str, int] = {}          # 标识符 -> 位宽
    clock_id: str | None = None
    previous: dict[str, str] = {}
    transitions = 0
    clock_edges = 0
    in_header = True

    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if in_header:
                found = _VAR.match(line)
                if found:
                    width, identifier, name = found.groups()
                    if name.split("[")[0] == clock_name:
                        clock_id = identifier
                    else:
                        ids[identifier] = int(width)
                elif line.startswith("$enddefinitions"):
                    in_header = False
                continue

            if not line or line[0] in "#$":
                continue
            # 标量：`0!` / `1!` / `x!`；向量：`b1010 !`
            if line[0] in "01xzXZ" and len(line) > 1:
                value, identifier = line[0], line[1:]
            elif line[0] in "bB":
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                value, identifier = parts[0][1:], parts[1]
            else:
                continue

            if identifier == clock_id:
                if previous.get(identifier) != value:
                    clock_edges += 1
                previous[identifier] = value
                continue
            if identifier not in ids:
                continue

            before = previous.get(identifier)
            if before is not None and before != value:
                if len(value) == 1 and len(before) == 1:
                    transitions += 1
                else:
                    # 向量：数有多少位不同。长度不等时按右对齐补零。
                    width = max(len(before), len(value))
                    a, b = before.rjust(width, "0"), value.rjust(width, "0")
                    transitions += sum(1 for x, y in zip(a, b) if x != y)
            previous[identifier] = value

    total_bits = sum(ids.values())
    cycles = clock_edges / 2.0 if clock_edges else 0.0
    alpha = transitions / (total_bits * cycles) if total_bits and cycles else 0.0
    return ActivityMeasurement(
        alpha=alpha, signals=len(ids), cycles=cycles,
        transitions=transitions, level=level,
    )
