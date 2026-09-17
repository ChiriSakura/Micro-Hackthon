"""Per-candidate run directory and manifest, following the plan's section 7.

Every candidate gets its own directory so that no two runs share mutable state,
and every artifact in it is checksummed so a later report can prove which bytes
produced which number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
from typing import Any

from fast.schemas.models import RunReport, SCHEMA_VERSION, digest_json, to_primitive


STAGE_FILES = {
    "kernel": "kernel_result.json",
    "compiler": "compiler_schedule.json",
    "hardware": "hardware_candidate.json",
    "evaluation": "evaluation_result.json",
    "critique": "critique.json",
}


def git_commit(path: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_is_dirty(path: Path) -> bool | None:
    try:
        output = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(output)


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def tool_versions() -> dict[str, str | None]:
    """Record the versions that a later reader would need to reproduce a run."""
    versions: dict[str, str | None] = {"python": platform.python_version()}
    for module in ("torch", "transformers", "datasets", "ray", "chia"):
        try:
            versions[module] = __import__(module).__version__
        except Exception:
            versions[module] = None
    for binary, flag in (("java", "-version"), ("verilator", "--version"), ("sbt", "--version")):
        versions[binary] = _binary_version(binary, flag)
    return versions


def _binary_version(binary: str, flag: str) -> str | None:
    try:
        completed = subprocess.run([binary, flag], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else None


@dataclass
class RunManifest:
    """Writes one candidate directory and its manifest."""

    root: Path
    repositories: dict[str, Path] = field(default_factory=dict)

    def candidate_dir(self, experiment_id: str, candidate_id: str) -> Path:
        return Path(self.root) / experiment_id / candidate_id

    def write(
        self,
        report: RunReport,
        *,
        started_at: str,
        finished_at: str,
        exit_code: int,
        failed_stage: str | None = None,
        retries: int = 0,
        cloud_cost_usd: float = 0.0,
        agent_tokens: int = 0,
        extra: dict[str, Any] | None = None,
    ) -> Path:
        directory = self.candidate_dir(report.spec.experiment_id, report.spec.candidate_id)
        (directory / "artifacts").mkdir(parents=True, exist_ok=True)

        stages = {
            "kernel": report.kernel,
            "compiler": report.compiler,
            "hardware": report.hardware,
            "evaluation": report.evaluation,
            "critique": report.critique,
        }
        written: dict[str, Path] = {}
        for stage, payload in stages.items():
            if payload is None:
                continue
            path = directory / STAGE_FILES[stage]
            path.write_text(json.dumps(to_primitive(payload), indent=2) + "\n", encoding="utf-8")
            written[stage] = path
        report_path = directory / "report.json"
        report_path.write_text(json.dumps(to_primitive(report), indent=2) + "\n", encoding="utf-8")
        written["report"] = report_path

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "experiment_id": report.spec.experiment_id,
            "candidate_id": report.spec.candidate_id,
            "config": to_primitive(report.spec),
            "config_digest": digest_json(report.spec),
            "report_digest": digest_json(report),
            "seed": report.spec.seed,
            "commits": {
                name: {"commit": git_commit(Path(path)), "dirty": git_is_dirty(Path(path))}
                for name, path in self.repositories.items()
            },
            "versions": tool_versions(),
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "command": " ".join(sys.argv),
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "failed_stage": failed_stage,
            "retries": retries,
            "cache_hits": list(report.cache_hits),
            "cloud_cost_usd": cloud_cost_usd,
            "agent_tokens": agent_tokens,
            "artifacts": {
                name: {"path": str(path), "checksum": file_checksum(path)}
                for name, path in sorted(written.items())
            },
            "external_artifacts": _external_artifacts(report),
            # The kernel measurement runs in DynaX's own environment, so its
            # versions and device come from the trace rather than from here.
            "kernel_environment": _kernel_environment(report),
        }
        if extra:
            manifest.update(extra)
        manifest_path = directory / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest_path


def _external_artifacts(report: RunReport) -> dict[str, Any]:
    """Checksum artifacts an adapter produced outside the candidate directory."""
    entries: dict[str, Any] = {}
    for name, uri in (
        ("kernel_trace", report.kernel.trace_uri),
        ("evaluation_log", report.evaluation.log_uri if report.evaluation else ""),
    ):
        if not uri.startswith("file://"):
            continue
        path = Path(uri[len("file://") :])
        entries[name] = {
            "uri": uri,
            "checksum": file_checksum(path) if path.is_file() else None,
            "exists": path.is_file(),
        }
    return entries


def _kernel_environment(report: RunReport) -> dict[str, Any] | None:
    """Lift the measurement manifest out of the kernel trace, when there is one."""
    uri = report.kernel.trace_uri
    if not uri.startswith("file://"):
        return None
    path = Path(uri[len("file://") :])
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("manifest")
    except (OSError, ValueError):
        return None


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
