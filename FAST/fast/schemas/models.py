"""Versioned, JSON-safe contracts exchanged by the five FAST agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any


SCHEMA_VERSION = "0.2"


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
    sparse_method: str = "xm"
    sparsity_x_high: int | None = None
    max_samples: int = 8
    dtype: str = "auto"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("experiment_id", "candidate_id", "model", "dataset", "sparse_method"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be empty")
        if self.sequence_length <= 0:
            raise ValueError("sequence_length must be positive")
        if not 0 < self.sparsity_x <= self.sparsity_m:
            raise ValueError("sparsity must satisfy 0 < X <= M")
        if self.sparsity_x_high is not None and not (
            self.sparsity_x <= self.sparsity_x_high <= self.sparsity_m
        ):
            raise ValueError("sparsity must satisfy X <= X_high <= M")
        if self.epsilon < 0:
            raise ValueError("epsilon cannot be negative")
        if self.max_samples <= 0:
            raise ValueError("max_samples must be positive")

    @property
    def xm_budget(self) -> tuple[int, int, int]:
        """Return the (n1, n2, m) budget the DynaX X:M kernel should use."""
        high = self.sparsity_x_high or min(self.sparsity_m, self.sparsity_x * 2)
        return high, self.sparsity_x, self.sparsity_m

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
    # The proposal makes the sparse-index profile the Kernel Agent's output and
    # the Compiler Agent's input, so it travels with the result, not beside it.
    profile: KernelProfile | None = None
    evidence: tuple[str, ...] = ()
    error: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class KernelSearchSpace:
    """The kernel configurations an agent is allowed to propose.

    The space is enumerable on purpose. A proposer - especially an LLM one -
    returns labels, and a label outside this set is rejected before anything is
    measured, so a hallucinated configuration costs nothing and is visible.
    """

    block_m: int = 64
    xm_high: tuple[int, ...] = (8, 16, 32, 64)
    xm_low: tuple[int, ...] = (4, 8, 16, 32)
    nm_kept: tuple[int, ...] = (4, 8, 16, 32)
    topk: tuple[int, ...] = (32, 64, 128, 256)
    include_baselines: tuple[str, ...] = ("sanger", "salo")
    max_sequence_length: int = 4096
    schema_version: str = SCHEMA_VERSION

    def labels(self) -> tuple[str, ...]:
        """Every legal method label, in the syntax DynaX's runner accepts."""
        out: list[str] = []
        for high in self.xm_high:
            for low in self.xm_low:
                # X:M keeps `high` per block where the mass is large and `low`
                # where it is small, so low > high is not a configuration.
                if low <= high <= self.block_m:
                    out.append(f"xm:{high}:{low}:{self.block_m}")
        out += [f"nm:{kept}:{self.block_m}" for kept in self.nm_kept if kept <= self.block_m]
        out += [f"topk:{k}" for k in self.topk if k <= self.max_sequence_length]
        out += list(self.include_baselines)
        return tuple(dict.fromkeys(out))

    def contains(self, label: str) -> bool:
        return label in set(self.labels())


@dataclass(frozen=True)
class KernelCandidate:
    """One configuration a proposer wants measured, with why it wants it."""

    label: str
    proposed_by: str
    rationale: tuple[str, ...] = ()
    expected_effect: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("candidate label cannot be empty")
        if not self.proposed_by.strip():
            raise ValueError("every candidate must record who proposed it")


@dataclass(frozen=True)
class KernelProfile:
    """The sparse-index profile the Compiler Agent schedules from.

    The proposal makes this the Kernel Agent's output, and it has to be a
    distribution rather than a mean: tiling and PE load balancing are decided by
    the shape of the sparsity, and an average hides exactly the imbalance that
    leaves a systolic array idle.

    Densities are normalised by each query row's own causal length, so the
    histograms describe the pruner's behaviour rather than re-drawing the
    causal triangle.
    """

    histogram_bins: int
    row_density_histogram: tuple[int, ...]
    block_density_histogram: tuple[int, ...]
    load_imbalance: float
    column_top1_mass: float
    column_top5_mass: float
    column_top10_mass: float
    per_layer_kept_ratio: tuple[float, ...] = ()
    per_layer_load_imbalance: tuple[float, ...] = ()
    schema_version: str = SCHEMA_VERSION

    @property
    def balanced(self) -> bool:
        """A busiest row within 25% of the average is schedulable as-is."""
        return self.load_imbalance <= 1.25


@dataclass(frozen=True)
class KernelMeasurement:
    """What DynaX actually reported for one candidate."""

    label: str
    status: Status
    perplexity: float | None
    quality_loss: float | None
    actual_sparsity: float
    index_entropy: float
    block_occupancy: float
    row_kept_min: float | None
    row_kept_max: float | None
    wall_seconds: float | None
    profile: KernelProfile | None = None
    proposed_by: str = ""
    rationale: tuple[str, ...] = ()
    error: str | None = None
    schema_version: str = SCHEMA_VERSION

    @property
    def within(self) -> bool:
        return self.status is Status.PASSED and self.quality_loss is not None


@dataclass(frozen=True)
class KernelSearchReport:
    """The whole search: what was proposed, what it measured, what survived."""

    spec: ExperimentSpec
    proposer: str
    baseline_metric: float | None
    measurements: tuple[KernelMeasurement, ...]
    pareto: tuple[str, ...]
    best: KernelMeasurement | None
    rounds: int
    rejected: tuple[str, ...] = ()
    wall_seconds: float = 0.0
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
class ArchSpecs:
    """The envelope the µArch Agent must design inside.

    Table II lists "arch specs" as a µArch input, and without it the agent has
    nothing to be constrained by: any schedule can be satisfied by asking for a
    bigger array. These are the budgets a real target imposes.
    """

    max_pe: int = 256
    max_sram_bytes: int = 512 * 1024
    # um^2，Nangate45。原来这里是任意的「area units」；面积模型按 yosys 实测
    # 标定之后，单位就是真实的 um^2 了，名字必须跟着改——一个还叫 units 却
    # 装着 um^2 的字段，正是这个项目在别处反复防的那种静默错配。
    #
    # 默认 4 mm^2：论文的 DynaX-S 是 28nm 下 1.08 mm^2，换算到 45nm 约
    # (45/28)^2 ≈ 2.6 倍，即 ~2.8 mm^2。4 mm^2 放得下 DynaX-S 规模的设计，
    # 也确实会拒掉明显超标的点，而不是形同虚设。
    max_area_um2: float = 4_000_000.0
    target_mhz: float = 500.0
    data_widths: tuple[int, ...] = (8, 16)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if min(self.max_pe, self.max_sram_bytes) <= 0 or self.max_area_um2 <= 0:
            raise ValueError("architecture budgets must be positive")
        if not self.data_widths:
            raise ValueError("at least one data width must be allowed")


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
    # Parameters of the DynaX Chisel modules this candidate would instantiate.
    # topk_m/topk_n are dictated by the kernel's block budget, not chosen freely:
    # TopK(m, n) builds n-1 comparator stages over an m-wide block.
    topk_m: int = 64
    topk_n: int = 16
    binary_point: int = 8
    reg_width: int = 32
    col_select_bits: int = 6
    area_units: float | None = None
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
    kernel_data["profile"] = kernel_profile_from_dict(kernel_data.get("profile"))
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


def kernel_profile_from_dict(data: dict[str, Any] | None) -> KernelProfile | None:
    if not data:
        return None
    payload = dict(data)
    for key in (
        "row_density_histogram", "block_density_histogram",
        "per_layer_kept_ratio", "per_layer_load_imbalance",
    ):
        payload[key] = tuple(payload.get(key, ()))
    return KernelProfile(**payload)


def kernel_measurement_from_dict(data: dict[str, Any]) -> KernelMeasurement:
    payload = dict(data)
    payload["status"] = Status(payload["status"])
    payload["rationale"] = tuple(payload.get("rationale", ()))
    payload["profile"] = kernel_profile_from_dict(payload.get("profile"))
    return KernelMeasurement(**payload)


def kernel_search_report_from_dict(data: dict[str, Any]) -> KernelSearchReport:
    spec_data = dict(data["spec"])
    spec_data["budget"] = Budget(**spec_data["budget"])
    measurements = tuple(kernel_measurement_from_dict(item) for item in data["measurements"])
    best = data.get("best")
    return KernelSearchReport(
        spec=ExperimentSpec(**spec_data),
        proposer=data["proposer"],
        baseline_metric=data.get("baseline_metric"),
        measurements=measurements,
        pareto=tuple(data.get("pareto", ())),
        best=kernel_measurement_from_dict(best) if best else None,
        rounds=data.get("rounds", 0),
        rejected=tuple(data.get("rejected", ())),
        wall_seconds=data.get("wall_seconds", 0.0),
        schema_version=data.get("schema_version", SCHEMA_VERSION),
    )
