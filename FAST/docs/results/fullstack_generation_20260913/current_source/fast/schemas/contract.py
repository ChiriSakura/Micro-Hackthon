"""稀疏算法的**类型化契约**：一个标签到底规定了什么。

## 为什么需要它

标签一直是被当字符串用的：`gather_slowdown()` 按前缀查表，`plan()` 的
`block_m` / `kept_per_block` 是**默认值**而调用方不传。后果是软件评估的稀疏
策略和硬件构建的可以不是同一个——实测 `flow._round()` 用 `xm:32:4:64` 跑
kernel，而 Compiler 按 `block_m=64, kept_per_block=16` 规划硬件。

## X:M 不能被一个 kept 数替代

DynaX 的动态 X:M 是：每个 M 宽的 block 按概率质量选择保留 `{0, n2, n1}` 之一
——质量大的块保留 n1 个，小的保留 n2 个，可忽略的整块跳过。用一个固定的
"kept" 描述它会丢掉**行长的分布**，而分布正是决定 PE 尾部浪费和队列不均衡的
东西。

所以这里保留 `kept_high` / `kept_low` 两个值，并把「硬件必须按哪个尺寸造」
和「平均保留多少」分开：

    sizing_kept   硬件要能装下的最坏情况 = kept_high
    每块实际保留   在 {0, kept_low, kept_high} 里按质量选

只支持固定 top-k 的硬件版本必须显式声明 `supported_semantics`，把它当成一个
**子任务**来评估，而不是假装它实现了完整的 X:M。
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SparseAlgorithmContract:
    """一个稀疏配置标签解析出来的、可被各层共同引用的参数。"""

    label: str
    family: str
    #: block 宽度 M。top-k 没有 block 概念时是 None。
    block_m: int | None
    #: 质量大的 block 保留几个（X:M 的 n1；N:M 的 N；top-k 的 K）。
    kept_high: int | None
    #: 质量小的 block 保留几个。只有 X:M 有第二档。
    kept_low: int | None
    threshold_0: float | None = None
    threshold_1: float | None = None

    @property
    def sizing_kept(self) -> int | None:
        """**硬件按哪个尺寸造**：最坏情况下一个 block 要保留几个。

        不是平均值——阵列和寄存器窗口必须装得下最宽的那一行，否则会在真实
        数据上溢出而不是变慢。
        """
        return self.kept_high

    @property
    def has_two_tier_keep(self) -> bool:
        """是不是「每块在两档之间按质量选」。X:M 是，N:M 和 top-k 不是。"""
        return self.kept_low is not None and self.kept_low != self.kept_high

    def describe(self) -> str:
        if self.has_two_tier_keep:
            return (f"{self.family}: 每个 {self.block_m} 宽 block 按概率质量保留 "
                    f"{{0, {self.kept_low}, {self.kept_high}}} 之一")
        if self.block_m:
            return f"{self.family}: 每个 {self.block_m} 宽 block 保留 {self.kept_high}"
        return f"{self.family}: 每行保留 {self.kept_high}"


def parse_algorithm(label: str) -> SparseAlgorithmContract:
    """把 DynaX runner 的标签语法解析成契约。

    语法（和 `DynaX/run_eval_matrix.py` 一致）：

        xm:n1:n2:M    动态 X:M，每块在 {0, n2, n1} 中按质量选
        nm:N:M        静态 N:M，每块固定保留 N
        topk:K        每行保留全局 top-K，没有 block 结构

    解析不了就**如实返回未知**，不要退回一组默认参数——默认参数正是这个
    模块要消灭的东西。
    """
    text = str(label or "").strip()
    parts = text.split(":")
    family = parts[0] if parts else ""

    try:
        if family == "xm" and len(parts) in (4, 6):
            n1, n2, block = int(parts[1]), int(parts[2]), int(parts[3])
            if not 0 < n2 <= n1 <= block:
                raise ValueError("invalid X:M budget")
            t0, t1 = map(float, parts[4:]) if len(parts) == 6 else (None, None)
            if t0 is not None and (not all(math.isfinite(t) for t in (t0, t1))
                                   or not 0 <= t1 <= t0):
                raise ValueError("invalid X:M thresholds")
            return SparseAlgorithmContract(text, family, block, n1, n2, t0, t1)
        if family == "nm" and len(parts) == 3:
            kept, block = int(parts[1]), int(parts[2])
            return SparseAlgorithmContract(text, family, block, kept, kept)
        if family == "topk" and len(parts) == 2:
            return SparseAlgorithmContract(text, family, None, int(parts[1]), int(parts[1]))
    except ValueError:
        pass
    return SparseAlgorithmContract(text, family or "unknown", None, None, None)
