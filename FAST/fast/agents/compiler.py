"""Compiler Agent：把 Kernel 的稀疏统计变成一份有界的调度。

在流水线里的位置：Kernel → **Compiler** → µArch → Evaluator → Critic。

它读的不是「稀疏率」这个标量，而是 `KernelProfile` 里的分布——tile 大小和
PE 负载均衡由稀疏的**形状**决定，平均值恰好掩盖了让脉动阵列空转的那部分
不均衡。

这个类只产出单点调度。真正的搜索在 `fast/agents/cooptimizer.py`：
Compiler 和 µArch 是双向耦合的，硬件约束会反向裁剪调度空间，
所以两者不能各搜各的。

门限：kernel 没通过质量门限时返回 `SKIPPED`，不做任何调度。
"""

from __future__ import annotations

from fast.schemas.models import CompilerSchedule, KernelResult, Status


class CompilerAgent:
    """Creates a bounded schedule from kernel statistics and hardware limits."""

    def run(self, kernel: KernelResult, *, max_parallelism: int = 16) -> CompilerSchedule:
        if kernel.status is not Status.PASSED:
            return CompilerSchedule(
                status=Status.SKIPPED,
                tile_q=0,
                tile_k=0,
                tile_d=0,
                loop_order=(),
                data_layout="none",
                parallelism=0,
                predicted_utilization=0.0,
                predicted_bytes=0,
                error="kernel quality gate failed",
            )
        profile = kernel.profile
        rationale: list[str] = []

        # Block occupancy says how much data can be skipped; load imbalance says
        # whether the PEs will sit idle. They answer different questions, and the
        # schedule's parallelism is decided by the second one: widening a lane
        # that is already starved by a long row buys nothing.
        if profile is not None:
            imbalance = max(1.0, profile.load_imbalance)
            parallelism = max(1, min(max_parallelism, round(max_parallelism / imbalance)))
            predicted_utilization = min(1.0, 1.0 / imbalance)
            rationale.append(f"load_imbalance={imbalance:.3f}")
            rationale.append(
                "balanced rows: widened lanes" if profile.balanced
                else "skewed rows: narrowed lanes to keep them fed"
            )
            # Concentrated columns are re-read by every row in a tile, so they
            # are worth staging once rather than streaming per row.
            layout = "blocked-qkd-broadcast" if profile.column_top5_mass >= 0.5 else "blocked-qkd"
            rationale.append(f"column_top5_mass={profile.column_top5_mass:.3f}")
        else:
            # No profile: fall back to density alone and say so, rather than
            # inventing a balance figure the kernel never measured.
            parallelism = max(1, min(max_parallelism, round(16 * kernel.block_occupancy)))
            predicted_utilization = min(1.0, 0.45 + kernel.block_occupancy)
            layout = "blocked-qkd"
            rationale.append("no kernel profile; scheduled from block_occupancy alone")

        # Only occupied blocks are fetched, so traffic scales with occupancy.
        predicted_bytes = max(1, round(64 * 64 * kernel.block_occupancy * 2))
        rationale.append(f"block_occupancy={kernel.block_occupancy:.3f}")

        return CompilerSchedule(
            status=Status.PASSED,
            tile_q=64,
            tile_k=64,
            tile_d=32,
            loop_order=("q", "k", "d"),
            data_layout=layout,
            parallelism=parallelism,
            predicted_utilization=predicted_utilization,
            predicted_bytes=predicted_bytes,
            rationale=tuple(rationale),
        )
