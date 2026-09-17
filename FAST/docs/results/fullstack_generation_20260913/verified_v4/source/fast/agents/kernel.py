"""The Kernel Agent: spend a measurement budget, not just take one measurement.

The agent owns three things a proposer must not touch: what gets measured (the
adapter), whether a result clears the accuracy budget (the epsilon gate), and
what counts as a frontier. A proposer only says which configurations to try
next, so a rule and an LLM can be swapped and compared under identical
conditions.
"""

from __future__ import annotations

import time

from fast.adapters.base import KernelAdapter
from fast.agents.proposers import KernelProposer, SweepProposer
from fast.schemas.models import (
    ExperimentSpec,
    KernelMeasurement,
    KernelResult,
    KernelSearchReport,
    KernelSearchSpace,
    Status,
)


class KernelAgent:
    """Runs DynaX-backed measurements and enforces the quality gate."""

    def __init__(self, adapter: KernelAdapter):
        self.adapter = adapter

    def run(self, spec: ExperimentSpec) -> KernelResult:
        """Measure the single candidate named by the spec."""
        
        # 调用适配器评估该实验规范
        result = self.adapter.evaluate(spec)
        if result.quality_loss < 0 or not 0 <= result.actual_sparsity <= 1:
            raise ValueError("kernel adapter returned invalid metrics")
        return result

    def search(
        self,
        spec: ExperimentSpec,
        *,
        proposer: KernelProposer | None = None,
        space: KernelSearchSpace | None = None,
        batch: int = 4,
        # 不叫 `candidates`：循环里的局部变量 `candidates` 是 proposer 提出的
        # 那一批，两者会遮蔽。名字撞了之后这里拿到的是一个元组而不是个数，
        # 而且直到运行时才炸。
        candidate_count: int = 1,
        db=None,
    ) -> KernelSearchReport:
        """Spend ``spec.budget.max_evaluations`` measurements on the space.

        Rounds are batched because the expensive part is loading the model, not
        measuring one more configuration: the adapter evaluates a whole round in
        a single process.

        ``db`` is an optional :class:`~fast.storage.ExperimentDB`. It is injected
        rather than owned so the agent stays a pure function of its inputs in
        tests, and so recording a search never changes what the search does.
        """
        proposer = proposer or SweepProposer()
        space = space or KernelSearchSpace(max_sequence_length=spec.sequence_length)
        # Budget already refuses a non-positive max_evaluations, so there is no
        # second guard here: one owner per invariant.
        budget = spec.budget.max_evaluations

        started = time.time()
        # 初始化历史记录元组
        history: tuple[KernelMeasurement, ...] = ()
        baseline: float | None = None
        rounds = 0
        
        # 如果提供了数据库，则启动一个运行记录（run），获取 run_id
        run_id = db.start_run(spec, proposer=proposer.name) if db is not None else None
        seen_rejections = 0

        while len(history) < budget:
            want = min(batch, budget - len(history))
            
            # 让提议者根据当前规范、空间和历史记录，提出 want 个候选配置
            candidates = proposer.propose(spec, space, history, want)
            if not candidates:
                break
            rounds += 1
            measured, round_baseline = self.adapter.measure(spec, candidates)
            if baseline is None:
                baseline = round_baseline
            history += tuple(measured)
            if db is not None:
                db.record_proposals(run_id, rounds, "kernel", candidates)
                db.record_measurements(run_id, measured)
                notes = list(getattr(proposer, "rejected", ()) or ())
                db.record_rejections(run_id, rounds, "kernel", notes[seen_rejections:])
                seen_rejections = len(notes)

        if db is not None:
            db.finish_run(run_id)
        rejected = tuple(getattr(proposer, "rejected", ()) or ())
        # `proposer` 报的是**实际产出**，不是配置的那个。
        #
        # `LLMProposer` 在调用失败/回复不可用时会静默回退到 `SweepProposer`，
        # 而报告的这个字段原来写的是配置值——于是一次全靠 sweep 兜底的运行
        # 会顶着 `llm:gemini-2.5-pro` 的名字出现在下游。逐候选的 `proposed_by`
        # 一直是诚实的（回退产出的写 `sweep`），所以这里直接从它汇总。
        actual = _proposer_provenance(history, proposer.name)
        accepted = [item for item in history if item.within and item.quality_loss <= spec.epsilon]
        best = max(accepted, key=lambda item: item.actual_sparsity) if accepted else None
        picked, shortfall = select_candidates(tuple(accepted), candidate_count)
        return KernelSearchReport(
            spec=spec,
            proposer=actual,
            baseline_metric=baseline,
            measurements=history,
            pareto=pareto_front(history),
            best=best,
            rounds=rounds,
            rejected=rejected,
            wall_seconds=round(time.time() - started, 3),
            candidates=picked,
            candidate_shortfall=shortfall,
        )




def _proposer_provenance(history, configured: str) -> str:
    """从逐候选的 `proposed_by` 汇总出这次搜索**实际**由谁提议。

    配置了 LLM 却全程回退到 sweep，是一个下游必须看得见的事实：报告会一路
    交给 Compiler/Critic，而「这些候选是模型推理出来的」和「这些候选是等距
    采样出来的」对归因的含义完全不同。
    """
    from collections import Counter

    counts = Counter(item.proposed_by for item in history if getattr(item, "proposed_by", None))
    if not counts:
        return configured
    if len(counts) == 1:
        return next(iter(counts))
    total = sum(counts.values())
    parts = [f"{name} {n}/{total}" for name, n in counts.most_common()]
    return " + ".join(parts)


def select_candidates(
    accepted: tuple[KernelMeasurement, ...], count: int
) -> tuple[tuple[KernelMeasurement, ...], str | None]:
    """从**同一个算法**的配置里挑 `count` 个交给下游。

    ## 候选是同一个算法的不同配置

    算法由使用者给定，不是搜出来的（见 `KernelSearchSpace`）。所以这里挑的是
    比如 `xm:32:8:64` 和 `xm:16:8:64`，不是「xm 还是 sanger」。

    这一点曾经搞反过：原来第一阶段叫「先保方法族覆盖」，按标签前缀分组、每族
    先进一个，理由是「实测方法族是硬件代价最强的预测因子（8 bank 下 nm 1.19x
    到 xm 2.14x，跨度 2.17x）」。那个测量本身没错，但它回答的是「该选哪个
    算法」——而算法不归这里选。族固定之后，那条规则要么没事可做（只有一个族），
    要么在做错事。

    ## 为什么不从 (稀疏度, 精度损失) 的 Pareto front 里挑

    **那个 front 可能把真正的赢家排除掉。** 用实测的硬件代价举例：

        xm:32:16:64  稀疏度 0.86  损失 0.018  硬件代价 2.58  ->  预测加速比 2.77
        nm:16:64     稀疏度 0.75  损失 0.020  硬件代价 1.19  ->  预测加速比 3.37

    后者在**两个轴上都被支配**，所以不在 front 上——但它快 22%。所以从全部
    通过 epsilon 门的点里挑，不限于 front。

    ## 散布在 (稀疏度, tile 不均衡度) 上

    这两个是**下游真正感受到的**量：稀疏度决定 cycles，tile 内不均衡度决定
    PE 利用率（实测在 `block_scheduler.scala` 上）。精度损失不作为散布轴——
    进到这里的点已经全部通过 epsilon 门了，它在这一步不再区分优劣。

    同一个算法内部这两个量的跨度是真实的：作业 17248126 实测的 tile(32)
    不均衡度，`xm:32:32:64` 1.336、`xm:32:16:64` 1.425、`xm:32:4:64` 1.576、
    `xm:64:4:64` 1.632——22% 的跨度，而且它和稀疏度不同向（`xm:32:32:64`
    最均衡但最不稀疏）。族内并不是「给 3 个和给 1 个没区别」。

    ## 不足额时说明原因，不凑数

    凑进来的点会被下游当成「Kernel 认为值得一试」的东西。
    """
    if count <= 0:
        return (), "candidate count must be positive"
    if not accepted:
        return (), "no measurement stayed inside the accuracy budget"

    # 最稀疏的那个先进来：它是「最想要的那个点」，其余名额用来覆盖取舍曲线。
    picked: list[KernelMeasurement] = [max(accepted, key=lambda i: i.actual_sparsity)]
    if len(picked) < count:
        picked.extend(_spread_fill(accepted, picked, count - len(picked)))

    shortfall = None
    if len(picked) < count:
        families = {item.label.split(":")[0] for item in accepted}
        note = "" if len(families) <= 1 else f"（注意：混了 {len(families)} 个算法 {sorted(families)}）"
        shortfall = (
            f"only {len(picked)} of {count} candidates: {len(accepted)} configurations "
            f"cleared epsilon{note}"
        )
    return tuple(picked), shortfall



def _imbalance_of(item: KernelMeasurement, num_rows: int = 32) -> float:
    """实测的 tile 内不均衡度；没测到就 0.0（见 `_spread_fill` 的说明）。

    **不接受全局 `load_imbalance` 的回退。** 一部分候选用实测、一部分用回退，
    等于把两个不同的量放在同一根轴上：全局值放大约 1.9-2.5 倍，排序也不同，
    散布结果因此由「谁有 profile」而不是「谁更不均衡」决定。
    """
    profile = getattr(item, "profile", None)
    if profile is None:
        return 0.0
    try:
        measured = profile.tile_imbalance_measured(num_rows)
    except Exception:  # noqa: BLE001
        return 0.0
    return 0.0 if measured is None else float(measured)

def _spread_fill(
    accepted: tuple[KernelMeasurement, ...],
    picked: list[KernelMeasurement],
    want: int,
) -> list[KernelMeasurement]:
    """在 (稀疏度, tile 不均衡度) 上按最大最小距离补齐名额。

    这两个轴是**下游真正感受到的**：稀疏度决定 cycles，不均衡度决定利用率。
    精度损失不作为轴——进到这里的点已经全部通过 epsilon 门。

    两个轴都归一化到 [0, 1] 再算距离——稀疏度在 0-1 而不均衡度实测能到 3 以上，
    不归一化的话距离几乎只由不均衡度决定，散布会退化成一维。

    没测到不均衡度的点该轴记 0，**不猜一个中性值**：一个看起来像测量的占位数
    会让它在散布里占据一个它没有的位置。
    """
    chosen_labels = {item.label for item in picked}
    remaining = [item for item in accepted if item.label not in chosen_labels]
    if not remaining:
        return []

    sparsity = [item.actual_sparsity for item in accepted]
    imbalance = [_imbalance_of(item) for item in accepted]
    s_lo, s_hi = min(sparsity), max(sparsity)
    i_lo, i_hi = min(imbalance), max(imbalance)

    def coords(item: KernelMeasurement) -> tuple[float, float]:
        s = (item.actual_sparsity - s_lo) / (s_hi - s_lo) if s_hi > s_lo else 0.0
        b = (_imbalance_of(item) - i_lo) / (i_hi - i_lo) if i_hi > i_lo else 0.0
        return s, b

    chosen: list[KernelMeasurement] = []
    reference = list(picked)
    for _ in range(min(want, len(remaining))):
        def min_distance(item: KernelMeasurement) -> float:
            if not reference:
                return float("inf")
            sx, lx = coords(item)
            return min(
                ((sx - sy) ** 2 + (lx - ly) ** 2) ** 0.5
                for sy, ly in (coords(other) for other in reference)
            )

        far = max(remaining, key=min_distance)
        chosen.append(far)
        reference.append(far)
        remaining.remove(far)
    return chosen


def pareto_front(history: tuple[KernelMeasurement, ...]) -> tuple[str, ...]:
    """Configurations nothing else beats on both sparsity and quality loss.

    Block occupancy is reported but deliberately not part of the frontier: it is
    the compiler and micro-architecture layers that turn low occupancy into
    speed, so the kernel layer must not pre-judge it.
    """
    scored = [item for item in history if item.within]
    front = []
    for item in scored:
        dominated = any(
            other.actual_sparsity >= item.actual_sparsity
            and other.quality_loss <= item.quality_loss
            and (
                other.actual_sparsity > item.actual_sparsity
                or other.quality_loss < item.quality_loss
            )
            for other in scored
        )
        if not dominated:
            front.append(item.label)
    return tuple(front)
