from __future__ import annotations

import json
from pathlib import Path

import pytest

from fast.adapters.dynax import DynaXKernelAdapter
from fast.schemas.models import Budget, ExperimentSpec, Status


def spec(**changes) -> ExperimentSpec:
    from dataclasses import replace

    base = ExperimentSpec(
        experiment_id="adapter-test",
        candidate_id="x8-m64",
        model="tiny-llama",
        dataset="wikitext-2-raw-v1",
        sequence_length=128,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=0.05,
        seed=20260903,
        budget=Budget(),
        max_samples=2,
    )
    return replace(base, **changes)


def adapter(tmp_path: Path, **changes) -> DynaXKernelAdapter:
    return DynaXKernelAdapter(dynax_root=tmp_path / "DynaX", run_root=tmp_path / "runs", **changes)


def test_method_label_maps_the_spec_onto_dynax_flags(tmp_path):
    backend = adapter(tmp_path)
    assert backend.method_label(spec()) == "xm:16:8:64"
    assert backend.method_label(spec(sparsity_x_high=32)) == "xm:32:8:64"
    assert backend.method_label(spec(sparse_method="nm")) == "nm:8:64"
    assert backend.method_label(spec(sparse_method="topk")) == "topk:8"
    assert backend.method_label(spec(sparse_method="salo")) == "salo"


def test_command_requests_the_dense_baseline_alongside_the_candidate(tmp_path):
    command = adapter(tmp_path).command(spec(), tmp_path / "run")
    assert "--methods" in command
    assert command[command.index("--methods") + 1] == "dense,xm:16:8:64"
    assert command[command.index("--seq-len") + 1] == "128"
    assert command[command.index("--dataset") + 1] == "wiki"


def _write_results(run_dir: Path, dense_ppl: float, candidate_ppl: float, label: str = "xm:16:8:64") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "manifest": {"model": "tiny-llama"},
        "results": [
            {"method": "dense", "status": "passed", "perplexity": dense_ppl, "windows": 2, "tokens": 254},
            {
                "method": label,
                "status": "passed",
                "perplexity": candidate_ppl,
                "windows": 2,
                "tokens": 254,
                "wall_seconds": 1.5,
                "config_digest": "deadbeef",
                "sparsity_stats": {
                    "xm": {
                        "calls": 4,
                        "mean_sparsity": 0.82,
                        "mean_index_entropy": 0.91,
                        "mean_block_occupancy": 1.0,
                    }
                },
            },
        ],
    }
    (run_dir / "results.json").write_text(json.dumps(payload), encoding="utf-8")


class _FakeCompleted:
    returncode = 0
    stdout = "ok"
    stderr = ""


def _patched_adapter(tmp_path, monkeypatch, dense_ppl, candidate_ppl, label="xm:16:8:64"):
    backend = adapter(tmp_path)

    def fake_run(command, **kwargs):
        run_dir = Path(command[command.index("--run-dir") + 1])
        _write_results(run_dir, dense_ppl, candidate_ppl, label)
        return _FakeCompleted()

    monkeypatch.setattr("fast.adapters.dynax.subprocess.run", fake_run)
    return backend


def test_measurement_within_epsilon_passes_the_quality_gate(tmp_path, monkeypatch):
    backend = _patched_adapter(tmp_path, monkeypatch, 10.0, 10.2)
    result = backend.evaluate(spec())

    assert result.status is Status.PASSED
    assert result.quality_loss == pytest.approx(0.02)
    assert result.actual_sparsity == 0.82
    assert result.baseline_metric == 10.0
    assert result.trace_uri.startswith("file://")
    assert any("dense_perplexity" in item for item in result.evidence)


def test_measurement_outside_epsilon_fails_the_quality_gate(tmp_path, monkeypatch):
    backend = _patched_adapter(tmp_path, monkeypatch, 10.0, 12.0)
    result = backend.evaluate(spec())

    assert result.status is Status.FAILED
    assert result.error and "epsilon" in result.error


def test_a_candidate_better_than_dense_is_not_charged_a_loss(tmp_path, monkeypatch):
    backend = _patched_adapter(tmp_path, monkeypatch, 10.0, 9.5)
    result = backend.evaluate(spec())

    assert result.status is Status.PASSED
    assert result.quality_loss == 0.0


def test_a_missing_results_file_is_reported_as_a_failure(tmp_path, monkeypatch):
    backend = adapter(tmp_path)
    monkeypatch.setattr("fast.adapters.dynax.subprocess.run", lambda command, **kwargs: _FakeCompleted())
    result = backend.evaluate(spec())

    assert result.status is Status.FAILED
    assert result.error and "no results.json" in result.error
