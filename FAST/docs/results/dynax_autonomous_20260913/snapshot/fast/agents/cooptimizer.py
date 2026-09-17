"""Joint Compiler/µArch exploration.

Table II keeps the two agents separate - different inputs, outputs and stopping
criteria - but §II.A has them "jointly explore the coupled software-hardware
space". Both are true, and this is how: each agent still owns its own decision
and its own contract, while the pair is proposed, constrained and scored
together, because a schedule and an array are only meaningful against each other.

Ownership, mirroring the Kernel Agent:
- the proposer suggests co-design points;
- the CoOptimizer owns feasibility, scoring and the frontier;
- neither may bypass the verified-template gate.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import random
import time
from typing import Protocol

from fast.agents.codesign import (
    DEFAULT_OBJECTIVE,
    ObjectiveSpec,
    CoDesignPoint,
    CoDesignSpace,
    estimate,
    pe_utilisation,
    to_hardware,
    to_schedule,
    violations,
    working_set_bytes,
)
from fast.agents.templates import (
    ARRAY_CRITICAL_PATH_NS,
    TemplateRegistry,
    divider_critical_path_ns,
    gather_slowdown,
    queue_critical_path_ns,
)
from fast.schemas.models import (
    ArchSpecs,
    CompilerSchedule,
    HardwareCandidate,
    KernelResult,
    Status,
)


@dataclass(frozen=True)
class CoDesignResult:
    """One evaluated pair: the schedule, the hardware, and what it would cost."""

    point: CoDesignPoint
    schedule: CompilerSchedule
    hardware: HardwareCandidate
    metrics: dict[str, float]
    feasible: bool
    violations: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoDesignReport:
    spec_sequence_length: int
    fidelity: str
    evaluated: int
    feasible: int
    best: CoDesignResult | None
    frontier: tuple[CoDesignResult, ...]
    rejected_examples: tuple[str, ...]
    wall_seconds: float
    rounds: int = 0
    stopped_because: str = ""
    history: tuple[CoDesignResult, ...] = ()


class CoDesignProposer(Protocol):
    name: str

    def propose(
        self,
        kernel: KernelResult,
        specs: ArchSpecs,
        space: CoDesignSpace,
        history: tuple[CoDesignResult, ...],
        count: int,
    ) -> tuple[CoDesignPoint, ...]: ...


class RandomProposer:
    """Seeded black-box control with the same legal parameter domains."""

    name = "random"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def propose(self, kernel, specs, space, history, count):
        seen = {_key(item.point) for item in history}
        picked = []
        from fast.agents.codesign import CoDesignPoint
        domains = {name: getattr(space, name) for name in space.__dataclass_fields__}
        domains.update(data_width=specs.data_widths)
        for _ in range(max(100, count * 100)):
            point = CoDesignPoint(**{name: self.rng.choice(values)
                                     for name, values in domains.items()})
            if _key(point) not in seen:
                seen.add(_key(point))
                picked.append(point)
                if len(picked) == count:
                    break
        return tuple(picked)


class ParetoFeedbackProposer:
    """Rule control: explore neighbours of alternating Pareto extremes.

    This is explicitly a non-LLM baseline. It tests whether local feedback alone
    accounts for an apparent agent advantage. Random exploration avoids trapping
    the search on a single latency optimum.
    """

    name = "pareto-feedback-rules"

    def __init__(self, seed=0):
        self.random = RandomProposer(seed)
        self.rng = random.Random(seed)

    def propose(self, kernel, specs, space, history, count):
        if not history:
            return GuidedProposer().propose(kernel, specs, space, history, count)
        front = _frontier(list(history))
        if not front:
            return self.random.propose(kernel, specs, space, history, count)
        seen = {_key(item.point) for item in history}
        candidates = []
        domains = {name: getattr(space, name) for name in space.__dataclass_fields__}
        domains.update(data_width=specs.data_widths)
        neighbours = []
        for parent in front:
            for field, values in domains.items():
                for value in values:
                    child = replace(parent.point, **{field: value})
                    if _key(child) not in seen:
                        seen.add(_key(child))
                        neighbours.append(child)
        self.rng.shuffle(neighbours)
        candidates.extend(neighbours[:max(1, count // 2)])
        shadow = history + tuple(CoDesignResult(p, None, None, {}, False) for p in candidates)
        candidates.extend(self.random.propose(kernel, specs, space, shadow, count-len(candidates))
                          if len(candidates) < count else ())
        return tuple(candidates[:count])


class GuidedProposer:
    """Deterministic control, guided by the kernel profile rather than by a grid.

    The full product space is far larger than any measurement budget, so the
    opening batch is derived from what the kernel measured: the row imbalance
    sets the queue depth worth trying, and the retained fraction sets how many
    lanes can be kept fed.
    """

    name = "guided"

    def propose(self, kernel, specs, space, history, count):
        seen = {_key(item.point) for item in history}
        picked: list[CoDesignPoint] = []

        imbalance = (max(1.0, kernel.profile.tile_imbalance_for(32))
                     if kernel.profile else 1.0)
        # 队列深度：**取拿到大部分收益的最浅那个**，不是去够一个固定目标。
        #
        # 原来的写法是 `min(depths, key=|utilisation(d) - 0.9|)`。实测曲线
        # 在 1 以下饱和（xm 停在 0.867），0.9 根本够不到，于是那个写法永远
        # 选最深的一档——花 129k um^2（DynaX-S 芯片面积的 16%）去追一个
        # 硬件到不了的目标。而 xm 从深度 4 到 16 的收益是 0.0025。
        #
        # 收益递减很陡：xm 深度 2 就拿到 78% 的可得收益，深度 4 拿到 98%。
        # 所以判据改成「达到可得上限的 95%」，再深就不值那个面积。
        wanted_queue = _shallowest_effective_queue(
            kernel.profile, space.queue_depth, target_mhz=specs.target_mhz
        )
        wanted_divider = _shallowest_divider(
            space, queue_critical_path_ns(32, 4, wanted_queue)
        )
        wanted_banks = _smallest_effective_banks(space, kernel.sparse_method)

        for point in _ordered_candidates(kernel, specs, space, wanted_queue, imbalance,
                                         wanted_divider, wanted_banks):
            key = _key(point)
            if key in seen:
                continue
            seen.add(key)
            picked.append(point)
            if len(picked) == count:
                break
        return tuple(picked)



def _shallowest_effective_queue(profile, depths: tuple[int, ...],
                                num_rows: int = 32, pe_per_row: int = 4,
                                target_mhz: float | None = None) -> int:
    """吞吐最高的那个深度；并列时取最浅的。

    判据是**利用率 / 时钟周期**，不是利用率。只看利用率会漏掉队列自己的
    关键路径：实测它从 2.27 ns（深度 0）涨到 3.14 ns（深度 8），而执行阵列
    是 2.23 ns——深度 8 起调度器取代阵列决定系统频率。xm 上的实际曲线：

        深度 0  0.7079 / 2.273 = 0.311
        深度 2  0.8323 / 2.528 = 0.329   <- 最优
        深度 4  0.8644 / 2.760 = 0.313
        深度 8  0.8669 / 3.140 = 0.276   <- 比完全没有队列还差

    只看利用率会选深度 8 甚至 16，多花 12 万 um^2（DynaX-S 芯片面积的
    16%）买一个比不装队列还慢的系统。

    并列取最浅：面积在这里不参与判据，所以「一样快」时选便宜的那个。
    """
    if not depths:
        return 0
    ordered = sorted(depths)

    # 只在**可行**的深度里挑。频率约束把深队列直接杀掉（深度 8 = 318 MHz），
    # 不先过滤就会把整个预算花在会被拒的点上——提议一个必然不可行的点，
    # 等于没提议。
    if target_mhz is not None:
        period_cap = 1000.0 / target_mhz
        allowed = [d for d in ordered
                   if queue_critical_path_ns(num_rows, pe_per_row, d) <= period_cap]
        # 一个都不满足时保留最浅的：让 `violations()` 去报那个具体原因，
        # 而不是在这里返回一个空结果让上层不知道发生了什么。
        ordered = allowed or ordered[:1]

    def throughput(depth: int) -> float:
        period = max(
            ARRAY_CRITICAL_PATH_NS,
            queue_critical_path_ns(num_rows, pe_per_row, depth),
        )
        return pe_utilisation(profile, depth, num_rows, pe_per_row) / period

    best = max(throughput(d) for d in ordered)
    # 1% 之内算并列：实测值本身没有那么高的分辨率。
    for depth in ordered:
        if throughput(depth) >= best * 0.99:
            return depth
    return ordered[0]


SRAM_CHOICES = (65536, 131072, 262144)



def _shallowest_divider(space, queue_ns: float) -> int:
    """让除法器不再是瓶颈的最浅级数。

    上游的组合除法（0 级）是 14.78 ns / 68 MHz，而阵列能跑 448 MHz——
    除法器在数据通路上，它慢整条流水线跟着慢。但**深过瓶颈就只剩成本**：
    关键路径已经由阵列或队列决定之后，再加级数只增面积不增频率。

    所以判据是「降到不再是最慢那一段」，不是「越深越好」。
    """
    floor_ns = max(ARRAY_CRITICAL_PATH_NS, queue_ns)
    for stages in sorted(space.divider_stages):
        if divider_critical_path_ns(stages) <= floor_ns:
            return stages
    return max(space.divider_stages)


def _smallest_effective_banks(space, sparse_method: str, fraction: float = 0.99) -> int:
    """拿到大部分访存收益的最小 bank 数。

    bank 冲突的收益递减很陡（xm：4 个 bank 减速 3.05x，8 个 2.14x，
    32 个 1.13x），而 bank 数在逻辑上几乎免费——真实代价在 SRAM 宏的
    长宽比上，由 `plan_sram()` 承担。所以这里取「够用的最小」而不是最大。
    """
    counts = sorted(space.bank_count)
    if not counts:
        return 8
    best = max(1.0 / gather_slowdown(b, sparse_method) for b in counts)
    for banks in counts:
        if 1.0 / gather_slowdown(banks, sparse_method) >= best * fraction:
            return banks
    return counts[-1]


def _ordered_candidates(kernel, specs, space, wanted_queue, imbalance,
                        wanted_divider, wanted_banks):
    """Candidates in the order worth spending a budget on.

    Widest arrays first, because the retained work is what has to be covered;
    for each shape the smallest SRAM that actually holds the tile, because
    over-provisioning memory costs area without buying cycles.

    **`divider_stages` 和 `bank_count` 以前根本没被提议过**——它们在
    `CoDesignSpace` 里是搜索维度，但生成器一直在用 `CoDesignPoint` 的默认值
    （除法器 0 级 = 68 MHz）。频率约束一旦生效，整个预算就全花在不可行点上。
    两个维度各自有一个由实测决定的「够用值」，所以和 `wanted_queue` 一样
    先算一次、再传进来，不进这已经六层的循环。
    """
    for rows in sorted(space.num_rows, reverse=True):
        for cols in sorted(space.pe_per_row, reverse=True):
            if rows * cols > specs.max_pe:
                continue
            for tile_k in space.tile_k:
                for reg_width in space.reg_width:
                    if tile_k % reg_width:
                        continue
                    for width in specs.data_widths:
                        for double in (True, False):
                            base = CoDesignPoint(
                                tile_q=64, tile_k=tile_k, tile_d=64,
                                parallelism=min(rows, max(space.parallelism)),
                                double_buffer=double,
                                num_rows=rows, pe_per_row=cols, reg_width=reg_width,
                                data_width=width, sram_bytes=space.sram_bytes[0],
                                queue_depth=wanted_queue,
                                divider_stages=wanted_divider,
                                bank_count=wanted_banks,
                            )
                            fitted = _smallest_sram_that_fits(base, space.sram_bytes)
                            if fitted is not None:
                                yield fitted


def _smallest_sram_that_fits(point: CoDesignPoint, choices=SRAM_CHOICES) -> CoDesignPoint | None:
    for sram in sorted(choices):
        candidate = replace(point, sram_bytes=sram)
        if working_set_bytes(candidate) <= sram:
            return candidate
    return None


def _key(point: CoDesignPoint) -> tuple:
    return tuple(sorted(point.__dict__.items()))


class CoOptimizer:
    """Explores schedule/hardware pairs against one kernel result."""

    FIDELITY = "L1-analytical"

    def __init__(
        self,
        registry: TemplateRegistry | None = None,
        *,
        template_id: str = "repe_array",
        allow_unverified: bool = False,
        # 目标由外面给：提议/排序/收敛/报告必须是同一个定义。
        objective: ObjectiveSpec | None = None,
    ):
        self.registry = registry or TemplateRegistry()
        self.template_id = template_id
        # Composing an unverified template is the one thing the µArch Agent may
        # never do silently; exploring the cost space with one is legitimate but
        # must be asked for, and the candidate still reports FAILED.
        self.allow_unverified = allow_unverified
        self.objective = objective or DEFAULT_OBJECTIVE

    def run(
        self,
        kernel: KernelResult,
        *,
        sequence_length: int,
        # 模型的**真实 head 维度**，和分块尺寸 `tile_d` 是两回事。
        # 必填：给默认值会让"用 tile_d 冒充 head_dim"那个洞在调用方忘记传时
        # 悄悄复活，而它上一次就是靠两者默认都等于 64 才一直看着像对的。
        head_dim: int,
        specs: ArchSpecs | None = None,
        space: CoDesignSpace | None = None,
        proposer: CoDesignProposer | None = None,
        budget: int = 24,
        batch: int = 8,
        block_m: int = 64,
        kept_per_block: int = 16,
        patience: int | None = 2,
        min_improvement: float = 0.02,
        timeout_seconds: float | None = None,
    ) -> CoDesignReport:
        if budget <= 0 or batch <= 0 or (patience is not None and patience <= 0):
            raise ValueError("budget, batch and patience must be positive")
        if kernel.status is not Status.PASSED:
            return CoDesignReport(sequence_length, self.FIDELITY, 0, 0, None, (), (
                "kernel quality gate failed; nothing to co-optimise",
            ), 0.0, 0, "kernel gate")

        specs = specs or ArchSpecs()
        space = space or CoDesignSpace()
        proposer = proposer or GuidedProposer()
        template = self.registry.by_id(self.template_id)
        if template is None:
            return CoDesignReport(sequence_length, self.FIDELITY, 0, 0, None, (), (
                f"template {self.template_id!r} is not in the registry",
            ), 0.0, 0, "unknown template")
        if not template.verified and not self.allow_unverified:
            return CoDesignReport(sequence_length, self.FIDELITY, 0, 0, None, (), (
                f"{template.template_id} is unverified: {template.blocking_issue}",
            ), 0.0, 0, "verified-template gate")

        started = time.time()
        history: tuple[CoDesignResult, ...] = ()
        rejected: list[str] = []
        # Table II gives the Compiler Agent "Reduction or timeout" as its stopping
        # criterion, so the loop runs while rounds keep reducing EDP and stops
        # when they stop paying for themselves.
        # **和外层同一个目标。** 这里曾经按 `edp` 挑最优，而外层收敛用的是
        # 另一个量、报告用的是第三个——「变好」有三个定义，内层选出来的点
        # 未必是外层想要的点。
        objective = self.objective
        from fast.agents.pareto import extends_frontier, frontier_vectors, valid_vector
        progress_front = ()
        stalled = 0
        rounds = 0
        stopped = "budget exhausted"

        while len(history) < budget:
            if timeout_seconds is not None and time.time() - started >= timeout_seconds:
                stopped = "timeout"
                break
            want = min(batch, budget - len(history))
            points = proposer.propose(kernel, specs, space, history, want)
            if not points:
                stopped = "proposer exhausted the space"
                break
            rounds += 1
            previous_size = len(history)
            seen = {_key(item.point) for item in history}
            for point in points[:want]:
                if _key(point) in seen:
                    continue
                seen.add(_key(point))
                problems = violations(
                    point, kernel, specs, self.registry, head_dim=head_dim,
                    block_m=block_m, kept_per_block=kept_per_block,
                )
                metrics = estimate(
                    point, kernel, sequence_length, head_dim=head_dim,
                    block_m=block_m, kept_per_block=kept_per_block,
                )
                rationale = _rationale(kernel, point, metrics)
                history += (CoDesignResult(
                    point=point,
                    schedule=to_schedule(point, rationale, metrics["pe_utilization"], kernel.profile,
                                         block_m=block_m, kept_per_block=kept_per_block),
                    hardware=to_hardware(
                        point, template, head_dim=head_dim,
                        block_m=block_m, kept_per_block=kept_per_block
                    ),
                    metrics=metrics,
                    feasible=not problems,
                    violations=problems,
                    rationale=rationale,
                ),)
                if problems:
                    rejected.extend(problems[:1])

            if len(history) == previous_size:
                stopped = "proposer repeated evaluated points"
                break
            new_vectors = [objective.vector(item.metrics) for item in history[previous_size:]
                           if item.feasible and valid_vector(objective.vector(item.metrics))]
            improved = any(extends_frontier(progress_front, v, min_improvement)
                           for v in new_vectors)
            if improved:
                progress_front = frontier_vectors((*progress_front, *new_vectors))
                stalled = 0
            else:
                stalled += 1
                if patience is not None and stalled >= patience:
                    stopped = f"no Pareto improvement for {patience} rounds"
                    break

        feasible = [item for item in history if item.feasible]
        best = (min(feasible, key=lambda item: objective.score(item.metrics))
                if feasible else None)
        return CoDesignReport(
            spec_sequence_length=sequence_length,
            fidelity=self.FIDELITY,
            evaluated=len(history),
            feasible=len(feasible),
            best=best,
            frontier=_frontier(feasible, objective),
            rejected_examples=tuple(dict.fromkeys(rejected))[:8],
            wall_seconds=round(time.time() - started, 3),
            rounds=rounds,
            stopped_because=stopped,
            history=history,
        )


def _rationale(kernel, point: CoDesignPoint, metrics: dict[str, float]) -> tuple[str, ...]:
    lines = [
        f"kernel_sparsity={kernel.actual_sparsity:.4f}",
        f"block_occupancy={kernel.block_occupancy:.4f}",
        f"lanes={point.mac_lanes} queue_depth={point.queue_depth}",
        f"predicted_pe_utilization={metrics['pe_utilization']:.4f}",
    ]
    if kernel.profile is not None:
        # 报 tile 内的不均衡度，不是全局那个。规划是按 tile 内的量做的
        # （`pe_utilisation` 吃的就是它），rationale 里报另一个数会让审阅
        # 的人拿一个没参与决策的量去解释决策。两者连排序都不一样。
        lines.insert(1, f"tile_load_imbalance={kernel.profile.tile_imbalance_for(point.num_rows):.4f}")
        lines.insert(2, f"global_load_imbalance={kernel.profile.load_imbalance:.4f}")
    lines.append(f"memory_slowdown={metrics['memory_slowdown']:.4f} at {point.bank_count} banks")
    lines.append(f"clock={metrics['max_frequency_mhz']:.0f}MHz area={metrics['area']:,.0f}um2 "
                 f"power={metrics['power']:.0f}mW")
    return tuple(lines)


def _frontier(results: list[CoDesignResult], objective=None) -> tuple[CoDesignResult, ...]:
    """Exact feasible front in the declared axes; no cycles/area surrogate."""
    from fast.agents.pareto import valid_vector
    objective = objective or DEFAULT_OBJECTIVE
    results = [r for r in results if r.feasible and valid_vector(objective.vector(r.metrics))]
    front = []
    seen = set()
    for item in results:
        vector = objective.vector(item.metrics)
        dominated = any(objective.dominates(other.metrics, item.metrics) for other in results)
        if not dominated and vector not in seen:
            front.append(item)
            seen.add(vector)
    return tuple(sorted(front, key=lambda r: objective.vector(r.metrics)))
