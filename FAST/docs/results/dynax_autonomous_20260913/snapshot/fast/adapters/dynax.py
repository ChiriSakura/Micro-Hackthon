"""Kernel adapter that measures a candidate with the real DynaX implementation.

The adapter shells out to ``DynaX/run_eval_matrix.py`` so the measurement runs
in DynaX's own pinned environment and can be dispatched to a Slurm allocation or
a remote worker through ``launcher``. Its only contract with the rest of FAST is
``KernelResult``.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import time
import tempfile

from fast.schemas.models import (
    ExperimentSpec,
    KernelCandidate,
    KernelMeasurement,
    KernelProfile,
    KernelResult,
    Status,
)


@dataclass(frozen=True)
class DynaXKernelAdapter:
    """Run one dense/sparse comparison and normalise it into ``KernelResult``."""

    dynax_root: Path
    run_root: Path
    python_executable: str = "python"
    launcher: tuple[str, ...] = ()
    device: str = "auto"
    timeout_seconds: int = 7200
    env: dict[str, str] | None = None

    def method_label(self, spec: ExperimentSpec) -> str:
        if spec.sparse_method == "xm":
            n1, n2, m = spec.xm_budget
            return f"xm:{n1}:{n2}:{m}"
        if spec.sparse_method == "nm":
            return f"nm:{spec.sparsity_x}:{spec.sparsity_m}"
        if spec.sparse_method == "topk":
            return f"topk:{spec.sparsity_x}"
        return spec.sparse_method

    def command(
        self, spec: ExperimentSpec, run_dir: Path, methods: list[str] | None = None
    ) -> list[str]:
        return [
            *self.launcher,
            self.python_executable,
            str(Path(self.dynax_root) / "run_eval_matrix.py"),
            "--model", spec.model,
            "--dataset", _dataset_flag(spec.dataset),
            "--seq-len", str(spec.sequence_length),
            "--max-samples", str(spec.max_samples),
            "--methods", ",".join(methods or ["dense", self.method_label(spec)]),
            "--dtype", spec.dtype,
            "--device", self.device,
            "--seed", str(spec.seed),
            "--run-dir", str(run_dir),
        ]

    def measure(
        self, spec: ExperimentSpec, candidates: tuple[KernelCandidate, ...]
    ) -> tuple[tuple[KernelMeasurement, ...], float | None]:
        """Measure a whole round in one process.

        Loading the model dominates the cost - tens of seconds against about ten
        per configuration - so a round is one subprocess with every label on the
        command line, sharing one dense baseline.
        """
        if not candidates:
            return (), None
        labels = [item.label for item in candidates]
        parent = Path(self.run_root) / spec.experiment_id / spec.candidate_id
        parent.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix="kernel_round_", dir=parent))
        command = self.command(spec, run_dir, methods=["dense", *labels])
        completed = subprocess.run(
            command,
            cwd=str(self.dynax_root),
            env={**os.environ, **(self.env or {})},
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        (run_dir / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(completed.stderr, encoding="utf-8")

        results_path = run_dir / "results.json"
        if not results_path.is_file():
            reason = f"DynaX produced no results.json (exit code {completed.returncode})"
            return tuple(_unmeasured(item, reason) for item in candidates), None

        payload = json.loads(results_path.read_text(encoding="utf-8"))
        if payload.get("manifest", {}).get("methods_requested", ["dense", *labels]) != ["dense", *labels]:
            return tuple(_unmeasured(item, "measurement identity mismatch") for item in candidates), None
        records = {item["method"]: item for item in payload["results"]}
        dense = records.get("dense")
        baseline = dense.get("perplexity") if dense and dense.get("status") == "passed" else None

        measurements = []
        for candidate in candidates:
            record = records.get(candidate.label)
            if record is None:
                measurements.append(_unmeasured(candidate, "missing from results.json"))
                continue
            if record.get("status") != "passed":
                measurements.append(_unmeasured(candidate, record.get("error") or "measurement failed"))
                continue
            stats = _method_stats(record)
            loss = record.get("relative_quality_loss")
            measurements.append(
                KernelMeasurement(
                    label=candidate.label,
                    status=Status.PASSED,
                    perplexity=record.get("perplexity"),
                    # A configuration that beats dense is not charged a loss.
                    quality_loss=max(0.0, loss) if loss is not None else None,
                    actual_sparsity=stats.get("mean_sparsity", 0.0),
                    index_entropy=stats.get("mean_index_entropy", 0.0),
                    block_occupancy=stats.get("mean_block_occupancy", 0.0),
                    row_kept_min=stats.get("row_kept_min"),
                    row_kept_max=stats.get("row_kept_max"),
                    wall_seconds=record.get("wall_seconds"),
                    profile=_profile(stats),
                    proposed_by=candidate.proposed_by,
                    rationale=candidate.rationale,
                )
            )
        return tuple(measurements), baseline

    def evaluate(self, spec: ExperimentSpec) -> KernelResult:
        run_dir = Path(self.run_root) / spec.experiment_id / spec.candidate_id / "kernel"
        run_dir.mkdir(parents=True, exist_ok=True)
        command = self.command(spec, run_dir)
        environment = {**os.environ, **(self.env or {})}
        started = time.time()
        completed = subprocess.run(
            command,
            cwd=str(self.dynax_root),
            env=environment,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        (run_dir / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        results_path = run_dir / "results.json"

        if not results_path.is_file():
            return _failed(
                spec,
                run_dir,
                f"DynaX produced no results.json (exit code {completed.returncode})",
            )
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        records = {item["method"]: item for item in payload["results"]}
        label = self.method_label(spec)
        dense = records.get("dense")
        candidate = records.get(label)
        if dense is None or candidate is None:
            return _failed(spec, run_dir, f"results.json is missing dense or {label}", label)
        if dense["status"] != "passed" or candidate["status"] != "passed":
            reason = candidate.get("error") or dense.get("error") or "measurement failed"
            return _failed(spec, run_dir, reason, label)

        stats = _method_stats(candidate)
        relative_delta = (candidate["perplexity"] - dense["perplexity"]) / dense["perplexity"]
        # A candidate that beats the dense baseline is not charged a quality loss.
        quality_loss = max(0.0, relative_delta)
        within_budget = quality_loss <= spec.epsilon
        return KernelResult(
            status=Status.PASSED if within_budget else Status.FAILED,
            baseline_metric=dense["perplexity"],
            candidate_metric=candidate["perplexity"],
            metric_name=f"{spec.dataset}_perplexity",
            quality_loss=quality_loss,
            actual_sparsity=stats.get("mean_sparsity", 0.0),
            index_entropy=stats.get("mean_index_entropy", 0.0),
            block_occupancy=stats.get("mean_block_occupancy", 0.0),
            trace_uri=results_path.as_uri(),
            # 硬件侧靠它查 bank 冲突：冲突取决于索引的**分布**，而分布由
            # 方法决定（实测 8 bank 下 nm 减速 1.19x、xm 2.14x）。不填的话
            # `gather_slowdown()` 对每个 kernel 都退回 xm——恰好是最差的那档。
            sparse_method=label,
            profile=_profile(stats),
            evidence=(
                f"dense_perplexity={dense['perplexity']:.6f}",
                f"candidate_perplexity={candidate['perplexity']:.6f}",
                f"relative_perplexity_delta={relative_delta:.6f}",
                f"windows={candidate.get('windows')}",
                f"tokens={candidate.get('tokens')}",
                f"attention_calls={stats.get('calls')}",
                f"wall_seconds={candidate.get('wall_seconds')}",
                f"config_digest={candidate.get('config_digest')}",
                f"measured_in={round(time.time() - started, 1)}s",
            ),
            error=None if within_budget else "relative perplexity loss exceeds epsilon",
        )


def _dataset_flag(dataset: str) -> str:
    """Map a dataset identifier onto the DynaX ``--dataset`` choices."""
    lowered = dataset.lower()
    if "wiki" in lowered:
        return "wiki"
    if "ptb" in lowered or "penn" in lowered:
        return "ptb"
    if "c4" in lowered:
        return "c4"
    raise ValueError(f"dataset {dataset!r} has no DynaX loader; expected wikitext, ptb or c4")


def _method_stats(record: dict) -> dict:
    stats = record.get("sparsity_stats") or {}
    if not stats:
        return {}
    return next(iter(stats.values()))


def _failed(spec: ExperimentSpec, run_dir: Path, reason: str,
            label: str | None = None) -> KernelResult:
    return KernelResult(
        status=Status.FAILED,
        # 失败的记录也要带方法名：事后排查「哪个方法跑不起来」靠的就是它。
        sparse_method=label or spec.sparse_method,
        baseline_metric=0.0,
        candidate_metric=0.0,
        metric_name=f"{spec.dataset}_perplexity",
        quality_loss=0.0,
        actual_sparsity=0.0,
        index_entropy=0.0,
        block_occupancy=0.0,
        trace_uri=run_dir.as_uri(),
        evidence=(f"stderr={(run_dir / 'stderr.log').as_uri()}",),
        error=reason,
    )


def _profile(stats: dict) -> KernelProfile | None:
    """Lift DynaX's recorded distributions into the typed profile.

    Returns None rather than a zero-filled profile when the run predates the
    distribution recorder, so a caller can tell "not measured" from "balanced".
    """
    if "row_density_histogram" not in stats:
        return None

    def ordered(mapping: dict | None) -> tuple[float, ...]:
        if not mapping:
            return ()
        return tuple(mapping[key] for key in sorted(mapping, key=int))

    return KernelProfile(
        histogram_bins=stats.get("histogram_bins", 32),
        row_density_histogram=tuple(stats.get("row_density_histogram", ())),
        block_density_histogram=tuple(stats.get("block_density_histogram", ())),
        load_imbalance=stats.get("mean_load_imbalance", 0.0),
        column_top1_mass=stats.get("column_top1_mass", 0.0),
        column_top5_mass=stats.get("column_top5_mass", 0.0),
        column_top10_mass=stats.get("column_top10_mass", 0.0),
        per_layer_kept_ratio=ordered(stats.get("per_layer_mean_kept_ratio")),
        per_layer_load_imbalance=ordered(stats.get("per_layer_mean_load_imbalance")),
        # 阵列高度 -> tile 内不均衡度。老的统计文件没有这个键，那时
        # 元组为空，`tile_imbalance_for()` 会退回全局量并在文档里说明
        # 那是偏悲观的替代——不是静默地用一个错的数。
        tile_load_imbalance=tuple(
            (int(rows), float(value))
            for rows, value in sorted(
                (stats.get("mean_tile_load_imbalance") or {}).items(), key=lambda kv: int(kv[0])
            )
        ),
    )


def _unmeasured(candidate: KernelCandidate, reason: str) -> KernelMeasurement:
    return KernelMeasurement(
        label=candidate.label,
        status=Status.FAILED,
        perplexity=None,
        quality_loss=None,
        actual_sparsity=0.0,
        index_entropy=0.0,
        block_occupancy=0.0,
        row_kept_min=None,
        row_kept_max=None,
        wall_seconds=None,
        proposed_by=candidate.proposed_by,
        rationale=candidate.rationale,
        error=reason,
    )
