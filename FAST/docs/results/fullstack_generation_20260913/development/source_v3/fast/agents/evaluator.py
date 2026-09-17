"""Evaluator Agent：把某一档保真度的后端归一化成统一的评估契约。

在流水线里的位置：Kernel → Compiler → µArch → **Evaluator** → Critic。

这个 Agent 自己不测量任何东西，它只保证**无论后端是哪一档，出来的
`EvaluationResult` 形状一致、并且诚实标注自己是哪一档**：

    L0-deterministic            合成数据，只验证控制流    functional_passed 恒 False
    L1-analytical-shared-model  一阶代价模型              functional_passed 恒 False
    L2-rtl-simulation           Chisel→Verilator→golden   functional_passed 是实测

`fidelity` 字段会一路传到 Critic 的归因里，所以它不是「精度声明」，
是「这个数字是怎么来的」。L1 那个 `shared-model` 后缀尤其重要：
协同优化器用代价模型挑出获胜设计，Evaluator 再用同一个模型给它打分——
这时候「一致」是算术，不是确认。

后端见 `fast/adapters/`。
"""

from __future__ import annotations

from dataclasses import replace

from fast.adapters.base import EvaluationAdapter
from fast.schemas.models import EvaluationResult, ExperimentSpec, HardwareCandidate, Status


# 保真度阶梯：便宜的先跑，贵的只给通过了前一档的候选。
#
# 三档的成本差三个数量级（提案的预算表）：
#
#     Verilator   分钟，免费        功能对不对、周期数
#     Hammer      分钟             PPA
#     FireSim     $6/h（30h=$180） 高保真性能
#
# 每一档都是下一档的**前提**：功能没过就跑 PPA，量的是一个不工作的设计的
# 面积；PPA 超预算就跑 FireSim，是在一个注定被拒的点上烧最贵的那档。
FIDELITY_ORDER: tuple[str, ...] = ("L0", "L1", "L2", "L3")


def fidelity_rank(fidelity: str) -> int:
    """把 fidelity 字符串排到阶梯上。认不出的排最低——**「不知道有多可信」
    要当成「最不可信」**，否则一个拼错的标签会让最贵的后端被无条件调用。"""
    head = (fidelity or "").split("-", 1)[0].upper()
    return FIDELITY_ORDER.index(head) if head in FIDELITY_ORDER else 0


class EvaluatorAgent:
    """Normalizes one fidelity backend into the common evaluation contract.

    带上 `ladder` 就变成一个阶梯：按成本从低到高依次跑，前一档没过就不往
    上升。这是这个 Agent 唯一的**决策**——在此之前它只做归一化。
    """

    def __init__(self, adapter: EvaluationAdapter, ladder: tuple = ()):
        self.adapter = adapter
        # 从便宜到贵。空 = 只有一档，退化成原来的行为。
        self.ladder = ladder
        # 每一档为什么跑了或者没跑。升级决策要能被审——「没跑 FireSim」和
        # 「跑了 FireSim 但失败」在报告里必须区分得开。
        self.escalation: list[str] = []

    def run(self, spec: ExperimentSpec, candidate: HardwareCandidate,
            plan=None, kernel=None) -> EvaluationResult:
        if candidate.status is not Status.PASSED:
            return EvaluationResult(
                status=Status.SKIPPED,
                fidelity="none",
                functional_passed=False,
                cycles=None,
                throughput=None,
                pe_utilization=None,
                area=None,
                power=None,
                edp=None,
                wall_seconds=0.0,
                cloud_cost_usd=0.0,
                log_uri="",
                evidence=("hardware.status",),
                error="hardware candidate gate failed",
            )
        result = self.adapter.evaluate(spec, candidate, plan, kernel)
        if result.cloud_cost_usd < 0 or result.wall_seconds < 0:
            raise ValueError("evaluator returned invalid cost or duration")
        if not self.ladder:
            return result

        self.escalation = [f"{result.fidelity}: {'passed' if _clears(result) else 'stopped here'}"]
        best = result
        for backend in self.ladder:
            if not _clears(best):
                break
            upper = backend.evaluate(spec, candidate, plan, kernel)
            self.escalation.append(
                f"{upper.fidelity}: {'passed' if _clears(upper) else 'stopped here'}"
            )
            # **只在保真度真的更高时才替换，而且是逐字段合并、不是整体覆盖。**
            #
            # 一个后端标错了 fidelity 就可能让一个更弱的结果盖掉更强的，形状
            # 还完全一样——所以先比 rank。但只比 rank 还不够：各档**测的不是
            # 同一组量**。L2 跑真实 RTL，答的是功能对不对；利用率/面积/功耗
            # 仍然只有 L1 的解析模型给。整体覆盖的后果是**升到最高保真度反而
            # 知道得更少**：实测这一轮 L2 之后 pe_utilization/area/power 全变
            # None，于是 Critic 的利用率门和代价模型偏差检查都静默失效——
            # 又一个「有约束但不咬人」。
            if fidelity_rank(upper.fidelity) > fidelity_rank(best.fidelity):
                best = _merge(best, upper)
            if not _clears(upper):
                break
        return best



# 逐字段取「测到了它的那一档里最高的一档」。
_METRICS = ("cycles", "throughput", "pe_utilization", "area", "power", "edp")


def _merge(lower: EvaluationResult, upper: EvaluationResult) -> EvaluationResult:
    """把高保真度的结果盖在低保真度上，**但不抹掉它没测的量**。

    `fidelity` 报高的那一档，功能结论也归它——那是它唯一能答而低档答不了的
    问题。没测到的字段（None）保留低档的值，并在 `evidence` 里标出每个字段
    实际来自哪一档：一个混着 L1 面积和 L2 功能结论的结果，如果只标 L2，就是
    在给面积一个它没有的证据等级。
    """
    kept: dict[str, object] = {}
    borrowed: list[str] = []
    for field in _METRICS:
        high = getattr(upper, field)
        if high is None:
            kept[field] = getattr(lower, field)
            if kept[field] is not None:
                borrowed.append(f"{field}<-{lower.fidelity}")
        else:
            kept[field] = high
    evidence = tuple(upper.evidence) + tuple(borrowed)
    return replace(upper, evidence=evidence, **kept)

def _clears(result: EvaluationResult) -> bool:
    """这一档过了吗——过了才值得往上升。

    L2 以下的 `functional_passed` 恒为 False，那是「没检查」不是「失败」。
    把它当失败会让阶梯永远升不上去，而 L2 正是唯一能检查功能的那一档。
    """
    if result.status is not Status.PASSED:
        return False
    if fidelity_rank(result.fidelity) >= 2:
        return result.functional_passed
    return True
