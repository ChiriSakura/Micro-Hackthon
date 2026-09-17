"""搜索空间里不能有分辨不出差别的维度。

实测：`tile_q` / `tile_k` / `tile_d` / `parallelism` / `double_buffer` 单独变
时，cycles / area / power / seconds / edp / clock / dram_bytes **七个指标全
不变**。它们贡献了 144 倍的空间膨胀（1,658,880 -> 11,520）。

留着它们不是「多探索一点」，是更糟：搜索预算 99.3% 花在分辨不出差别的组合
上，LLM proposer 会为它们编造**不可能被证伪**的理由，而等预算对比里随机搜索
和 LLM 在这片空白上的差异全是噪声。
"""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from fast.agents.codesign import CoDesignPoint, CoDesignSpace, estimate
from fast.schemas.models import KernelResult, Status

_METRICS = ("cycles", "area", "power", "seconds", "edp",
            "clock_period_ns", "dram_bytes")


def _kernel() -> KernelResult:
    return KernelResult(
        status=Status.PASSED, baseline_metric=10.0, candidate_metric=10.2,
        metric_name="ppl", quality_loss=0.02, actual_sparsity=0.75,
        index_entropy=0.9, block_occupancy=0.5, trace_uri="",
        sparse_method="xm:32:4:64")


def _point(**kw) -> CoDesignPoint:
    base = dict(tile_q=64, tile_k=64, tile_d=64, parallelism=8, double_buffer=True,
                num_rows=16, pe_per_row=16, reg_width=32, data_width=16,
                sram_bytes=131072, queue_depth=2, divider_stages=8, bank_count=32)
    return CoDesignPoint(**{**base, **kw})


def test_every_searched_dimension_changes_at_least_one_metric():
    """**这是这个文件存在的理由。**

    加一个新维度而忘了接成本侧时，这个测试会失败——而不是等到某次实验
    报告写出「探索了 N 万个设计」才发现其中大半是空转。
    """
    kernel, space = _kernel(), CoDesignSpace()
    reference = estimate(_point(), kernel, 512, head_dim=64)
    inert = []

    for field in fields(space):
        values = getattr(space, field.name)
        if not isinstance(values, tuple) or len(values) < 2:
            continue          # 单值维度不参与搜索，见 CoDesignSpace 的说明
        if not hasattr(_point(), field.name):
            continue
        moved = False
        for value in values:
            got = estimate(_point(**{field.name: value}), kernel, 512, head_dim=64)
            for key in _METRICS:
                a, b = reference.get(key), got.get(key)
                if a is not None and b is not None and abs(a - b) > 1e-9 * max(1.0, abs(a)):
                    moved = True
                    break
            if moved:
                break
        if not moved:
            inert.append(field.name)

    assert not inert, (
        f"这些维度在搜索空间里有多档，但改变它们不影响任何指标：{inert}。"
        f"先让代价模型算到它们，再放开搜索——反过来会让优化器在纯噪声上"
        f"花预算，而报告看起来像探索了很大的空间。")


@pytest.mark.parametrize("name", ["tile_q", "tile_k", "tile_d",
                                  "parallelism", "double_buffer"])
def test_the_known_inert_dimensions_stay_pinned(name):
    """已知分辨不了的维度必须是单值。

    要放开，先接成本侧：`tile_d` 该影响重用和尾部损耗，`double_buffer`
    该影响驻留字节和面积。**接上再放开，不要反过来。**
    """
    assert len(getattr(CoDesignSpace(), name)) == 1


def test_the_space_is_the_size_the_cost_model_can_actually_rank():
    space = CoDesignSpace()
    size = 1
    for field in fields(space):
        values = getattr(space, field.name)
        if isinstance(values, tuple):
            size *= len(values)
    assert size == 11_520, f"搜索空间变成了 {size:,}——新增或放开了维度？"
