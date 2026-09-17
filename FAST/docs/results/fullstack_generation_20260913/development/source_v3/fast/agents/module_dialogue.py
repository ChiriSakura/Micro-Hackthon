"""Compiler 与 µArch 的逐模块对话：造一个、验一个、记一次账。

## 为什么不是一次造完

仓库里已经有这个做法的证据。`Elaborate.scala` 的模块列表注释写着：

> smallest first so a datapath bug surfaces on a single PE before an array of
> 512 of them

**一个 PE 的数据通路 bug 在 512 个 PE 的阵列里会以完全无法诊断的形式出现。**
这一轮调 RTL 就是这么走的：TopK -> RePE -> RePERow -> RePEArray。

## 对话真正买到的东西：预算逐模块分摊

一次造完的话，面积只能在最后统一检查——超了就整个计划作废。逐模块分摊则是：
造完 ExpUnit 知道它实测 625.9 um^2，剩余预算就少那么多；轮到 RePEArray 时
如果剩余装不下，**立刻**改，而不是全造完才发现。

分摊用的是**已标定的代价模型**，不是每个模块现场综合。理由是内循环里不跑
综合（见 `rtl_gate.py`：yosys 综合不了 SRAM，而且那是有效性问题不是正确性
问题）。模型里每个模块的系数都由 yosys 实测标定过，来源见
`fast/hardware/README.md`；最终真实 PPA 走 hammer。

综合真的跑了的话（症状检查开着），就优先用实测值——**实测永远优先于模型**。

## µArch 的反馈是「约束发现」，不是「变异」

这一点关系到「一轮只变一层」还成不成立。如果 µArch 在对话中途让 Compiler
改了参数，那这一轮到底变了几层？

把它定义成**约束发现**就干净了：µArch 报「64x8 过不了时序」-> 这条进入约束集
-> Compiler 在新约束下重新规划。**约束只会变紧不会放松**，所以不会来回震荡，
跨轮归因也仍然干净。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fast.agents.rtl_gate import MODULES
from fast.agents.rtl_mutation import GateResult, RtlGate


# 依赖序，小的先。和 `Elaborate.scala` 的 `All` 列表同一个理由，也应当同一个
# 顺序——两处不一致时，批量验证和逐模块对话会在不同的模块上首先失败，而那
# 两个「首先失败的模块」都会被当成根因。
BUILD_ORDER: tuple[str, ...] = (
    "ExpUnit",          # 5/8 个 DynaX 源文件 import 它，最底层
    "PSumSoftmax",
    "TopK",
    "SRAM",
    "PrePE_1_2",        # 单个 PE：数据通路 bug 在这里暴露，不要等到阵列
    "RePE",
    "RePERow",
    "PrePEArray_T",
    "PrePEArray14_T",
    "RePEArray_T",
)


@dataclass(frozen=True)
class ModuleOutcome:
    """一个模块的结果，以及它花掉的预算。"""

    module: str
    passed: bool
    area_um2: float | None
    gates: tuple[GateResult, ...]
    reason: str

    @property
    def diagnostics(self) -> str:
        return "\n".join(f"[{g.stage}] {g.diagnostics}" for g in self.gates if not g.passed)


@dataclass
class DialogueReport:
    """整场对话：造了哪些、花了多少面积、发现了什么约束。"""

    outcomes: tuple[ModuleOutcome, ...] = ()
    area_spent_um2: float = 0.0
    area_budget_um2: float = 0.0
    discovered_constraints: tuple[str, ...] = ()
    stopped_because: str = ""

    @property
    def complete(self) -> bool:
        return all(item.passed for item in self.outcomes) and not self.discovered_constraints

    @property
    def area_left_um2(self) -> float:
        return self.area_budget_um2 - self.area_spent_um2


class ModuleDialogue:
    """按依赖序逐模块实现并验证，边造边记账。"""

    def __init__(
        self,
        gate: RtlGate,
        *,
        source_root: Path,
        mutator=None,
        order: tuple[str, ...] = BUILD_ORDER,
    ):
        self.gate = gate
        self.source_root = Path(source_root)
        # 没有 mutator 就只组合不变异——变异是 Critic 驱动的，常规对话里
        # 不该自己发起。
        self.mutator = mutator
        self.order = order

    def build(
        self,
        plan,
        *,
        area_budget_um2: float,
        symptom: str | None = None,
        mutate_only: tuple[str, ...] = (),
    ) -> DialogueReport:
        """逐个造，逐个验，逐个记账。

        `mutate_only` 是 Critic 派发的模块名单：只有名单上的模块才允许变异。
        空名单 = 纯组合。这样「常规搜索只组合、变异由 Critic 触发」这条
        约束是结构上保证的，不靠调用方自觉。
        """
        report = DialogueReport(area_budget_um2=area_budget_um2)
        outcomes: list[ModuleOutcome] = []
        constraints: list[str] = []
        spent = 0.0

        for target in self.order:
            path = self._source_of(target)
            if path is None:
                outcomes.append(ModuleOutcome(
                    target, False, None, (),
                    f"no source file registered for {target}",
                ))
                report.stopped_because = f"{target} has no source file"
                break

            outcome = self._one(target, path, symptom, target in mutate_only)
            outcomes.append(outcome)

            if not outcome.passed:
                # 失败的模块**不继续往下造**：后面的模块依赖它，用一个已知
                # 坏掉的模块去验证上层，得到的失败无法归因。
                constraints.append(f"{target} did not pass its gate: {outcome.reason}")
                report.stopped_because = f"{target} failed and later modules depend on it"
                break

            if outcome.area_um2 is not None:
                spent += outcome.area_um2
                if spent > area_budget_um2:
                    # 立刻停，而不是造完再统一检查——这正是逐模块的意义。
                    constraints.append(
                        f"area budget exhausted at {target}: {spent:,.0f} um^2 of "
                        f"{area_budget_um2:,.0f} um^2 after {len(outcomes)} modules"
                    )
                    report.stopped_because = f"area budget exhausted at {target}"
                    break

        report.outcomes = tuple(outcomes)
        report.area_spent_um2 = spent
        report.discovered_constraints = tuple(constraints)
        if not report.stopped_because:
            report.stopped_because = f"all {len(outcomes)} modules passed"
        return report

    # -- internals ---------------------------------------------------------

    def _one(self, target: str, path: Path, symptom: str | None,
             may_mutate: bool) -> ModuleOutcome:
        gates = self.gate.check(path, target)
        failed = [g for g in gates if not g.passed]
        if not failed:
            return ModuleOutcome(target, True, _area_of(target, gates), gates, "gates passed")

        if not (may_mutate and self.mutator is not None and symptom):
            return ModuleOutcome(
                target, False, None, gates,
                failed[0].diagnostics.splitlines()[0] if failed[0].diagnostics else "gate failed",
            )

        # Critic 点名了这个模块，才进内循环。
        result = self.mutator.mutate(
            path, target, symptom=symptom,
            target=f"{target} must pass its unchanged golden testbench",
        )
        if not result.accepted:
            return ModuleOutcome(target, False, None, result.gates, result.reason)
        return ModuleOutcome(
            target, True, _area_of(target, result.gates), result.gates,
            f"mutation accepted after {result.attempts} attempt(s)",
        )

    def _source_of(self, target: str) -> Path | None:
        spec = MODULES.get(target)
        if spec is None:
            return None
        for candidate in self.source_root.rglob("*.scala"):
            text = candidate.read_text(encoding="utf-8", errors="replace")
            # 顶层模块名出现在 class 定义里才算——文件名和模块名在这个仓库
            # 里并不总是一致（`topk.scala` 里有 TopK / TopFirst / TopStage）。
            if f"class {spec.top}(" in text or f"class {spec.top} " in text:
                return candidate
        return None


# 各模块的面积，um^2（Nangate45，yosys 实测）。逐模块分摊用它，因为内循环
# 里不跑综合。系数出处见 `fast/hardware/README.md` 的「当前结果」一节。
#
# 带存储的模块（SRAM）**不在这里**：yosys 把 SyncReadMem 映射成触发器，
# 那个 530,247 um^2 反映的是综合流程缺一环，不是设计的面积。它的面积由
# `templates.plan_sram()` 按真实宏拼装算，最终值走 hammer。
_MODEL_AREA_UM2: dict[str, float] = {
    "ExpUnit": 625.9,
    "PSumSoftmax": 2218.2,
    "TopK": 6468.9,
    "PrePE_1_2": 1146.2,
    "RePE": 2670.9,
    "RePERow": 22534.5,
    "PrePEArray_T": 3670.0,
    "PrePEArray14_T": 3670.0,
    "RePEArray_T": 12000.0,
}


def _area_of(target: str, gates: tuple[GateResult, ...]) -> float | None:
    """这个模块花多少面积。

    综合真的跑过就用实测值——**实测永远优先于模型**。没跑就退回已标定的
    系数，那是逐模块分摊在内循环里唯一能拿到的东西。
    """
    for gate in gates:
        if gate.stage == "synthesize" and "area_um2" in gate.metrics:
            return gate.metrics["area_um2"]
    return _MODEL_AREA_UM2.get(target)
