from __future__ import annotations

import json

from fast.adapters import DeterministicEvaluationAdapter, DeterministicKernelAdapter
from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, TemplateRecord, UArchAgent
from fast.orchestrator import FiveAgentFlow
from fast.schemas.models import Budget, ExperimentSpec
from fast.storage import RunManifest, now


def _report(tmp_path):
    spec = ExperimentSpec(
        experiment_id="manifest-test",
        candidate_id="x8-m64",
        model="tiny-llama",
        dataset="wikitext-2-raw-v1",
        sequence_length=64,
        sparsity_x=8,
        sparsity_m=64,
        epsilon=0.01,
        seed=20260903,
        budget=Budget(),
    )
    template = TemplateRecord("sparse-pe", "sha256:test", "memory://sparse-pe", True)
    flow = FiveAgentFlow(
        KernelAgent(DeterministicKernelAdapter()),
        CompilerAgent(),
        UArchAgent((template,)),
        EvaluatorAgent(DeterministicEvaluationAdapter()),
        CriticAgent(),
    )
    return flow.run(spec, template_id="sparse-pe")


def test_manifest_records_every_stage_artifact_with_a_checksum(tmp_path):
    report = _report(tmp_path)
    path = RunManifest(root=tmp_path / "runs").write(
        report, started_at=now(), finished_at=now(), exit_code=0
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    directory = path.parent

    assert manifest["experiment_id"] == "manifest-test"
    assert manifest["config_digest"] and manifest["report_digest"]
    assert manifest["seed"] == 20260903
    assert set(manifest["artifacts"]) == {
        "kernel", "compiler", "hardware", "evaluation", "critique", "report",
    }
    for entry in manifest["artifacts"].values():
        assert entry["checksum"].startswith("sha256:")
    for name in ("kernel_result.json", "compiler_schedule.json", "hardware_candidate.json",
                 "evaluation_result.json", "critique.json", "report.json"):
        assert (directory / name).is_file()
    assert (directory / "artifacts").is_dir()
    assert manifest["versions"]["python"]


def test_each_candidate_gets_an_isolated_directory(tmp_path):
    manifest = RunManifest(root=tmp_path / "runs")
    first = manifest.candidate_dir("exp", "candidate-a")
    second = manifest.candidate_dir("exp", "candidate-b")
    assert first != second
    assert first.parent == second.parent


def test_kernel_environment_is_lifted_from_a_file_trace(tmp_path):
    from dataclasses import replace

    trace = tmp_path / "results.json"
    trace.write_text(json.dumps({"manifest": {"torch": "2.5.1", "device": "cuda"}, "results": []}), encoding="utf-8")
    report = _report(tmp_path)
    report = replace(report, kernel=replace(report.kernel, trace_uri=trace.as_uri()))

    path = RunManifest(root=tmp_path / "runs").write(
        report, started_at=now(), finished_at=now(), exit_code=0
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["kernel_environment"] == {"torch": "2.5.1", "device": "cuda"}
    assert manifest["external_artifacts"]["kernel_trace"]["exists"] is True


def test_a_memory_trace_leaves_the_kernel_environment_empty(tmp_path):
    report = _report(tmp_path)
    path = RunManifest(root=tmp_path / "runs").write(
        report, started_at=now(), finished_at=now(), exit_code=0
    )
    assert json.loads(path.read_text(encoding="utf-8"))["kernel_environment"] is None
