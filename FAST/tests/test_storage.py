from fast.storage import ExperimentStore


def test_store_keys_results_by_stage_and_input_digest(tmp_path):
    store = ExperimentStore(tmp_path / "db" / "fast.db")
    output_digest = store.put("exp/candidate", "kernel", {"x": 8}, {"ok": True})
    found = store.get("exp/candidate", "kernel", "bad-digest")
    assert found is None

    from fast.schemas.models import digest_json

    found = store.get("exp/candidate", "kernel", digest_json({"x": 8}))
    assert found == {"ok": True}
    assert len(output_digest) == 64
