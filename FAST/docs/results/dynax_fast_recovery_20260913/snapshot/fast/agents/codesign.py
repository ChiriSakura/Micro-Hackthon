"""The coupled software-hardware space the Compiler and µArch Agents share.

The proposal has these two agents "jointly explore the coupled software-hardware
space", which a pipeline cannot do: a schedule is only meaningful against the
array that runs it, and an array is only sized correctly against the schedule it
serves. Tile size is bounded by SRAM; parallelism is bounded by array rows; the
predict unit's width is dictated by the kernel's per-block budget.

So the constraints live here rather than inside either agent - a rule that spans
two layers belongs to neither - and the search proposes *pairs*.

The analytical, first-order cost model screens candidates before expensive RTL
validation. Its predictions remain L1 evidence even when another stage has
independently verified a component; see docs/agent-architecture.md for scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import math

from fast.agents.templates import (
    gather_slowdown_provenance,
    ARRAY_CRITICAL_PATH_NS,
    divider_area_um2,
    divider_critical_path_ns,
    array_power_mw,
    bank_logic_area_um2,
    gather_slowdown,
    predict_array_area_um2,
    queue_area_um2,
    queue_critical_path_ns,
    queue_utilisation,
    TemplateRegistry,
    array_area_units,
    required_col_select_bits,
    sram_area_units,
    sram_leakage_mw,
    topk_area_units,
)
from fast.schemas.models import (
    ArchSpecs,
    CompilerSchedule,
    HardwareCandidate,
    KernelProfile,
    KernelResult,
    Status,
)


@dataclass(frozen=True)
class CoDesignPoint:
    """One schedule paired with the hardware that would run it."""

    tile_q: int
    tile_k: int
    tile_d: int
    parallelism: int
    double_buffer: bool
    num_rows: int
    pe_per_row: int
    reg_width: int
    data_width: int
    sram_bytes: int
    queue_depth: int
    # softmax 除法器的流水级数。0 = 上游的组合除法。
    # 它决定系统时钟：0 级 68 MHz，8 级 505 MHz（实测，Nangate45）。
    divider_stages: int = 0
    # K 取数引擎的 bank 数。实测维度：4 个 bank 时 xm 减速 3.05x，
    # 32 个 bank 降到 1.13x，代价是 regWidth x bankCount 的选择网络。
    bank_count: int = 8

    @property
    def mac_lanes(self) -> int:
        return self.num_rows * self.pe_per_row


@dataclass(frozen=True)
class CoDesignSpace:
    """What the joint search may vary. Small on purpose: every point is costed."""

    # ---- 单值维度：**代价模型分辨不了它们** -----------------------------
    #
    # 实测（每个维度单独变，看七个指标动不动）：
    #
    #     tile_q / tile_k / tile_d / parallelism / double_buffer
    #         -> cycles, area, power, seconds, edp, clock, dram_bytes 全不变
    #
    # 留成可搜索维度的后果不是"多探索一点"，是**更糟**：
    #
    #   - 5 个维度贡献 3x3x2x4x2 = 144 倍的空间膨胀，真实空间是 11,520
    #     而不是 1,658,880。搜索预算 99.3% 花在分辨不出差别的组合上。
    #   - LLM proposer 会认真地为它们编造理由（「把 tile_q 调到 128 以提高
    #     重用」），而那些理由**不可能被数据证伪**。
    #   - 等预算对比时，随机搜索和 LLM 在这 144 倍空白里的差异全是噪声。
    #
    # 这和「搜索维度必须有实测的成本侧」是同一条的极端形式：那条说的是
    # 只有收益没有成本的维度会让优化器走极端；这里是**既无收益也无成本**，
    # 优化器的每一次选择都是纯随机，而报告会写成"探索了 165 万个设计"。
    #
    # 要把它们加回来，先让代价模型真的算到它们：`tile_d` 应当影响重用和
    # 尾部损耗（`estimate()` 修正总工作量之后它就彻底没作用了），
    # `double_buffer` 应当影响驻留字节和面积，`tile_q/tile_k` 影响 tile 边界
    # 的开销。**接上成本侧再放开，不要反过来。**
    tile_q: tuple[int, ...] = (64,)
    tile_k: tuple[int, ...] = (64,)
    tile_d: tuple[int, ...] = (64,)
    parallelism: tuple[int, ...] = (8,)
    double_buffer: tuple[bool, ...] = (True,)
    num_rows: tuple[int, ...] = (4, 8, 16, 32)
    pe_per_row: tuple[int, ...] = (4, 8, 16, 32)
    reg_width: tuple[int, ...] = (16, 32, 64)
    queue_depth: tuple[int, ...] = (0, 2, 4, 8, 16)
    # 取数引擎的 bank 数。只取 2 的幂：bank 选择要用取模，非 2 的幂会引入
    # 一个除法器，那个除法器的关键路径会盖过冲突本身的代价。
    bank_count: tuple[int, ...] = (4, 8, 16, 32)
    # softmax 归一化器的除法器流水级数。这个维度是实测逼出来的：上游的
    # 组合除法（0 级）跑 68 MHz，而执行阵列能跑 450 MHz——时钟由除法器
    # 决定，可搜索空间里却没有一个维度和它有关，优化器一直在调一个不
    # 决定结果的变量。
    #
    # 取值来自 slurm 上的实测曲线（Nangate45，见 divider_profile）：
    # 8 级是第一个越过 500 MHz 的点，代价约 0.9% 的系统面积。
    divider_stages: tuple[int, ...] = (0, 4, 8, 12)
    sram_bytes: tuple[int, ...] = (65536, 131072, 262144)

    def points(self, specs: ArchSpecs, sram_choices: tuple[int, ...] | None = None):
        sram_choices = self.sram_bytes if sram_choices is None else sram_choices
        for tq in self.tile_q:
            for tk in self.tile_k:
                for td in self.tile_d:
                    for par in self.parallelism:
                        for rows in self.num_rows:
                            for cols in self.pe_per_row:
                                for regs in self.reg_width:
                                    for width in specs.data_widths:
                                        for sram in sram_choices:
                                            for queue in self.queue_depth:
                                              for div in self.divider_stages:
                                                for buffered in self.double_buffer:
                                                  for banks in self.bank_count:
                                                    yield CoDesignPoint(
                                                        tile_q=tq, tile_k=tk, tile_d=td,
                                                        parallelism=par, double_buffer=buffered,
                                                        num_rows=rows, pe_per_row=cols,
                                                        reg_width=regs, data_width=width,
                                                        sram_bytes=sram, queue_depth=queue,
                                                        divider_stages=div, bank_count=banks,
                                                    )


# 定点格式的小数位数。整个 RTL 栈是 Q8.8：`Elaborate.scala` 的 `Point = 8`，
# 每个模块的 `point` 参数都从那里来。它不是搜索维度——改它要重做全部金标准。
BINARY_POINT = 8


def tile_working_set_bytes(tile_q: int, tile_k: int, tile_d: int, data_width: int,
                           double_buffer: bool = False) -> int:
    """一个 tile 要驻留多少字节：一份 Q tile，加 K 和 V 各一份。

    抽成自由函数是因为 µArch Agent 也要算它——它拿到的是 `CompilerSchedule`
    而不是 `CoDesignPoint`。两边各写一遍同一个公式，迟早会分叉，而分叉的
    后果是「SRAM 够不够」这个判断在两条路径上给出不同答案。
    """
    per_element = data_width // 8
    tiles = tile_q + 2 * tile_k
    buffers = 2 if double_buffer else 1
    return tiles * tile_d * per_element * buffers


def working_set_bytes(point: CoDesignPoint) -> int:
    """Bytes a tile needs resident: one Q tile plus a K and a V tile."""
    return tile_working_set_bytes(
        point.tile_q, point.tile_k, point.tile_d, point.data_width, point.double_buffer
    )


#: Critic 的变异会用哪些名字指同一个计划参数。模型的措辞每轮都不同——
#: 实测同一个干预出现过 `queue`、`plan.queue`、`queue_depth` 三种写法。
#: 对格式宽容、对含义严格：认得出就执行，认不出就**明确报不支持**。
_PLAN_FIELD_ALIASES = {
    "queue": "queue_depth", "queue_depth": "queue_depth", "plan.queue": "queue_depth",
    "divider": "divider_stages", "divider_stages": "divider_stages",
    "plan.divider": "divider_stages",
    "banks": "bank_count", "bank_count": "bank_count", "plan.banks": "bank_count",
    "num_rows": "num_rows", "rows": "num_rows", "plan.rows": "num_rows",
    "pe_per_row": "pe_per_row", "pes": "pe_per_row",
    "reg_width": "reg_width", "data_width": "data_width",
    "sram_bytes": "sram_bytes", "parallelism": "parallelism",
    "tile_q": "tile_q", "tile_k": "tile_k",
}


#: 功耗模型**实际覆盖了什么**。
#:
#: 评审 P1-5：只有执行阵列动态功耗和 SRAM 漏电进了这个数。预测阵列
#: （PrePEArray_S 85.2 mW / _L 416.0 mW 实测）和执行阵列（RePEArray_S 398 mW）
#: 是**同一个量级**，漏掉它会系统性低估"预测重"的设计——而那正是这个
#: 架构族里最该被比较的差别。
#:
#: 为什么不直接加起来：这些实测值的**活动因子来源不一致**。执行阵列的
#: L 锚点明确记录用的是默认常数 0.200 而不是激励文件，只有 S 是金标准激励
#: 数出来的真实翻转率。预测阵列那两个数的来源查不到。把来源不一的数凑一个
#: 和，会把一个**已知的缺口**变成一个**看不见的误差**。
POWER_COVERAGE = {
    "included": ("execute-array-dynamic", "sram-leakage"),
    "excluded": ("predict-array", "topk", "block-scheduler", "divider",
                 "gather-engine", "dynamic-memory-energy"),
    "status": "partial",
    "why": "excluded terms have inconsistent activity-factor provenance",
}


@dataclass(frozen=True)
class PlanIntervention:
    """一条 compiler/planner_model 的变异**实际要做的事**。

    在有它之前，这两层的变异只设 `replan=True`，field / value /
    expected_effect **全被丢掉**——下一轮用同样的输入再调一次 `plan()`，
    规则 proposer 会确定性地给出完全相同的结果。「重入某层」不等于
    「执行了该层的建议」。

    这和 µArch 那条曾经犯过的错是同一个：不把变异交给下游，「重新实现」
    就只是再算一遍。

    实测的干预长这样：

        {"layer":"compiler","field":"queue","value":0}
        {"layer":"compiler","field":"clock_period_ns","value":2.3}

    前者是**钉住一个维度**，后者是**加一条约束**。两种都能执行。
    """

    #: 被钉住的搜索维度 -> 只允许的取值。
    pinned: dict[str, tuple] = field(default_factory=dict)
    #: 时钟周期上限，ns。None 表示这条干预没提。
    max_clock_ns: float | None = None
    #: 认不出来的部分，原样留着报出去。**不要静默丢弃**。
    unsupported: tuple[str, ...] = ()

    @property
    def actionable(self) -> bool:
        return bool(self.pinned) or self.max_clock_ns is not None

    def restrict(self, space: "CoDesignSpace") -> "CoDesignSpace":
        """把钉住的维度落到搜索空间上。

        钉住的值不在原空间里时**保留它**——Critic 有理由提一个空间外的值
        （比如实测发现 queue 0 更快），而悄悄忽略会让这一轮又变成空转。
        """
        if not self.pinned:
            return space
        changes = {}
        for name, values in self.pinned.items():
            if hasattr(space, name):
                changes[name] = tuple(values)
        return replace(space, **changes) if changes else space


def plan_intervention(mutations) -> PlanIntervention:
    """把 Critic 的变异翻译成可执行的规划干预。

    对格式宽容、对含义严格：字段名认别名（实测同一个干预出现过 `queue`、
    `plan.queue` 两种写法），认不出的原样记进 `unsupported` 报出去——
    评审的完成条件是「每项 mutation 确实执行**或明确报不支持**」。
    """
    pinned: dict[str, tuple] = {}
    max_clock: float | None = None
    unsupported: list[str] = []

    for mutation in mutations or ():
        layer = getattr(getattr(mutation, "layer", None), "value", "")
        if layer not in ("compiler", "planner_model"):
            continue
        raw_field = str(getattr(mutation, "field", "") or "").strip().lower()
        value = getattr(mutation, "value", None)

        # 时钟类字段按**含义**认，不按精确名字：实测出现过 `clock_period_ns`、
        # `predicted.clock`、`clock_period_constraint_ns` 三种写法，最后一种
        # 让一整轮以「unknown plan field」停掉。对格式宽容、对含义严格。
        #
        # **但周期和频率不是一回事。** 把 `max_frequency_mhz=400` 当成 400 ns
        # 的周期会得到一个荒谬的约束，而且不会有任何东西报错——这正是这个
        # 项目反复撞到的那类单位混用。按字段名区分，两种都认。
        is_frequency = "mhz" in raw_field or "freq" in raw_field
        is_period = "clock" in raw_field or "period" in raw_field
        if is_frequency or is_period:
            try:
                number = float(value)
            except (TypeError, ValueError):
                unsupported.append(f"{raw_field}={value!r} (not a number)")
                continue
            if number <= 0:
                unsupported.append(f"{raw_field}={value!r} (must be positive)")
                continue
            max_clock = (1000.0 / number) if is_frequency else number
            continue

        name = _PLAN_FIELD_ALIASES.get(raw_field)
        if name is None:
            unsupported.append(f"{raw_field}={value!r} (unknown plan field)")
            continue
        try:
            pinned[name] = (int(value),)
        except (TypeError, ValueError):
            unsupported.append(f"{raw_field}={value!r} (not an integer)")

    return PlanIntervention(pinned=pinned, max_clock_ns=max_clock,
                            unsupported=tuple(unsupported))


@dataclass(frozen=True)
class ObjectiveSpec:
    """Fixed-task latency/energy Pareto objective under hardware/quality constraints.

    `primary` selects a representative for a sequential build, never the whole
    result. Energy is J/task; its reciprocal is task/J. Partial energy estimates
    may guide exploration but must retain coverage and fidelity in reports.
    """

    primary: str = "seconds"
    pareto_axes: tuple[str, ...] = ("seconds", "energy_j")

    def __post_init__(self) -> None:
        allowed = {"seconds", "energy_j", "power", "area"}
        if not self.pareto_axes or len(set(self.pareto_axes)) != len(self.pareto_axes):
            raise ValueError("pareto_axes must be nonempty and unique")
        if not set(self.pareto_axes) <= allowed:
            raise ValueError("unknown Pareto axis")
        if self.primary not in self.pareto_axes:
            raise ValueError(
                f"primary={self.primary!r} 不在 pareto_axes={self.pareto_axes} 里"
                "——内层会朝一个不在最终判据里的方向优化"
            )

    def score(self, metrics: dict) -> float:
        """一个设计点的单值分数，**越小越好**。

        算不出来返回 +inf，让它排在最后；**不要返回 0**，那会让一个缺数据的
        点看起来最好。
        """
        value = metrics.get(self.primary)
        from fast.agents.pareto import valid_vector
        return float(value) if valid_vector((value,)) else float("inf")

    def vector(self, metrics: dict) -> tuple:
        return tuple(metrics.get(axis) for axis in self.pareto_axes)

    def dominates(self, a: dict, b: dict) -> bool:
        from fast.agents.pareto import dominates_vector
        return dominates_vector(self.vector(a), self.vector(b))


#: Minimise energy/task and latency/task; area, quality and frequency are constraints.
DEFAULT_OBJECTIVE = ObjectiveSpec()


@dataclass(frozen=True)
class DesignObjectives:
    """一个设计点在**约束优化**里的坐标。

        min  (L(x), E(x))               固定任务的延迟与能耗
        s.t. dAcc(x) <= epsilon         精度（Kernel 层的 ε 门已经保证）
             A(x)    <= A_max           面积
             P(x)    <= P_max           功耗
             f(x)    >= f_min           频率

    task 固定输入形状和质量门槛，允许稀疏算法减少实际执行的 MAC。
    E = P * L；最大化 task/J 等价于最小化 J/task。延迟排序仅用于展示，
    不能替代完整前沿。默认坐标来自模型，RTL 功能通过不等于 PPA 实测；
    功耗只覆盖执行阵列动态功耗和 SRAM 漏电，能耗也继承这个范围。
    """

    latency_ns: float | None
    power_mw: float | None
    area_um2: float | None
    throughput_mac_per_s: float | None
    clock_ns: float | None = None

    @property
    def energy_j(self) -> float | None:
        from fast.agents.pareto import valid_vector
        if not valid_vector((self.latency_ns, self.power_mw)):
            return None
        return self.latency_ns * self.power_mw * 1e-12

    @property
    def energy_efficiency_tasks_per_j(self) -> float | None:
        return 1.0 / self.energy_j if self.energy_j else None

    def complete_for(self, objective: "ObjectiveSpec | None" = None) -> bool:
        """这个点在**当前目标的每一根轴**上都有数。"""
        spec = objective or DEFAULT_OBJECTIVE
        from fast.agents.pareto import valid_vector
        return valid_vector(tuple(getattr(self, _AXIS_FIELD[name], None)
                                  for name in spec.pareto_axes))

    @property
    def complete(self) -> bool:
        return self.complete_for()


def design_objectives(plan, evaluation) -> DesignObjectives:
    """从一轮的计划和评估里取出目标坐标。

    算不出来的填 None，**不要补默认值**——补出来的数会让这个点在帕累托
    比较里占据它没有的位置，而那正是判"支配"的依据。
    """
    cycles = getattr(plan, "predicted_cycles", None)
    clock = getattr(plan, "predicted_clock_ns", None)
    latency = cycles * clock if cycles and clock else None
    return DesignObjectives(
        latency_ns=latency,
        clock_ns=clock,
        power_mw=getattr(plan, "predicted_power_mw", None),
        area_um2=getattr(plan, "predicted_area_um2", None),
        throughput_mac_per_s=throughput_mac_per_s(
            clock_ns=clock,
            num_rows=getattr(plan, "num_rows", None),
            pe_per_row=getattr(plan, "pe_per_row", None),
            utilisation=getattr(evaluation, "pe_utilization", None),
        ),
    )


def constraint_violations(objectives: DesignObjectives, specs) -> tuple[str, ...]:
    """Return violated or unverified active constraints; neither enters a feasible front."""
    from fast.agents.pareto import valid_vector
    out: list[str] = []
    limit = getattr(specs, "max_area_um2", None)
    if limit is not None:
        if not valid_vector((objectives.area_um2,)):
            out.append("area not measured or invalid; feasibility unverified")
        elif objectives.area_um2 > limit:
            out.append(f"area {objectives.area_um2:,.0f} > {limit:,.0f} um^2")
    limit = getattr(specs, "max_power_mw", None)
    if limit is not None:
        if not valid_vector((objectives.power_mw,)):
            out.append("power not measured or invalid; feasibility unverified")
        elif objectives.power_mw > limit:
            out.append(f"power {objectives.power_mw:,.1f} > {limit:,.1f} mW")
    target = getattr(specs, "target_mhz", None)
    if target:
        if not valid_vector((objectives.clock_ns,)):
            out.append("clock not measured or invalid; feasibility unverified")
        else:
            mhz = 1000.0 / objectives.clock_ns
            if mhz < target:
                out.append(f"clock {mhz:,.0f} < {target:,.0f} MHz")
    return tuple(out)


#: `ObjectiveSpec` 的轴名 -> `DesignObjectives` 的字段名。
_AXIS_FIELD = {"seconds": "latency_ns", "energy_j": "energy_j",
               "power": "power_mw", "area": "area_um2"}


def dominates(a: DesignObjectives, b: DesignObjectives,
              objective: "ObjectiveSpec | None" = None) -> bool:
    """a 在**所有**目标轴上不差于 b，且至少一个严格更好。

    轴由 `ObjectiveSpec` 给，不写死——「变好」只能有一个定义（评审 P1-3），
    而这里曾经硬编码 (延迟, 功耗)，和内层按 edp 排、外层按吞吐收敛各不相同。

    吞吐不上轴：固定工作量下它是延迟的另一面，放进来等于给同一根轴投两票。
    """
    spec = objective or DEFAULT_OBJECTIVE
    fields = [_AXIS_FIELD[name] for name in spec.pareto_axes if name in _AXIS_FIELD]
    values_a = [getattr(a, name, None) for name in fields]
    values_b = [getattr(b, name, None) for name in fields]
    # 任何一根轴上缺数就不判支配：补一个默认值会让这个点占据它没有的位置。
    from fast.agents.pareto import dominates_vector
    return dominates_vector(values_a, values_b)


def throughput_mac_per_s(
    *, clock_ns: float | None, num_rows: int | None, pe_per_row: int | None,
    utilisation: float | None,
) -> float | None:
    """循环在优化的那个标量：**面积约束下的吞吐**。

    有效 MAC/s = 频率 x 阵列规模 x 利用率。四个因子缺一个就返回 None——
    **不要用默认值补**：一个看起来像测量的占位数会让这个点在排序里占据它
    没有的位置，而排序正是判"有没有变好"的依据。

    ## 为什么是这个标量

    在此之前循环**没有目标函数**，只有验收门（功能通过、util >= 0.70、代价
    模型偏差 < 25%）。没有目标就没有"更好"，没有"更好"就没有"不再变好"——
    收敛判据因此无从定义，14 次运行里大半停在"轮数用完"。

    ## 为什么不能只看利用率

    利用率由 `queue_depth` 和 tile 不均衡度决定，**对阵列规模不敏感**：实测
    16x8 和 16x16 给出同一个 0.8503164429130726。只按利用率排，一个大一倍的
    阵列和一个小的看起来一样好，而它们的吞吐差一倍。
    """
    if not clock_ns or not num_rows or not pe_per_row or utilisation is None:
        return None
    return (1e9 / clock_ns) * num_rows * pe_per_row * utilisation


def violations(
    point: CoDesignPoint,
    kernel: KernelResult,
    specs: ArchSpecs,
    registry: TemplateRegistry | None = None,
    *,
    head_dim: int,
    block_m: int = 64,
    kept_per_block: int = 16,
) -> tuple[str, ...]:
    """Every reason this pair could not be built or run as described.

    Checked here rather than in either agent because each rule ties a software
    choice to a hardware one.
    """
    problems: list[str] = []

    if point.parallelism > point.num_rows:
        problems.append(
            f"parallelism={point.parallelism} exceeds num_rows={point.num_rows}: "
            "the schedule asks for more independent row lanes than the array has"
        )
    if point.tile_k % point.reg_width != 0:
        problems.append(
            f"tile_k={point.tile_k} is not a multiple of regWidth={point.reg_width}: "
            "the K tile cannot be streamed through the register file without a partial pass"
        )
    needed = working_set_bytes(point)
    if needed > point.sram_bytes:
        problems.append(
            f"working set {needed} B exceeds sram_bytes={point.sram_bytes}"
            f"{' (double buffered)' if point.double_buffer else ''}"
        )
    if point.sram_bytes > specs.max_sram_bytes:
        problems.append(f"sram_bytes={point.sram_bytes} exceeds the budget {specs.max_sram_bytes}")
    if point.mac_lanes > specs.max_pe:
        problems.append(f"{point.mac_lanes} MAC lanes exceed the PE budget {specs.max_pe}")
    if point.data_width not in specs.data_widths:
        problems.append(f"data_width={point.data_width} is not among {specs.data_widths}")
    # 定点格式是 Q(bits-point).point，binary point 固定在 8——所以 8 位数据
    # 宽度**一个整数位都不剩**，Chisel 直接拒绝：
    #
    #     requirement failed: need at least one integer bit: bits=8 point=8
    #
    # `ArchSpecs.data_widths` 默认含 8，planner 会挑它，然后设计 elaborate
    # 不出来。这条是「计划 -> 设计」那一步实测发现的：在此之前没有任何东西
    # 会把一份计划真的造成 Verilog，所以这个约束一直没机会暴露。
    if point.data_width <= BINARY_POINT:
        problems.append(
            f"data_width={point.data_width} leaves no integer bits above the "
            f"Q{BINARY_POINT} binary point; the fixed-point type needs at least one"
        )
    if kept_per_block > block_m:
        problems.append(f"kept_per_block={kept_per_block} exceeds the block width {block_m}")

    if registry is not None:
        array = registry.by_id("repe_array")
        if array is not None:
            problems.extend(array.admits(
                numRows=point.num_rows, peCountPerRow=point.pe_per_row,
                regWidth=point.reg_width, bits=point.data_width,
                colSelectBits=required_col_select_bits(block_m),
            ))
        topk = registry.by_id("topk")
        if topk is not None:
            problems.extend(topk.admits(m=block_m, n=kept_per_block, bits=point.data_width))

    area = area_units(point, block_m, kept_per_block, head_dim=head_dim)
    if area > specs.max_area_um2:
        problems.append(
            f"area {area:,.0f} um^2 exceeds the budget {specs.max_area_um2:,.0f} um^2"
        )

    # 频率与功耗此前不参与可行性判断——`target_mhz` 是个从没被读过的字段，
    # 功耗是任意单位没法设预算。两者现在都有实测支撑，所以让它们真的咬人。
    #
    # 频率约束特别锋利：它直接杀掉深的工作队列（深度 8 = 319 MHz），
    # 而那一档正是「只看利用率」会选中的。
    period_ns = clock_period_ns(point)
    achieved_mhz = 1000.0 / period_ns
    if achieved_mhz < specs.target_mhz:
        problems.append(
            f"clock {achieved_mhz:.0f} MHz (period {period_ns:.3f} ns) is below the "
            f"target {specs.target_mhz:.0f} MHz"
        )

    if specs.max_power_mw is not None:
        # 功耗依赖利用率，而利用率依赖 kernel 的 profile。拿不到 profile 时
        # 按满负荷算——**偏保守**，宁可拒掉一个其实可行的点，也不放过一个
        # 超预算的点。
        utilisation = pe_utilisation(
            kernel.profile, point.queue_depth, point.num_rows, point.pe_per_row
        ) if kernel.profile is not None else 1.0
        power = (
            array_power_mw(point.mac_lanes, utilisation, point.data_width)
            + sram_leakage_mw(point.sram_bytes)
        )
        if power > specs.max_power_mw:
            problems.append(
                f"power {power:.0f} mW exceeds the budget {specs.max_power_mw:.0f} mW"
            )

    return tuple(problems)


def clock_period_ns(point: CoDesignPoint) -> float:
    """系统时钟周期，ns——数据通路上最慢的那一段。

    三段都是 Nangate45 实测的，而且**三段都真的当过瓶颈**：执行阵列
    2.23 ns、除法器（0 级 14.78 ns 到 12 级 1.55 ns）、工作队列
    （深度 0 的 2.27 ns 到深度 8 的 3.14 ns）。抽成函数是因为可行性判断和
    代价估算都要用它，两边各算一遍迟早分叉。
    """
    return max(
        ARRAY_CRITICAL_PATH_NS,
        divider_critical_path_ns(point.divider_stages),
        queue_critical_path_ns(point.num_rows, point.pe_per_row, point.queue_depth),
    )


#: 哪个门里的模块对应时钟模型里的哪一段。
#:
#: **只有这三段在时钟模型里。** 别的模块（KeyFeeder、TopK、ExpUnit）也能被
#: 变异、门也会量出它们的关键路径，但那个数**替换不了任何一段**——报出来
#: 而不是悄悄忽略，否则会让人以为"量了就算进去了"。
_MODULE_COMPONENT = {
    "BlockSched": "queue",
    "Divider": "divider",
    "RePE": "array",
    "PrePE": "array",
}


def component_of_module(target: str) -> str | None:
    """一个被变异的模块属于时钟模型的哪一段；不在模型里就返回 None。"""
    for prefix, component in _MODULE_COMPONENT.items():
        if str(target or "").startswith(prefix):
            return component
    return None


def effective_clock_ns(
    *, num_rows: int, pe_per_row: int, queue_depth: int, divider_stages: int,
    measured: dict[str, float] | None = None,
) -> float:
    """系统时钟周期，**实测的那一段用实测值**。

    存在的理由：µArch 的变异改的是 RTL，而计划里的 `predicted_clock_ns` 是
    模型算的——RTL 变了模型不知道。实测撞到过：两次变异 `accepted=True`，
    而延迟/功耗/面积四轮完全没动，因为目标是从 `predicted_cycles x
    predicted_clock_ns` 算的，**变异对目标的影响在评估链上根本不可见**。

    时钟是三段的最大值，所以一段变快**不一定**让时钟变快：把队列从
    2.760 ns 缩到 2.2，时钟会停在阵列的 2.230，不是 2.2。这正是需要按段
    替换而不是整体覆盖的原因。
    """
    parts = {
        "array": ARRAY_CRITICAL_PATH_NS,
        "divider": divider_critical_path_ns(divider_stages),
        "queue": queue_critical_path_ns(num_rows, pe_per_row, queue_depth),
    }
    for component, value in (measured or {}).items():
        if component in parts and value:
            parts[component] = value
    return max(parts.values())


def area_units(point: CoDesignPoint, block_m: int, kept_per_block: int,
               *, head_dim: int) -> float:
    """一个协同设计点的总面积，um^2（Nangate45）。

    三项里两项经过 yosys 实测标定（TopK、RePEArray），SRAM 那项是估计——
    yosys 没有存储器宏编译器，实测值反映的是综合流程缺一环。详见
    `fast/agents/templates.py` 的面积模型一节。
    """
    # **每个 query 行一个 TopK、一个除法器。**
    #
    # `attention_tile.scala` 里是 `Seq.fill(tileQ)(Module(new TopK(...)))` 和
    # `Seq.fill(tileQ)(Module(new FixedPointDivPipelined(...)))`——模型此前各
    # 只算了一个，32 行的设计因此少算了 193k + 168k um^2。
    #
    # 这个缺陷是**整设计综合实测**发现的：模型预测 1,072,094 um^2，实测
    # 2,124,822（还缺一块），差 1.98 倍。逐模块综合看不出来——单个 TopK 的
    # 面积一直是对的，错的是数量。
    rows = point.num_rows
    return (
        array_area_units(point.num_rows, point.pe_per_row, point.data_width, point.reg_width)
        # 预测阵列此前完全不在模型里。它和执行阵列一样大甚至更大。
        # head_dim，不是 tile_d：预测阵列的宽度是**模型的 head 维度**，
        # 而 tile_d 是分块尺寸。两者默认都等于 64，所以这个混淆一直看着像对的。
        + predict_array_area_um2(point.num_rows, head_dim)
        + rows * topk_area_units(block_m, kept_per_block, point.data_width)
        + sram_area_units(point.sram_bytes)
        # 除法器在数据通路上，它的面积必须算进来——否则「多花面积换频率」
        # 这个取舍只有收益没有成本，优化器会无脑选最深的流水。
        + rows * divider_area_um2(point.divider_stages)
        # 工作队列同理，而且贵得多：DynaX-S 深度 16 的队列是 129k um^2，
        # 两个阵列合计才 740k——**17.4%**。此前这一项完全没收费，于是
        # queue_depth 变成一个只有收益的维度，优化器必然选最深的那个。
        + queue_area_um2(point.num_rows, point.pe_per_row, point.queue_depth)
        # 取数引擎的选择网络。相对 SRAM 宏（256 KB 是 105 万 um^2）它很小
        # ——整个 4->32 bank 区间才约 1 万——但收进来才能说「已经算过了」，
        # 而不是「大概可以忽略」。
        + bank_logic_area_um2(point.bank_count)
    )


def pe_utilisation(profile: KernelProfile | None, queue_depth: int,
                   num_rows: int = 32, pe_per_row: int = 4) -> float:
    """阵列里有多少 PE 在干活，给定这个内核的行长分布。

    动态稀疏下每个 query 行保留的列数不同。所有行共享同一个 K 列寄存器窗口，
    窗口推进到下一个 tile 之前，先算完的行只能空转。工作队列让先完成的行
    提前进入后面的 tile，把这个差异摊掉。

    ## 数据来源：实测优先，模型兜底

    有实测曲线就用实测（`templates.queue_utilisation`，Verilator 跑真实
    工作量，RTL 是 `block_scheduler.scala`）。没有才回退到一阶模型

        utilisation = 1 / (1 + (imbalance - 1) / (1 + queue))

    并且**必须知道两者的差别**：那个公式在深度增大时收敛到 1，而实测曲线
    在 1 以下就饱和了。xm 到深度 4 停在 0.867，公式在深度 16 承诺 0.976。
    差的那 13% 是 tile 内的结构性损失——一行的保留数不是 pe 的整数倍时，
    最后一趟有空槽，加多少队列都填不上。所以回退路径是**偏乐观**的。

    ## 吃进来的 imbalance 必须是 tile 内的那个

    `profile.tile_load_imbalance` 是共享同一个 tile 的那 numRows 行之间的
    差异；`profile.load_imbalance` 是整行、全序列、跨头拍平的全局极值，
    主要在反映因果斜坡。两者连排序都不一样（实测：全局量把完美均衡的 N:M
    排在 topk 之前，实际正好相反）。详见 `sparsity_stats.py` 里的注记。
    """
    if profile is None:
        return 0.75  # no profile: assume nothing about balance, and say so upstream
    imbalance = max(1.0, profile.tile_imbalance_for(num_rows))
    measured = queue_utilisation(imbalance, queue_depth, num_rows, pe_per_row)
    if measured is not None:
        return measured
    return 1.0 / (1.0 + (imbalance - 1.0) / (1.0 + queue_depth))


def estimate(
    point: CoDesignPoint,
    kernel: KernelResult,
    sequence_length: int,
    *,
    head_dim: int,
    block_m: int = 64,
    kept_per_block: int = 16,
) -> dict[str, float]:
    """一个协同设计点的一阶 cycles / traffic / area / EDP。

    ## 总工作量由**问题形状**决定，不由分块决定

    `head_dim` 是必填的关键字参数，因为这里曾经用 `point.tile_d` 冒充它：

        dense_macs = sequence_length * sequence_length * point.tile_d

    而 `tile_d` 是**可搜索的分块尺寸**。后果是把分块改小会被当成「活变少」
    并直接奖励——实测 tile_d 从 64 减到 32，cycles 减半、EDP 变四分之一，
    纯粹是模型假象。分块该影响的是重用、尾部损耗和驻留字节，**不是任务本身**。

    默认值也不能给：一个默认的 head_dim 会让这个洞在调用方忘记传时悄悄
    复活，而它上一次就是靠 `tile_d` 默认恰好等于 64 才一直看着像对的。

    ## 分阶段计，而不是一个 dense_macs

        prediction   seq^2 x head_dim，**稠密**——DynaX 的预测器给所有
                     (query, key) 对算近似分数，这是 O(N^2) 的开销，
                     不随稀疏度下降。把它漏掉会让稀疏收益被高估。
        QK^T         seq^2 x head_dim x retained
        AV           seq^2 x head_dim x retained

    **还没计入的**（说出来而不是假装不存在）：selection/TopK、softmax、
    索引与控制、片上片外搬运的分别成本。它们目前被并进 `memory_slowdown`
    这一个系数里。
    """
    retained = max(0.0, 1.0 - kernel.actual_sparsity)
    if head_dim <= 0:
        raise ValueError("head_dim must be positive")

    # 因果遮罩这里没扣：seq^2 是上界。两个方法比较时它是同一个常数因子，
    # 但**绝对值偏大约 2 倍**，报出去的时候要说清楚。
    pairs = sequence_length * sequence_length
    predict_macs = pairs * head_dim                 # 稠密，不随稀疏度降
    sparse_macs = 2.0 * pairs * head_dim * retained  # QK^T 和 AV 各一遍

    # 阵列尺寸要传下去：不均衡度和实测曲线都随行数变（xm 32 行 1.46、
    # 64 行 1.56），用默认值等于把 64x8 的点当成 32x4 来算。
    utilisation = pe_utilisation(
        kernel.profile, point.queue_depth, point.num_rows, point.pe_per_row
    )
    lanes = max(1, point.mac_lanes)
    compute_cycles = sparse_macs / (lanes * max(utilisation, 1e-3))

    # 预测阵列是另一块硬件（`attention_tile.scala` 同时例化两个），它按
    # `num_rows x head_dim` 个单元并行跑低精度近似分数。它和执行阵列在
    # DynaX 里是流水重叠的，所以取两者的最大值而不是相加——**这是一个
    # 建模假设**，真实重叠程度要靠集成 harness 测。
    predict_lanes = max(1, point.num_rows * head_dim)
    predict_cycles = predict_macs / predict_lanes
    compute_cycles = max(compute_cycles, predict_cycles)

    # 访存减速：阵列每拍要 regWidth 个新 K 标量，取数引擎在真实稀疏索引下
    # 供不上。实测 4 个 bank 时 xm 减速 3.05x，32 个 bank 降到 1.13x。
    #
    # **`double_buffer` 治不了这个。** 双缓冲藏的是延迟，不是带宽——取数
    # 引擎的吞吐比阵列的需求慢 N 倍时，再多的缓冲也补不上那 N 倍。所以这一项
    # 不看 double_buffer，而 double_buffer 只影响驻留字节数和面积。
    memory_slowdown, slowdown_source = gather_slowdown_provenance(
        point.bank_count, kernel.sparse_method)
    cycles = compute_cycles * memory_slowdown

    # Only occupied blocks are fetched; the rest are skipped whole.
    per_element = point.data_width // 8
    # K/V 都要搬，而且每个元素是 head_dim 维——原来这里漏了 head_dim，
    # 所以流量与 head 宽度无关，那不对。
    dram_bytes = kernel.block_occupancy * pairs * head_dim * per_element

    area = area_units(point, block_m, kept_per_block, head_dim=head_dim)

    # 时钟周期取数据通路上最慢的那一段。两段都是实测的：
    #
    #   执行阵列  2.23 ns（单个 PE 内部的路径，不随阵列规模变化）
    #   除法器    14.78 ns（0 级/上游）到 1.55 ns（12 级）
    #
    # 在有这个 max 之前，`edp = energy * cycles` 里 energy 又等于
    # `power * cycles`，所以 EDP 的单位是「周期² x 功率」——**时钟周期从来
    # 没进过公式**。后果是优化器完全看不见除法器：快的除法器不改变周期数，
    # 只改变每周期多长，而「每周期多长」在模型里不存在。
    #
    # 这也是为什么实测能改变搜索结果，而不只是让数字更准：它补上的是模型
    # 里缺失的一个物理量，不是一个系数。
    #
    # 工作队列也在这个 max 里，而且是实测发现的：它的关键路径随深度从
    # 2.27 ns 涨到 3.14 ns，深度 8 起就超过阵列的 2.23 ns，取代阵列决定
    # 系统频率。少了这一项，深度看起来是「只涨利用率」的；算上之后，
    # xm 上深度 8 的「利用率/周期」比完全没有队列还差（0.276 vs 0.311）。
    period_ns = clock_period_ns(point)
    seconds = cycles * period_ns * 1e-9

    # 功耗，mW。两项都换成了实测标定的量——此前逻辑项是任意单位
    # （32x4 算出 2.85，实测 398.655 mW），SRAM 项是 `sram_bytes * 1e-6`
    # （256 KB 只有 0.26 mW，实测宏拼装漏电是 51 mW，差 200 倍）。
    #
    # 动态读功耗还没进来：它要乘以访存次数，而访存次数正是周期模型里
    # 缺的那一块（见下面 dram_bytes 处的注记）。只放漏电而不放动态，
    # 是**偏低**的估计，但比放一个编出来的系数强。
    power = (
        array_power_mw(lanes, utilisation, point.data_width)
        + sram_leakage_mw(point.sram_bytes)
    )
    energy = power * 1e-3 * seconds  # mW -> W; energy is joules/task
    return {
        "cycles": cycles,
        "compute_cycles": compute_cycles,
        "memory_slowdown": memory_slowdown,
        # 这个系数是**测出来的还是借来的**。没标定过的算法会静默继承 xm 的
        # 值，而「框架能适配新算法」这个结论不能建立在一个借来的常数上。
        "memory_slowdown_source": slowdown_source,
        "clock_period_ns": period_ns,
        "max_frequency_mhz": 1000.0 / period_ns,
        "seconds": seconds,
        "pe_utilization": utilisation,
        "throughput": sequence_length / seconds if seconds else 0.0,
        "dram_bytes": dram_bytes,
        "area": area,
        "power": power,
        "energy_j": energy,
        "energy_efficiency_tasks_per_j": 1.0 / energy if energy > 0 else None,
        "energy_scope": "partial-model:execute-array-dynamic+sram-leakage",
        # 真正的 energy-delay product：焦耳 x 秒。
        "edp": energy * seconds,
    }


def data_layout_for(point: CoDesignPoint, profile) -> str:
    """数据布局：双缓冲与列广播是**两个正交的决定**。

    * `double_buffer` 是硬件决定的（多一份驻留缓冲）
    * 广播是 **profile 决定的**：列质量集中时，那几列会被 tile 里每一行
      重复读，值得只搬一次而不是每行都流一遍

    合并 planner 之前这两条分别活在 CoOptimizer 和 CompilerAgent 里，
    合并时广播那条一度被丢掉——它是唯一一条真正由 profile 驱动的布局决策，
    丢了就等于 `column_top5_mass` 这个测量没有任何用处。
    """
    parts = ["blocked-qkd"]
    if point.double_buffer:
        parts.append("double")
    if profile is not None and profile.column_top5_mass >= 0.5:
        parts.append("broadcast")
    return "-".join(parts)


def to_schedule(point: CoDesignPoint, rationale: tuple[str, ...], utilisation: float,
                profile=None, *, block_m: int = 64,
                kept_per_block: int = 16) -> CompilerSchedule:
    return CompilerSchedule(
        status=Status.PASSED,
        tile_q=point.tile_q,
        tile_k=point.tile_k,
        tile_d=point.tile_d,
        loop_order=("q", "k", "d"),
        data_layout=data_layout_for(point, profile),
        parallelism=point.parallelism,
        predicted_utilization=utilisation,
        predicted_bytes=working_set_bytes(point),
        num_rows=point.num_rows,
        pe_per_row=point.pe_per_row,
        reg_width=point.reg_width,
        data_width=point.data_width,
        sram_bytes=point.sram_bytes,
        queue_depth=point.queue_depth,
        divider_stages=point.divider_stages,
        bank_count=point.bank_count,
        block_m=block_m,
        kept_per_block=kept_per_block,
        rationale=rationale,
    )


def to_hardware(
    point: CoDesignPoint,
    template,
    *,
    head_dim: int,
    block_m: int,
    kept_per_block: int,
    binary_point: int = 8,
) -> HardwareCandidate:
    """Instantiate the composed candidate, carrying the real module parameters."""
    return HardwareCandidate(
        status=Status.PASSED if template.verified else Status.FAILED,
        template_id=template.template_id,
        template_digest=template.digest,
        verified_template=template.verified,
        pe_rows=point.num_rows,
        pe_cols=point.pe_per_row,
        queue_depth=point.queue_depth,
        sram_bytes=point.sram_bytes,
        data_width=point.data_width,
        manifest_uri=template.manifest_uri,
        topk_m=block_m,
        topk_n=kept_per_block,
        binary_point=binary_point,
        reg_width=point.reg_width,
        col_select_bits=required_col_select_bits(block_m),
        area_units=area_units(point, block_m, kept_per_block, head_dim=head_dim),
        error=None if template.verified else (
            f"{template.template_id} has not passed the verification gate: {template.blocking_issue}"
        ),
    )
