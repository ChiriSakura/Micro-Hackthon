"""Versioned, JSON-safe contracts exchanged by the five FAST agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


SCHEMA_VERSION = "0.1"


class Status(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Layer(str, Enum):
    KERNEL = "kernel"
    COMPILER = "compiler"
    UARCH = "uarch"
    EVALUATOR = "evaluator"
    INFRASTRUCTURE = "infrastructure"


class Decision(str, Enum):
    CONTINUE = "continue"
    REVERT = "revert"
    STOP = "stop"


@dataclass(frozen=True)
class Budget:
    max_candidates: int = 1
    max_evaluations: int = 1
    max_wall_seconds: int = 1800
    max_cloud_usd: float = 0.0

    def __post_init__(self) -> None:
        if min(self.max_candidates, self.max_evaluations, self.max_wall_seconds) <= 0:
            raise ValueError("count and wall-clock budgets must be positive")
        if self.max_cloud_usd < 0:
            raise ValueError("max_cloud_usd cannot be negative")


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    candidate_id: str
    model: str
    dataset: str
    sequence_length: int
    sparsity_x: int
    sparsity_m: int
    epsilon: float
    seed: int
    budget: Budget = field(default_factory=Budget)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("experiment_id", "candidate_id", "model", "dataset"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be empty")
        if self.sequence_length <= 0:
            raise ValueError("sequence_length must be positive")
        if not 0 < self.sparsity_x <= self.sparsity_m:
            raise ValueError("sparsity must satisfy 0 < X <= M")
        if self.epsilon < 0:
            raise ValueError("epsilon cannot be negative")

    @property
    def digest(self) -> str:
        return digest_json(self)


@dataclass(frozen=True)
class KernelResult:
    status: Status
    baseline_metric: float
    candidate_metric: float
    metric_name: str
    quality_loss: float
    actual_sparsity: float
    index_entropy: float
    block_occupancy: float
    trace_uri: str
    evidence: tuple[str, ...] = ()
    error: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class CompilerSchedule:
    status: Status
    tile_q: int
    tile_k: int
    tile_d: int
    loop_order: tuple[str, ...]
    data_layout: str
    parallelism: int
    predicted_utilization: float
    predicted_bytes: int
    rationale: tuple[str, ...] = ()
    error: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class HardwareCandidate:
    status: Status
    template_id: str
    template_digest: str
    verified_template: bool
    pe_rows: int
    pe_cols: int
    queue_depth: int
    sram_bytes: int
    data_width: int
    manifest_uri: str
    error: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class EvaluationResult:
    status: Status
    fidelity: str
    functional_passed: bool
    cycles: int | None
    throughput: float | None
    pe_utilization: float | None
    area: float | None
    power: float | None
    edp: float | None
    wall_seconds: float
    cloud_cost_usd: float
    log_uri: str
    evidence: tuple[str, ...] = ()
    error: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class Mutation:
    layer: Layer
    field: str
    operation: str
    value: int | float | str
    expected_effect: str
    risk: str


@dataclass(frozen=True)
class Critique:
    status: Status
    attribution: Layer
    decision: Decision
    summary: str
    evidence: tuple[str, ...]
    mutations: tuple[Mutation, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("a critique must cite at least one evidence field")


@dataclass(frozen=True)
class RunReport:
    spec: ExperimentSpec
    kernel: KernelResult
    compiler: CompilerSchedule | None
    hardware: HardwareCandidate | None
    evaluation: EvaluationResult | None
    critique: Critique
    cache_hits: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION


def to_primitive(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_primitive(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): to_primitive(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_primitive(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(to_primitive(value), sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def run_report_from_dict(data: dict[str, Any]) -> RunReport:
    """Rehydrate a cached report without using unsafe pickle payloads."""
    spec_data = dict(data["spec"])
    spec_data["budget"] = Budget(**spec_data["budget"])
    spec = ExperimentSpec(**spec_data)

    kernel_data = dict(data["kernel"])
    kernel_data["status"] = Status(kernel_data["status"])
    kernel_data["evidence"] = tuple(kernel_data.get("evidence", ()))
    kernel = KernelResult(**kernel_data)

    compiler = None
    if data.get("compiler") is not None:
        compiler_data = dict(data["compiler"])
        compiler_data["status"] = Status(compiler_data["status"])
        compiler_data["loop_order"] = tuple(compiler_data.get("loop_order", ()))
        compiler_data["rationale"] = tuple(compiler_data.get("rationale", ()))
        compiler = CompilerSchedule(**compiler_data)

    hardware = None
    if data.get("hardware") is not None:
        hardware_data = dict(data["hardware"])
        hardware_data["status"] = Status(hardware_data["status"])
        hardware = HardwareCandidate(**hardware_data)

    evaluation = None
    if data.get("evaluation") is not None:
        evaluation_data = dict(data["evaluation"])
        evaluation_data["status"] = Status(evaluation_data["status"])
        evaluation_data["evidence"] = tuple(evaluation_data.get("evidence", ()))
        evaluation = EvaluationResult(**evaluation_data)

    critique_data = dict(data["critique"])
    critique_data["status"] = Status(critique_data["status"])
    critique_data["attribution"] = Layer(critique_data["attribution"])
    critique_data["decision"] = Decision(critique_data["decision"])
    critique_data["evidence"] = tuple(critique_data.get("evidence", ()))
    critique_data["mutations"] = tuple(
        Mutation(layer=Layer(item["layer"]), **{k: v for k, v in item.items() if k != "layer"})
        for item in critique_data.get("mutations", ())
    )
    critique = Critique(**critique_data)
    return RunReport(
        spec=spec,
        kernel=kernel,
        compiler=compiler,
        hardware=hardware,
        evaluation=evaluation,
        critique=critique,
        cache_hits=tuple(data.get("cache_hits", ())),
        schema_version=data.get("schema_version", SCHEMA_VERSION),
    )
