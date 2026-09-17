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
    # 规划用的解析代价模型自己。实测和预测偏离过大时，瓶颈不在任何一层
    # 硬件——在模型里。这个循环能自己发现这件事，是它比逐层调优强的地方
    # 之一；此前这类错误全靠人发现（SRAM 面积差 40 倍、EDP 缺时钟周期、
    # 功耗是任意单位）。
    PLANNER_MODEL = "planner_model"


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
    # 稀疏方法名（"xm" / "nm:16:64" / "topk:64" / ...）。硬件侧需要它：
    # bank 冲突取决于索引的**分布**，而分布由方法决定——同样的稀疏度，
    # xm 在 8 bank 下减速 2.14x 而 nm 只有 1.19x。
    sparse_method: str = "xm"
    evidence: tuple[str, ...] = ()
    error: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class KernelSearchSpace:
    """**一个给定算法**的配置空间。

    ## 算法是输入，不是搜索维度

    这一点曾经搞反过：`labels()` 原来把 xm / nm / topk 和 sanger / salo 全部
    枚举在一起，于是 Kernel Agent 在**选算法**。那不是这个系统要做的事——
    算法由使用者给定（DynaX 的是动态 X:M），要探索的是**它的配置**，以及
    为这个配置协同设计的架构。

    混在一起的连锁后果不止一处：`select_candidates` 有一条「先保方法族覆盖」
    的规则，它的全部目的就是让候选散布到不同算法上；Critic 在算法层的变异
    因此变成「换成 sanger」，而不是「换一组 X:M 参数」。

    ## 空间仍然是可枚举的

    proposer（尤其是 LLM）返回的是标签，不在这个集合里的标签在**测量之前**
    就被拒绝——所以一个幻觉配置的代价是零而且可见。

    ## 哪些算法能被搜

    `xm` / `nm` / `topk` 的配置在**标签语法里**（DynaX 的 runner 解析
    `xm:N1:N2:M`、`nm:N:M`、`topk:K`），所以它们的配置空间可枚举。

    `sanger` 和 `salo` 不行，原因是结构性的而不是我们没写：sanger 的阈值是
    runner 的一个**全局参数** `--threshold-sanger`（一次运行一个值，不进标签），
    salo 的五个参数（match_size / pe_size / global_nums / random_nums /
    dilation）硬编码在 `gen_sparsity_mask_salo` 的函数体里。它们因此只能作为
    **基线**整体跑一次，不能在这里被搜索——所以放在 `baselines()` 而不是
    `labels()` 里，两者不混。
    """

    algorithm: str = "xm"
    block_m: int = 64
    xm_high: tuple[int, ...] = (8, 16, 32, 64)
    xm_low: tuple[int, ...] = (4, 8, 16, 32)
    nm_kept: tuple[int, ...] = (4, 8, 16, 32)
    topk: tuple[int, ...] = (32, 64, 128, 256)
    max_sequence_length: int = 4096
    # None keeps the legacy single-M, implicit-threshold baseline. Rediscovery
    # supplies ALL domains explicitly and uses six-field labels throughout.
    block_ms: tuple[int, ...] | None = None
    threshold_pairs: tuple[tuple[float, float], ...] | None = None
    schema_version: str = SCHEMA_VERSION

    #: 配置在标签语法里、因而可枚举的算法。
    SEARCHABLE = ("xm", "nm", "topk")
    #: 只能整体跑一次做对照的算法，理由见类文档。
    BASELINES = ("sanger", "salo")

    def __post_init__(self) -> None:
        name = self.algorithm.strip()
        if not name:
            raise ValueError("algorithm cannot be empty")
        if name not in self.SEARCHABLE:
            hint = (
                f"{name} 的配置不在标签语法里，只能作为基线整体跑"
                if name in self.BASELINES else
                f"未知算法；可搜索的是 {', '.join(self.SEARCHABLE)}"
            )
            raise ValueError(f"cannot search the configuration space of {name!r}: {hint}")
        import math
        if self.block_ms is not None and (not self.block_ms or any(
                not isinstance(m, int) or isinstance(m, bool) or m <= 0
                for m in self.block_ms)):
            raise ValueError("block_ms must contain positive integers")
        if self.threshold_pairs is not None and (not self.threshold_pairs or any(
                len(pair) != 2 or not all(math.isfinite(t) for t in pair)
                or not 0 <= pair[1] <= pair[0] for pair in self.threshold_pairs)):
            raise ValueError("threshold_pairs require finite 0 <= T1 <= T0")

    def labels(self) -> tuple[str, ...]:
        """这个算法的全部合法配置，用 DynaX runner 接受的标签语法。"""
        if self.algorithm == "xm":
            out = [
                f"xm:{high}:{low}:{m}" +
                (f":{float(thresholds[0]):g}:{float(thresholds[1]):g}" if thresholds else "")
                for m in (self.block_ms if self.block_ms is not None else (self.block_m,))
                for high in self.xm_high for low in self.xm_low
                for thresholds in (self.threshold_pairs if self.threshold_pairs is not None else (None,))
                # X:M 在质量大的 block 保留 `high` 个、小的保留 `low` 个，
                # 所以 low > high 不是一个配置。
                if 0 < low <= high <= m and self.max_sequence_length % m == 0
            ]
        elif self.algorithm == "nm":
            out = [f"nm:{kept}:{m}" for m in (self.block_ms or (self.block_m,))
                   for kept in self.nm_kept
                   if 0 < kept <= m and self.max_sequence_length % m == 0]
        else:  # topk
            out = [f"topk:{k}" for k in self.topk if k <= self.max_sequence_length]
        return tuple(dict.fromkeys(out))

    def baselines(self) -> tuple[str, ...]:
        """对照用的算法。**不参与搜索**——它们各自跑一次，用来比较。"""
        return self.BASELINES

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
    # 阵列高度 -> tile 内不均衡度。**这才是脉动阵列感受到的那个量**：
    # 共享同一个 tile 的那 numRows 行之间的差异。上面的 `load_imbalance`
    # 是整行、全序列、跨头拍平的全局极值，主要在反映因果斜坡——两者连
    # 排序都不一样（实测：全局量把完美均衡的 N:M 排在 topk 之前，实际
    # 正好相反）。详见 `DynaX/models/utils/sparsity_stats.py` 的注记。
    tile_load_imbalance: tuple[tuple[int, float], ...] = ()
    schema_version: str = SCHEMA_VERSION

    def tile_imbalance_measured(self, num_rows: int) -> float | None:
        """实测的 tile 内不均衡度；**没测到就返回 None**。

        存在的理由是 `tile_imbalance_for` 的回退值和测量值长得一模一样，
        而两者差得很远：同一个 `xm:32:16:64`，全局 `load_imbalance` 是 2.666、
        实测 tile(32) 是 **1.425**，回退放大 1.87 倍。**排序也不一样**——
        按全局 `xm:32:32:64` 排第 4，按实测 tile 排第 2。

        这个洞真的害到过：一整轮归因、一条 Critic 的换候选规则、还有两份文档
        里的数字，都建立在旧报告（`tile_load_imbalance = None`）的回退值上，
        被当成实测引用。要把这个量喂给模型、或者拿它做决策，用这个方法，
        拿到 None 就说「没测到」，不要拿回退值冒充测量。
        """
        if not self.tile_load_imbalance:
            return None
        table = dict(self.tile_load_imbalance)
        if num_rows in table:
            return table[num_rows]
        nearest = min(table, key=lambda rows: abs(rows - num_rows))
        return table[nearest]

    def tile_imbalance_for(self, num_rows: int) -> float:
        """给定阵列高度下的 tile 内不均衡度，没测到就退回全局值。

        没有记录时退回全局的 `load_imbalance`——那是个**偏悲观**的替代
        （实测放大 1.9-2.5 倍），而且排序可能是错的。老的运行结果里没有这个
        字段，退回是为了让它们仍然能读，不是因为退回值可用。

        **需要区分「测到了」和「退回了」的调用方用
        `tile_imbalance_measured()`**——它没测到时返回 None。
        """
        measured = self.tile_imbalance_measured(num_rows)
        return self.load_imbalance if measured is None else measured

    @property
    def balanced(self) -> bool:
        """最忙的行不超过平均的 25%，就可以照原样调度。

        判的是 **tile 内**的不均衡度：阵列被迫同步的边界在 tile，
        tile 之外的行长差异它碰不到。用全局那个量会把按构造完美均衡的
        N:M（tile 内 1.00、全局 1.83）判成不均衡。
        """
        return self.tile_imbalance_for(32) <= 1.25


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
    # 交给下游的候选集。proposal 里 Kernel Agent 的产出是「map the
    # sparsity-accuracy Pareto frontier」和复数的 sparse-index profiles，
    # 不是一个赢家——Compiler 和 µArch 要在这些点上联合搜索。
    candidates: tuple[KernelMeasurement, ...] = ()
    # 拿不满要的个数时说明原因。不足额比默默凑数好：凑进来的点会被下游
    # 当成「Kernel 认为值得一试」的东西。
    candidate_shortfall: str | None = None
    schema_version: str = SCHEMA_VERSION


@dataclass(frozen=True)
class CompilerSchedule:
    """Compiler Agent（planner）产出的完整硬件计划。

    **它同时包含软件和硬件参数，这是刻意的。** 分开规划就等于分开优化，
    而这两者是双向耦合的：阵列形状限制并行度，SRAM 容量限制 tile 大小，
    队列深度和 bank 数直接决定周期数。一次搜索覆盖全部参数，耦合就是
    结构上保证的，不可能被绕过。

    µArch Agent 拿到这份计划**只负责实现它**——检索模板、组合、仿真——
    不再自己推导任何参数。「造什么」和「怎么造」由此分开。
    """

    status: Status
    # ---- 软件侧：数据流与调度 ------------------------------------------
    tile_q: int
    tile_k: int
    tile_d: int
    loop_order: tuple[str, ...]
    data_layout: str
    parallelism: int
    predicted_utilization: float
    predicted_bytes: int

    # ---- 硬件侧：planner 决定造什么 ------------------------------------
    #
    # 这些以前散在 `CoDesignPoint` 和 µArch 的默认参数里。放进计划之后，
    # 「谁决定阵列是 32x4」这个问题有了唯一答案。
    num_rows: int = 32
    pe_per_row: int = 4
    reg_width: int = 8
    data_width: int = 16
    sram_bytes: int = 65_536
    queue_depth: int = 2
    divider_stages: int = 8
    bank_count: int = 8
    block_m: int = 64
    kept_per_block: int = 16

    # ---- 规划时的预测值 --------------------------------------------------
    #
    # 留着和实测对照。**两者的差距本身是一条可归因的结论**：模型说 2.23 ns
    # 而综合说 3.14 ns，说明瓶颈不在任何一层硬件，在代价模型本身。
    # 这一轮反复撞到的正是这类（SRAM 面积差 40 倍、EDP 缺时钟周期、
    # 功耗是任意单位），此前都靠人发现。
    predicted_cycles: float | None = None
    predicted_area_um2: float | None = None
    predicted_power_mw: float | None = None
    predicted_clock_ns: float | None = None

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

    # 频率下限，MHz。**这个字段一直存在，但从来没在 `violations()` 里生效过**
    # ——又一个「有约束但不咬人」的实例，和 queue_depth 不收面积是同一个形状。
    # 实测关键路径有了之后它可以真的生效。
    #
    # 默认从 500 改成 350，理由是实测：
    #
    #     执行阵列本身          2.230 ns = 448 MHz   <- 硬上限就在这里
    #     + queue_depth=2       2.528 ns = 396 MHz
    #     + queue_depth=4       2.760 ns = 362 MHz
    #     + queue_depth=8       3.140 ns = 319 MHz
    #
    # **论文的 500 MHz 在这条 Nangate45（45nm）流程上达不到**——论文是 28nm，
    # 节点不同，这在预期内。但如果把 500 当硬约束，每一个设计点都会被判不可行。
    # 350 MHz 能放过深度 0/2/4、拒掉深度 8，是一个真的能区分设计的门槛。
    target_mhz: float = 350.0

    # 功耗上限，mW。None = 不约束。功耗此前是任意单位（32x4 算出 2.85 而实测
    # 398.7 mW），没法写预算；换成 mW 之后才有意义。
    max_power_mw: float | None = None

    data_widths: tuple[int, ...] = (8, 16)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if min(self.max_pe, self.max_sram_bytes) <= 0 or self.max_area_um2 <= 0:
            raise ValueError("architecture budgets must be positive")
        if self.target_mhz <= 0:
            raise ValueError("target_mhz must be positive")
        if self.max_power_mw is not None and self.max_power_mw <= 0:
            raise ValueError("max_power_mw must be positive when set")
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
    # 这一轮 µArch 改了哪个 Chisel 模块、过没过门（`MutationOutcome`）。
    # **失败的尝试也留**：哪个模块在第几次失败、门给的诊断是什么，正是
    # 「归因到 µArch 层」下一轮需要的证据。None = 这一轮没有变异 RTL。
    mutation: Any = None
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
