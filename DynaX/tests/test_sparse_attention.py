from __future__ import annotations

import pytest
import torch

from models.utils.sparse_attention import prune_attn_scores, quant_qk_matmul


SEQUENCE_LENGTH = 64


def _scores(device: torch.device) -> torch.Tensor:
    row = torch.arange(SEQUENCE_LENGTH, dtype=torch.float32, device=device)
    return row.view(1, 1, 1, -1).expand(1, 1, SEQUENCE_LENGTH, -1).clone()


def _attention_mask(device: torch.device) -> torch.Tensor:
    return torch.zeros(1, 1, 1, SEQUENCE_LENGTH, device=device)


def _kept(mask: torch.Tensor) -> torch.Tensor:
    assert mask.shape == (1, 1, SEQUENCE_LENGTH, SEQUENCE_LENGTH)
    assert torch.all((mask == 0) | (mask == -10000))
    return mask == 0


def _assert_golden_masks(device: torch.device) -> None:
    scores = _scores(device)
    attention_mask = _attention_mask(device)

    nm = _kept(
        prune_attn_scores(scores, attention_mask, m=16, n=4, sparse_method="nm")
    )
    expected_nm = torch.zeros_like(nm)
    for block_start in range(0, SEQUENCE_LENGTH, 16):
        expected_nm[..., block_start + 12 : block_start + 16] = True
    assert torch.equal(nm, expected_nm)

    topk = _kept(
        prune_attn_scores(scores, attention_mask, topk=8, sparse_method="topk")
    )
    expected_topk = torch.zeros_like(topk)
    expected_topk[..., -8:] = True
    assert torch.equal(topk, expected_topk)

    xm_16 = _kept(
        prune_attn_scores(
            scores,
            attention_mask,
            threshold_0=0.0,
            threshold_1=-1.0,
            sparse_method="xm",
        )
    )
    expected_xm_16 = torch.zeros_like(xm_16)
    expected_xm_16[..., -16:] = True
    assert torch.equal(xm_16, expected_xm_16)

    xm_8 = _kept(
        prune_attn_scores(
            scores,
            attention_mask,
            threshold_0=2.0,
            threshold_1=-1.0,
            sparse_method="xm",
        )
    )
    expected_xm_8 = torch.zeros_like(xm_8)
    expected_xm_8[..., -8:] = True
    assert torch.equal(xm_8, expected_xm_8)

    xm_zero = _kept(
        prune_attn_scores(
            scores,
            attention_mask,
            threshold_0=3.0,
            threshold_1=2.0,
            sparse_method="xm",
        )
    )
    assert not xm_zero.any()

    probabilities = torch.softmax(scores + (1.0 - nm.float()) * -10000.0, dim=-1)
    assert torch.isfinite(probabilities).all()
    torch.testing.assert_close(
        probabilities.sum(dim=-1), torch.ones_like(probabilities.sum(dim=-1))
    )


def test_structured_masks_match_cpu_golden(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _assert_golden_masks(torch.device("cpu"))


@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_structured_masks_match_cuda_golden(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _assert_golden_masks(torch.device("cuda"))


def test_xm_is_deterministic_for_paper_default_shape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = torch.Generator().manual_seed(20260903)
    scores = torch.randn(1, 2, 64, 64, generator=generator)
    attention_mask = torch.zeros(1, 1, 64, 64)

    first = prune_attn_scores(scores, attention_mask, sparse_method="xm")
    second = prune_attn_scores(scores, attention_mask, sparse_method="xm")

    assert torch.equal(first, second)
    kept_per_row = (first == 0).sum(dim=-1)
    assert torch.all((kept_per_row == 8) | (kept_per_row == 16))


def test_quantized_query_patterns_match_manual_golden():
    query = torch.tensor([[[[1.0, -3.0, 2.0, -4.0]]]])
    identity_key = torch.eye(4).reshape(1, 1, 4, 4)

    one_of_two = quant_qk_matmul("1_2_4bit", query, identity_key, torch.matmul)
    one_of_four = quant_qk_matmul("1_4_6bit", query, identity_key, torch.matmul)

    torch.testing.assert_close(one_of_two, torch.tensor([[[[0.0, -3.0, 0.0, -4.0]]]]))
    torch.testing.assert_close(one_of_four, torch.tensor([[[[0.0, 0.0, 0.0, -4.0]]]]))


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"sparse_method": "unknown"}, "Unsupported sparse_method"),
        ({"sparse_method": "nm", "m": 16, "n": 17}, "0 < n <= m"),
        ({"sparse_method": "topk", "topk": 65}, "topk must be"),
    ],
)
def test_invalid_sparse_parameters_fail_loudly(kwargs, message, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match=message):
        prune_attn_scores(_scores(torch.device("cpu")), _attention_mask(torch.device("cpu")), **kwargs)


def test_nondivisible_xm_sequence_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    scores = torch.zeros(1, 1, 63, 63)
    attention_mask = torch.zeros(1, 1, 1, 63)

    with pytest.raises(ValueError, match="divisible by 64"):
        prune_attn_scores(scores, attention_mask, sparse_method="xm")
