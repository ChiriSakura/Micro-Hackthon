from __future__ import annotations

import json

from models.utils.runtime_config import DEFAULT_CONFIG_PATH, load_dynax_config


REQUIRED_KEYS = {
    "is_sparse",
    "is_quant",
    "sparse_methed",
    "quant_methed",
    "m",
    "n",
    "threshold_0",
    "threshold_1",
    "threshold_sanger",
    "topk",
}


def test_default_config_is_resolved_relative_to_source(monkeypatch):
    monkeypatch.delenv("DYNAX_CONFIG_PATH", raising=False)
    config = load_dynax_config()

    assert DEFAULT_CONFIG_PATH.is_file()
    assert REQUIRED_KEYS <= config.keys()


def test_per_run_config_overrides_repository_default(tmp_path, monkeypatch):
    candidate_config = tmp_path / "candidate.json"
    expected = {"candidate": "golden", "is_sparse": False}
    candidate_config.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.setenv("DYNAX_CONFIG_PATH", str(candidate_config))

    assert load_dynax_config() == expected
