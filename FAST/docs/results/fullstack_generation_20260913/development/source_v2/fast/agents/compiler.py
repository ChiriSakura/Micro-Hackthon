"""Compiler Agent：planner——决定**造什么**。

在流水线里的位置：Kernel → **Compiler** → µArch → Evaluator → Critic。

## 职责边界：规划 vs 实现

这个 Agent 输出一份**完整的硬件计划**：数据流与调度（tile 尺寸、循环序、
layout、并行度）**以及**硬件参数（阵列形状、队列深度、bank 数、SRAM 容量、
除法器级数）。µArch Agent 拿到计划只负责把它实现出来并证明它对，不再自己
推导任何参数。

「造什么」和「怎么造」由此分开。此前 µArch 里有

    pe_rows = max(1, min(8, schedule.parallelism))

——阵列形状是规划决策，却藏在实现者里。

## 为什么软硬件参数在同一次搜索里

分开规划就等于分开优化，而这两者双向耦合：阵列形状限制并行度，SRAM 容量
限制 tile 大小，队列深度和 bank 数直接决定周期数和时钟。**一次搜索覆盖全部
参数，耦合就是结构上保证的，不可能被绕过。**

搜索空间、可行性判据和代价模型在 `fast/agents/codesign.py`，搜索引擎在
`fast/agents/cooptimizer.py`——那两个文件是这个 Agent 的内脏，不是独立的
Agent。代价模型混合组件标定与一阶外推，功耗锚点还需更新；来源见
`hardware/README.md`，当前证据边界见 `docs/agent-architecture.md`。

## 它拥有什么

  * 可行性：面积 / PE / SRAM / **频率** / **功耗** 预算
  * 打分与 frontier
  * 输出**一个**计划（不是一组），让 Critic 的动作空间保持清晰

## 它不拥有什么

  * RTL 长什么样（µArch）
  * 计划到底对不对（µArch 的功能仿真门 + Evaluator 的实测）
  * 换哪个 kernel 候选（Critic）

门限：kernel 没通过质量门限时返回 `SKIPPED`，不做任何规划。
"""

from __future__ import annotations

from dataclasses import replace

from fast.agents.codesign import CoDesignSpace, clock_period_ns, to_schedule
from fast.agents.cooptimizer import CoDesignResult, CoOptimizer
from fast.agents.templates import TemplateRegistry
from fast.schemas.models import ArchSpecs, CompilerSchedule, KernelResult, Status


class CompilerAgent:
    """Plans one complete hardware configuration for one kernel result."""

    def __init__(
        self,
        registry: TemplateRegistry | None = None,
        *,
        template_id: str = "repe_array",
        allow_unverified: bool = False,
        proposer=None,
        objective=None,
    ):
        self.registry = registry or TemplateRegistry()
        self.template_id = template_id
        self.allow_unverified = allow_unverified
        # None = 确定性的 GuidedProposer。注入 LLMPlanProposer 就换成模型提议，
        # 而可行性、打分、frontier 仍然归搜索引擎——两种 proposer 因此**只在
        # 「会不会选」这一个维度上**有差别，对照实验才成立。
        self.proposer = proposer
        self.objective = objective
        # 上一次规划的完整搜索报告。Critic 要看它才能区分「没有可行点」和
        # 「有可行点但都不好」——两者的下一步完全不同。
        self.last_search: object | None = None

    def plan(
        self,
        kernel: KernelResult,
        *,
        sequence_length: int,
        head_dim: int = 64,
        specs: ArchSpecs | None = None,
        space: CoDesignSpace | None = None,
        budget: int = 24,
        batch: int = 8,
        block_m: int = 64,
        kept_per_block: int = 16,
    ) -> CompilerSchedule:
        """搜出一份完整的硬件计划。

        kernel 没过质量门限时直接 `SKIPPED`——在一个不该被造的算法上规划
        硬件是纯粹的浪费，而且会让 Critic 收到一份看似正常的计划。
        """
        if kernel.status is not Status.PASSED:
            return _skipped("kernel quality gate failed")

        specs = specs or ArchSpecs()
        search = CoOptimizer(
            self.registry,
            template_id=self.template_id,
            allow_unverified=self.allow_unverified,
            objective=self.objective,
        ).run(
            kernel,
            sequence_length=sequence_length,
            head_dim=head_dim,
            specs=specs,
            space=space,
            proposer=self.proposer,
            budget=budget,
            batch=batch,
            block_m=block_m,
            kept_per_block=kept_per_block,
        )
        self.last_search = search

        if search.best is None:
            # 说明「为什么一个都不可行」，不是只说「失败了」。被拒样例里
            # 带着具体的违反项（比如「clock 318 MHz 低于目标 350 MHz」），
            # Critic 要靠它决定是放宽约束还是换 kernel 候选。
            reason = "; ".join(search.rejected_examples[:3]) or "no feasible point"
            return _skipped(f"no feasible plan: {reason}")

        return _as_plan(search.best, block_m, kept_per_block)


def _as_plan(result: CoDesignResult, block_m: int, kept_per_block: int) -> CompilerSchedule:
    """把搜索的获胜点变成一份计划，**连同它的预测值一起**。

    预测值必须带出去：µArch 和 Evaluator 会产出实测数字，两者的差距本身是
    一条可归因的结论（模型说 2.23 ns 而综合说 3.14 ns，说明瓶颈在代价模型
    里而不在任何一层硬件）。不带出去，这个循环就发现不了自己的模型错了。
    """
    point = result.point
    metrics = result.metrics
    schedule = result.schedule
    return replace(
        to_schedule(point, result.rationale, metrics["pe_utilization"],
                    block_m=block_m, kept_per_block=kept_per_block),
        loop_order=schedule.loop_order,
        data_layout=schedule.data_layout,
        # The exported prediction is total DRAM traffic, not resident tile bytes.
        predicted_bytes=int(metrics["dram_bytes"]),
        predicted_cycles=metrics["cycles"],
        predicted_area_um2=metrics["area"],
        predicted_power_mw=metrics["power"],
        predicted_clock_ns=clock_period_ns(point),
    )


def _skipped(reason: str) -> CompilerSchedule:
    return CompilerSchedule(
        status=Status.SKIPPED,
        tile_q=0, tile_k=0, tile_d=0,
        loop_order=(), data_layout="none", parallelism=0,
        predicted_utilization=0.0, predicted_bytes=0,
        error=reason,
    )
