"""人工标定的算法知识不能被静默继承。

评审 P1-1：`gather_slowdown()` 按算法名前缀查一张实测表，**没测过的方法
静默退回 xm**。后果是拿一个没标定过的新算法跑这条流水线，它会继承 xm 的
人工标定值而报告里看不出来——于是「框架能适配新算法」这个结论建立在一个
借来的常数上。

## 为什么这里没有换成 label-free 模型

试过两条，都不成立：

  用真实 index trace 直接算 bank 冲突（bank = column mod bank_count，
  周期数取各 bank 最大负载）——四个 bank 数上**趋势都是反的**：实测 bank
  越多减速越小（xm 3.054 -> 1.133），模型却越大（1.247 -> 2.781）。

  结构特征——`index_entropy` 把 nm 排成最差（实测最好）；
  `block_occupancy` 对 3 个顺序但 topk/sanger 那一对是反的。

继续调参去拟合那 16 个实测点，得到的是"能复现标定集"的东西，不是能外推的
模型。所以这里不猜，改成**把出处说出来**。
"""

from __future__ import annotations

import pytest

from fast.agents.templates import gather_slowdown, gather_slowdown_provenance


@pytest.mark.parametrize("method,family", [
    ("xm:32:4:64", "xm"), ("nm:16:64", "nm"), ("topk:64", "topk"), ("sanger", "sanger"),
])
def test_a_calibrated_algorithm_reports_its_own_measurement(method, family):
    value, source = gather_slowdown_provenance(8, method)
    assert source == f"measured:{family}"
    assert value == gather_slowdown(8, method)


def test_an_uncalibrated_algorithm_says_it_borrowed_the_number():
    """静默继承是这条修复要消灭的东西。"""
    value, source = gather_slowdown_provenance(8, "newalgo:1:2")
    assert source.startswith("fallback:xm")
    assert "newalgo" in source
    # 借的是 xm 的值——偏保守，但**借来的就是借来的**。
    assert value == gather_slowdown_provenance(8, "xm")[0]


def test_an_uncalibrated_bank_count_says_which_point_it_used():
    """bank 数没测过时取最近的实测点，那也是一次外推。"""
    _, source = gather_slowdown_provenance(12, "xm")
    assert "nearest to 12" in source and "8banks" in source


def test_the_estimate_carries_the_provenance():
    """出处要一路进到评估证据里，不能停在这个函数内部。"""
    from fast.agents.codesign import CoDesignPoint, estimate
    from fast.schemas.models import KernelResult, Status

    kernel = KernelResult(
        status=Status.PASSED, baseline_metric=10.0, candidate_metric=10.2,
        metric_name="ppl", quality_loss=0.02, actual_sparsity=0.75,
        index_entropy=0.9, block_occupancy=0.5, trace_uri="",
        sparse_method="newalgo:1:2",
    )
    point = CoDesignPoint(
        tile_q=64, tile_k=64, tile_d=64, parallelism=256, double_buffer=True,
        num_rows=16, pe_per_row=16, reg_width=32, data_width=16,
        sram_bytes=131072, queue_depth=2, divider_stages=8, bank_count=8,
    )
    metrics = estimate(point, kernel, 512, head_dim=64)
    assert metrics["memory_slowdown_source"].startswith("fallback:xm")
