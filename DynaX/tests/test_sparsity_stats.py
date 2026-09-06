"""★ FAST 新增，非 DynaX 上游文件。"""

from __future__ import annotations

import json

import pytest
import torch

from models.utils.sparse_attention import prune_attn_scores
from models.utils.sparsity_stats import SparsityRecorder, get_recorder, reset_recorder


SEQUENCE_LENGTH = 128


def _scores() -> torch.Tensor:
    row = torch.arange(SEQUENCE_LENGTH, dtype=torch.float32)
    return row.view(1, 1, 1, -1).expand(1, 1, SEQUENCE_LENGTH, -1).clone()


def _attention_mask() -> torch.Tensor:
    return torch.zeros(1, 1, 1, SEQUENCE_LENGTH)


def test_recorder_reports_expected_nm_sparsity():
    recorder = reset_recorder()
    prune_attn_scores(_scores(), _attention_mask(), m=64, n=16, sparse_method="nm", layer_idx=3)

    summary = recorder.summary()["nm"]
    assert summary["calls"] == 1
    assert summary["mean_kept_ratio"] == pytest.approx(16 / 64)
    assert summary["mean_sparsity"] == pytest.approx(1 - 16 / 64)
    assert summary["row_kept_min"] == summary["row_kept_max"] == 32.0
    assert summary["per_layer_mean_kept_ratio"] == {"3": pytest.approx(16 / 64)}
    reset_recorder()


def test_recorder_is_isolated_per_run_and_serialises(tmp_path):
    recorder = reset_recorder()
    prune_attn_scores(_scores(), _attention_mask(), topk=8, sparse_method="topk")
    first = recorder.summary()["topk"]["calls"]

    reset_recorder()
    prune_attn_scores(_scores(), _attention_mask(), topk=8, sparse_method="topk")
    second = recorder.summary()["topk"]["calls"]
    assert first == second == 1

    path = recorder.dump(tmp_path / "sparsity.json")
    assert json.loads(path.read_text())["topk"]["calls"] == 1
    reset_recorder()


def test_disabled_recorder_collects_nothing():
    recorder = SparsityRecorder(enabled=False)
    recorder.record("xm", torch.ones(1, 1, 4, 4, dtype=torch.bool), torch.zeros(1, 1, 1, 4), causal_kept_ratio=1.0)
    assert recorder.summary() == {}


def test_block_occupancy_separates_clustered_from_spread_masks():
    recorder = reset_recorder()
    # top-k over a monotonically increasing row keeps only the final columns,
    # so exactly one 64-wide block is occupied out of two.
    prune_attn_scores(_scores(), _attention_mask(), topk=8, sparse_method="topk")
    clustered = recorder.summary()["topk"]["mean_block_occupancy"]

    reset_recorder()
    prune_attn_scores(_scores(), _attention_mask(), m=64, n=16, sparse_method="nm")
    spread = recorder.summary()["nm"]["mean_block_occupancy"]

    assert clustered == pytest.approx(0.5)
    assert spread == pytest.approx(1.0)
    reset_recorder()


def test_xm_budget_is_configurable():
    kept_default = prune_attn_scores(
        _scores(), _attention_mask(), threshold_0=0.0, threshold_1=-1.0, sparse_method="xm"
    ) == 0
    kept_wide = prune_attn_scores(
        _scores(), _attention_mask(), threshold_0=0.0, threshold_1=-1.0, sparse_method="xm",
        xm_n1=32, xm_n2=4, xm_m=64,
    ) == 0

    assert torch.all(kept_default.sum(dim=-1) == 32)  # n1=16 per 64-wide block, two blocks
    assert torch.all(kept_wide.sum(dim=-1) == 64)  # n1=32 per block
    reset_recorder()


@pytest.mark.parametrize("kwargs", [{"xm_n1": 4, "xm_n2": 8}, {"xm_n1": 0, "xm_n2": 0}, {"xm_n1": 128, "xm_m": 64}])
def test_invalid_xm_budget_fails_loudly(kwargs):
    with pytest.raises(ValueError, match="0 < n2 <= n1 <= m"):
        prune_attn_scores(_scores(), _attention_mask(), sparse_method="xm", **kwargs)


def test_default_recorder_is_process_wide():
    assert get_recorder() is get_recorder()
