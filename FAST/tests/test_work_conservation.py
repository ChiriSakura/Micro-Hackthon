"""总工作量由**问题形状**决定，不由分块决定。

评审 P0-1：`estimate()` 曾用 `sequence_length^2 x point.tile_d` 定义总 MAC 数，
而 `tile_d` 是**可搜索的分块尺寸**。后果是把分块改小会被直接奖励——实测
tile_d 从 64 减到 32，cycles 减半、EDP 变四分之一，纯粹是模型假象。

`tile_d` 默认恰好等于 head_dim（都是 64），所以这个混淆一直看着像对的。
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from fast.agents.codesign import CoDesignPoint, estimate
from fast.schemas.models import KernelResult, Status


def _kernel(sparsity: float = 0.75) -> KernelResult:
    return KernelResult(
        status=Status.PASSED, baseline_metric=10.0, candidate_metric=10.2,
        metric_name="ppl", quality_loss=0.02, actual_sparsity=sparsity,
        index_entropy=0.9, block_occupancy=0.5, trace_uri="",
        sparse_method="xm:32:4:64",
    )


def _point(**kw) -> CoDesignPoint:
    base = dict(tile_q=64, tile_k=64, tile_d=64, parallelism=256, double_buffer=True,
                num_rows=16, pe_per_row=16, reg_width=32, data_width=16,
                sram_bytes=131072, queue_depth=2, divider_stages=8, bank_count=32)
    return CoDesignPoint(**{**base, **kw})


@pytest.mark.parametrize("tile_d", [16, 32, 64])
def test_tiling_does_not_change_the_total_work(tile_d):
    """分块该影响重用、尾部损耗和驻留字节，**不是任务本身**。"""
    reference = estimate(_point(tile_d=64), _kernel(), 512, head_dim=64)
    got = estimate(_point(tile_d=tile_d), _kernel(), 512, head_dim=64)
    assert got["cycles"] == pytest.approx(reference["cycles"])
    assert got["edp"] == pytest.approx(reference["edp"])


def test_the_head_dimension_does_change_the_work():
    """head_dim 变了是**任务变了**，工作量必须跟着变。"""
    narrow = estimate(_point(), _kernel(), 512, head_dim=32)
    wide = estimate(_point(), _kernel(), 512, head_dim=128)
    assert wide["cycles"] > narrow["cycles"]
    assert wide["dram_bytes"] > narrow["dram_bytes"]


def test_head_dim_has_no_default():
    """默认值会让这个洞在调用方忘记传时悄悄复活——它上一次就是靠
    `tile_d` 默认恰好等于 64 才一直看着像对的。"""
    with pytest.raises(TypeError):
        estimate(_point(), _kernel(), 512)          # type: ignore[call-arg]


def test_both_qk_and_av_are_counted():
    """注意力的稀疏部分要跑两遍 seq^2 x D：QK^T 和 AV。"""
    got = estimate(_point(), _kernel(sparsity=0.0), 512, head_dim=64)
    # 稀疏度 0 时执行阵列的工作量是 2 x seq^2 x head_dim。
    lanes = 16 * 16
    expected_compute = 2 * 512 * 512 * 64 / (lanes * got["pe_utilization"])
    assert got["compute_cycles"] == pytest.approx(expected_compute, rel=1e-6)


def test_dense_prediction_puts_a_floor_under_the_sparsity_benefit():
    """DynaX 的预测器给**所有** (query, key) 对算近似分数，那是 O(N^2) 的
    开销，不随稀疏度下降。漏掉它会让稀疏收益被无限高估。
    """
    sparse = estimate(_point(), _kernel(sparsity=0.95), 512, head_dim=64)
    sparser = estimate(_point(), _kernel(sparsity=0.99), 512, head_dim=64)
    # 再稀疏也降不下去了——下限是稠密预测。
    assert sparser["cycles"] == pytest.approx(sparse["cycles"])
    # 但在下限之上，稀疏确实省时间。
    dense = estimate(_point(), _kernel(sparsity=0.50), 512, head_dim=64)
    assert dense["cycles"] > sparse["cycles"]


def test_traffic_scales_with_the_head_dimension():
    """搬的每个 K/V 元素是 head_dim 维——原来这一项漏了 head_dim。"""
    narrow = estimate(_point(), _kernel(), 512, head_dim=32)
    wide = estimate(_point(), _kernel(), 512, head_dim=64)
    assert wide["dram_bytes"] == pytest.approx(2 * narrow["dram_bytes"])
