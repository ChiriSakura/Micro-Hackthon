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
        parallelism = max(1, min(max_parallelism, round(16 * kernel.block_occupancy)))
        return CompilerSchedule(
            status=Status.PASSED,
            tile_q=64,
            tile_k=64,
            tile_d=32,
            loop_order=("q", "k", "d"),
            data_layout="blocked-qkd",
            parallelism=parallelism,
            predicted_utilization=min(1.0, 0.45 + kernel.block_occupancy),
            predicted_bytes=max(1, round(64 * 64 * kernel.block_occupancy * 2)),
            rationale=("block_occupancy", "index_entropy"),
        )
