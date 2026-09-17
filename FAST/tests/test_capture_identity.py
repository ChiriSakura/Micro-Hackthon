"""形状匹配不能证明算法语义匹配。

评审 P0-5：tile capture 的参照是**固定 top-n**（`torch.topk(scores, kept)`），
而下游候选可能是 `xm:32:4:64`——每块在 {0, 4, 32} 中按概率质量选。两者挑出的
列不同，所以这份抓取**验的是「给定保留列之后执行通路算得对不对」**，不是
「硬件自己选的列对不对」。

而匹配只看 (kept, rows, head_dim)，连 `tile_k` 都没看——它是从计划取
`plan.block_m`，抓取里那个值根本没参与比较。
"""

from __future__ import annotations

import json

import pytest

from fast.adapters.verilator import plan_bench
from fast.schemas.models import CompilerSchedule, Status


def _plan(num_rows=16, block_m=64, kept=16, pe=16) -> CompilerSchedule:
    return CompilerSchedule(
        status=Status.PASSED, tile_q=64, tile_k=block_m, tile_d=64,
        loop_order=("q", "k", "d"), data_layout="row", parallelism=num_rows * pe,
        predicted_utilization=0.85, predicted_bytes=1 << 20,
        num_rows=num_rows, pe_per_row=pe, queue_depth=2,
        block_m=block_m, kept_per_block=kept,
    )


def _write(root, name, *, rows, tile_k, head_dim, kept, identity=None, source=None):
    directory = root / f"tile_{name}"
    directory.mkdir(parents=True)
    payload = {
        "params": {"tile_q": rows, "tile_k": tile_k, "head_dim": head_dim, "kept": kept},
        "source": source or {"model": "TinyLlama", "layer": 10, "head": 0},
        "identity": identity or {
            "reference_semantics": "topk",
            "verifies": "execute-datapath-given-indices",
            "does_not_verify": "selection-semantics",
            "content_sha256": "deadbeef",
        },
        "q_ticks": [[0] * head_dim for _ in range(rows)],
        "k_ticks": [[0] * head_dim for _ in range(tile_k)],
        "v_ticks": [[0] * head_dim for _ in range(tile_k)],
        "expected_kept_idx": [[0] * kept for _ in range(rows)],
    }
    (directory / "tile.json").write_text(json.dumps(payload), encoding="utf-8")
    return directory / "tile.json"


def test_a_capture_with_the_wrong_tile_k_is_not_matched(tmp_path):
    """`tile_k` 决定 testbench 按多少行读 K/V。抓取里那个值原来根本没参与
    匹配——一份 tile_k=32 的抓取能被用在 block_m=64 的计划上。"""
    _write(tmp_path, "wrong", rows=16, tile_k=32, head_dim=64, kept=16)
    assert plan_bench(_plan(block_m=64), head_dim=64, capture_root=tmp_path) is None


def test_a_fully_matching_capture_is_found(tmp_path):
    _write(tmp_path, "right", rows=16, tile_k=64, head_dim=64, kept=16)
    bench = plan_bench(_plan(), head_dim=64, capture_root=tmp_path)
    assert bench is not None
    assert bench.tile_k == 64


def test_the_bench_carries_the_capture_identity(tmp_path):
    """身份要一路带到证据里，让读的人自己判断这次 L2 覆盖了什么。"""
    _write(tmp_path, "id", rows=16, tile_k=64, head_dim=64, kept=16)
    bench = plan_bench(_plan(), head_dim=64, capture_root=tmp_path)
    assert bench.identity["reference_semantics"] == "topk"
    assert bench.identity["does_not_verify"] == "selection-semantics"
    assert bench.source["model"] == "TinyLlama"


def test_a_capture_without_identity_does_not_pretend_to_have_one(tmp_path):
    """老抓取没有这个块。**报「not recorded」，不要编一个语义**。"""
    directory = tmp_path / "tile_old"
    directory.mkdir()
    (directory / "tile.json").write_text(json.dumps({
        "params": {"tile_q": 16, "tile_k": 64, "head_dim": 64, "kept": 16},
        "q_ticks": [[0] * 64 for _ in range(16)],
        "k_ticks": [[0] * 64 for _ in range(64)],
        "v_ticks": [[0] * 64 for _ in range(64)],
        "expected_kept_idx": [[0] * 16 for _ in range(16)],
    }), encoding="utf-8")

    bench = plan_bench(_plan(), head_dim=64, capture_root=tmp_path)
    assert bench is not None
    assert bench.identity == {}
    assert bench.identity.get("reference_semantics", "not recorded") == "not recorded"
