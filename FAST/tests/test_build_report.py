"""The report generator must not mislabel which configurations are on the frontier."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "build_report", Path(__file__).resolve().parents[1] / "scripts" / "build_report.py"
)
build_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_report)


def _row(method, sparsity, loss, status="passed"):
    return {"method": method, "sparsity": sparsity, "relative_loss": loss, "status": status}


def test_frontier_keeps_only_configurations_nothing_dominates():
    rows = [
        _row("dense", 0.0, 0.0),
        _row("a", 0.90, 0.10),   # most sparse at its cost
        _row("b", 0.80, 0.02),   # cheapest at its sparsity
        _row("c", 0.70, 0.05),   # dominated by b: less sparse and more costly
        _row("d", 0.80, 0.09),   # dominated by b: same sparsity, higher cost
    ]

    assert build_report.pareto_front(rows) == {"a", "b"}


def test_dense_and_failed_rows_never_enter_the_frontier():
    rows = [
        _row("dense", 0.0, 0.0),
        _row("broken", 0.99, -1.0, status="failed"),
        _row("a", 0.50, 0.01),
    ]

    assert build_report.pareto_front(rows) == {"a"}


def test_a_single_candidate_is_its_own_frontier():
    assert build_report.pareto_front([_row("only", 0.5, 0.2)]) == {"only"}


@pytest.mark.parametrize(
    ("method", "family"),
    [("dense", "Dense"), ("xm", "X:M"), ("xm:32:16:64", "X:M"),
     ("nm:8:64", "N:M"), ("topk:128", "Top-K"), ("sanger", "Sanger"), ("salo", "SALO")],
)
def test_parametric_labels_are_grouped_by_family(method, family):
    assert build_report.family_of(method) == family


def _results_file(path: Path) -> Path:
    payload = {
        "manifest": {
            "model": "tiny", "dataset": "wiki", "sequence_length": 512, "parameters": 10,
            "hidden_layers": 2, "attention_heads": 2, "windows_evaluated": 4,
            "windows_available": 40, "seed": 1, "dtype": "torch.float32", "device": "cpu",
        },
        "results": [
            {"method": "dense", "status": "passed", "perplexity": 10.0, "wall_seconds": 1.0,
             "sparsity_stats": {}},
            {"method": "xm", "status": "passed", "perplexity": 11.0, "relative_quality_loss": 0.1,
             "wall_seconds": 2.0, "windows": 4, "tokens": 2044,
             "sparsity_stats": {"xm": {"calls": 4, "mean_sparsity": 0.9, "mean_index_entropy": 0.8,
                                       "mean_block_occupancy": 0.4, "row_kept_min": 8.0,
                                       "row_kept_max": 16.0,
                                       "per_layer_mean_kept_ratio": {"0": 0.1, "1": 0.12}}}},
            {"method": "salo", "status": "failed", "error": "boom", "sparsity_stats": {}},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_a_failed_measurement_is_rendered_as_failed_not_dropped(tmp_path):
    run = build_report.load_run(_results_file(tmp_path / "results.json"))

    assert [row["method"] for row in run["rows"]] == ["dense", "xm", "salo"]
    failed = run["rows"][2]
    assert failed["status"] == "failed" and failed["error"] == "boom"

    text = build_report.markdown([{**run, "pareto": sorted(build_report.pareto_front(run["rows"]))}])
    assert "| `salo` | failed |" in text
    assert "| `xm` | 11.0000 | +10.00% | 90.00%" in text
