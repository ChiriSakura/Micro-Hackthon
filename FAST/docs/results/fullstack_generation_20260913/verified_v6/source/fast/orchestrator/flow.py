"""The CHIA driver/control plane; it is deliberately not a sixth agent."""

from __future__ import annotations

import hashlib
import re

from dataclasses import dataclass, field, replace

from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.agents.codesign import CoDesignSpace
from fast.schemas.conversions import (
    algorithm_parameters,
    kernel_result_from_measurement,
    measurement_from_kernel_result,
)
from fast.schemas.models import (
    ArchSpecs,
    Decision,
    ExperimentSpec,
    Layer,
    KernelResult,
    KernelSearchReport,
    RunReport,
    Status,
    digest_json,
    run_report_from_dict,
)
from fast.storage import ExperimentDB, ExperimentStore


@dataclass
class _LoopState:
    """跨轮携带的状态，以及下一轮该从哪一层重入。

    可变（不是 frozen）是刻意的：它就是「循环记住了什么」，而循环的每一步
    都在改它。把它做成不可变的会让每次重入都要重建一遍，那反而更容易漏字段。
    """

    candidate_index: int
    plan: object | None = None
    hardware: object | None = None
    replan: bool = True
    reimplement: bool = True
    tried_candidates: set[int] = field(default_factory=set)
    # 候选标签，用来解析 Critic 用**名字**指定的换候选动作。
    # 确定性 Critic 发 `candidate_index=<int>`，LLM Critic 发
    # `candidate="sanger"`——同一个动作的两种词汇，两种都要能落地。
    labels: tuple[str, ...] = ()
    #: 上一轮的「结果指纹」。用来发现**变异什么都没改**。
    last_fingerprint: tuple | None = None
    #: 归因到 µArch 时要施加的那条变异，和它对应的症状。
    #: 下一轮 `_round` 把它交给 `UArchAgent.mutate()` 去真正改 RTL。
    pending_uarch: object | None = None
    pending_symptom: str = ""
    #: 下一轮规划要执行的 compiler/planner_model 干预（钉住的维度、时钟上限）。
    pending_plan: object | None = None
    #: 连续指向同一个 (层, 证据量) 的次数，和那个瓶颈本身。
    bottleneck: tuple | None = None
    bottleneck_streak: int = 0
    #: 到目前为止**验证过的**最好目标值，和它是第几轮拿到的。
    best_objective: float | None = None
    best_round: int = -1
    rounds_without_progress: int = 0
    objective_front: tuple = ()

    def _converged(self, critique, report) -> str:
        """这一轮之后该不该停。返回停止理由，空串表示继续。

        两条判据，按信息量排：

        **① 瓶颈耗尽。** 同一个 (层, 证据量) 被连续指认
        `_BOTTLENECK_PATIENCE` 次而目标值没动 —— 这一层对这个瓶颈无能为力。
        实测那一轮 `['predicted.clock', 'plan.queue']` 连续出现 5 次，
        而 `predicted.clock` 六轮全是 396 MHz，一次没动过。

        **② 无进展。** 目标值连续 `_BOTTLENECK_PATIENCE` 轮相对改进小于
        `_PROGRESS_EPSILON`。**只在验证过的轮次上算**——L1 那一档的数是
        planner 自己代价模型算的，让它冒充进展等于让规划者给自己打分。
        """
        from fast.agents.pareto import extends_frontier, frontier_vectors
        vector = _pareto_of_report(report)
        improved = vector is not None and extends_frontier(
            self.objective_front, vector, _PROGRESS_EPSILON)
        if improved:
            self.objective_front = frontier_vectors((*self.objective_front, vector))
            self.best_objective = min(p[0] for p in self.objective_front)
            self.best_round = len(self.tried_candidates)
        if improved:
            self.rounds_without_progress = 0
        elif vector is not None:
            # 只有**验证过**的轮次才计入「没有进展」——没验证的轮次既不算
            # 进展也不算停滞，它只是没测。
            self.rounds_without_progress += 1

        key = _bottleneck_key(critique)
        if key == self.bottleneck:
            self.bottleneck_streak += 1
        else:
            self.bottleneck, self.bottleneck_streak = key, 1

        if self.bottleneck_streak >= _BOTTLENECK_PATIENCE and not improved:
            layer, evidence = key
            return (
                f"瓶颈耗尽：连续 {self.bottleneck_streak} 轮归因到 {layer} 的"
                f"同一组证据 {list(evidence)}，而目标值没有改进。"
                f"这一层对这个瓶颈无能为力。"
            )
        if self.rounds_without_progress >= _BOTTLENECK_PATIENCE:
            return (
                f"无进展：连续 {self.rounds_without_progress} 个验证过的轮次，"
                f"能耗–延迟前沿没有超过 {_PROGRESS_EPSILON:g} 的相对扩展"
            )
        return ""

    def _kernel_target(self, mutation) -> int | None:
        """kernel 层的变异指向哪个候选。

        **按值判断，不按字段名。** 字段名白名单试过，不够：同一个模型在
        一次运行里就用了两个名字——第 0 轮 `candidate`、第 2 轮
        `kernel_candidate`——于是一个完全正确的动作（换到另一个候选）被丢掉，
        报成「归因了但没有可施加的变异」。
        名字是模型自由发挥的部分，**值不是**：它要么是一个下标，要么是一个
        候选标签，两者都可判定。
        """
        value = mutation.value
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if text in self.labels:
            return self.labels.index(text)
        # 纯数字的字符串当下标；`candidate_index` 经 JSON 往返可能变成 "1"。
        if text.lstrip("-").isdigit():
            return int(text)

        # **对格式宽容，对含义严格。**
        #
        # 模型会按它在候选清单里看到的样子回写——实测发过
        # `"#1 xm:64:16:64"`（带 menu 里的序号前缀）。精确相等会把一个完全
        # 正确的动作丢掉，报成「归因了但没有可施加的变异」，循环第 1 轮就停。
        # 这是同一类问题的第三个变体：先是字段名（`candidate` /
        # `kernel_candidate`），然后是值的装饰。含义清楚的，就该落地。
        #
        # 取**最长**的唯一匹配，别依赖标签互不为前缀这种巧合。
        hits = sorted(
            (label for label in self.labels if label and label in text),
            key=len, reverse=True,
        )
        if hits:
            return self.labels.index(hits[0])
        # 只带序号的写法：`"#2"` / `"candidate 2"`。
        found = re.search(r"#\s*(\d+)", text) or re.fullmatch(r"\D*(\d+)\D*", text)
        if found:
            return int(found.group(1))
        return None

    def apply(self, critique, report) -> tuple[bool, str]:
        """按归因决定下一轮从哪里重入。返回 (要不要继续, 不继续的原因)。"""
        # **上一轮的变异如果什么都没改，就地停下。**
        #
        # 实测撞到过：Critic 连续两轮归因到 µArch 并发出
        # `uarch.queue rewrite` / `uarch.queue_rtl rewrite`，而
        # `UArchAgent.run(plan, template_id)` 是计划的**纯函数**——保计划重新
        # 实现，得到的必然是逐字节相同的硬件和逐字节相同的测量。三轮的计划
        # 和 util 完全一样，循环照常跑完，没有任何东西说「这两轮白跑了」。
        #
        # RTL 变异路径（`rtl_mutation.py` 的 LLM 改 Chisel + 机械门）现在接进
        # 来了，所以 `reimplement` **可以**真的改变东西——但只在配了 mutator
        # 且变异解析得到一个有门的模块时。其余情况仍然是空转，所以这个检查
        # 留着：它同时也抓「门自己跑不起来」那一类静默失败。
        # ---- 收敛判据 ------------------------------------------------------
        #
        # **由 orchestrator 强制执行，不交给 LLM。** Critic 自己也有「连续三次
        # 同症状就升级」的逻辑，但那取决于采样——温度 0.2 下实测那一轮就没
        # 触发，同一个瓶颈被指认了 5 次。
        stop = self._converged(critique, report)
        if stop:
            return False, stop

        fingerprint = _round_fingerprint(report)
        if fingerprint is not None and fingerprint == self.last_fingerprint:
            return False, (
                "上一轮的变异没有改变任何东西：计划、测量和 RTL 状态都与前一轮"
                "完全相同。归因到 µArch 却没有 RTL 改动落地时，检查："
                "变异是不是解析到了模块、门是不是自己跑不起来"
                "（诊断里的 [gate-infrastructure]）、以及有没有开 --mutate-rtl。"
            )
        self.last_fingerprint = fingerprint
        self.tried_candidates.add(self.candidate_index)
        self.replan = False
        self.reimplement = False

        for mutation in critique.mutations:
            if mutation.layer is Layer.KERNEL:
                index = self._kernel_target(mutation)
                if index is None:
                    continue
                if index in self.tried_candidates:
                    return False, f"candidate {index} already tried"
                # 换了工作负载，计划必须跟着重来——同一份硬件对不同稀疏度
                # 不是同一个取舍。
                self.candidate_index = index
                self.replan = True
                return True, ""
            if mutation.layer in (Layer.COMPILER, Layer.PLANNER_MODEL):
                # **把干预带到下一轮的规划里。**
                #
                # 这里曾经只设 `replan=True`，field / value / expected_effect
                # 全被丢掉——下一轮用同样的输入再调一次 `plan()`，规则
                # proposer 会确定性地给出**完全相同**的结果。「重入某层」
                # 不等于「执行了该层的建议」，这和 µArch 那条曾经犯过的错
                # 是同一个。
                from fast.agents.codesign import plan_intervention

                intervention = plan_intervention([mutation])
                if not intervention.actionable:
                    # 认不出就**明确报不支持**，不要假装重规划了一次。
                    return False, (
                        f"attributed to {mutation.layer.value} but the intervention "
                        f"cannot be executed: {'; '.join(intervention.unsupported)}"
                    )
                self.pending_plan = intervention
                self.replan = True
                return True, ""
            if mutation.layer is Layer.UARCH:
                # **计划不动**：这一轮只验证 RTL 的改动有没有用。
                # 变异本身要带到下一轮——`UArchAgent.run()` 是计划的纯函数，
                # 不把这条变异交给它去改 RTL，「重新实现」就只是再算一遍。
                self.reimplement = True
                self.pending_uarch = mutation
                self.pending_symptom = critique.summary
                return True, ""
            if mutation.layer is Layer.EVALUATOR:
                # 计划和硬件都不动，只换保真度。
                return True, ""

        return False, (
            f"attributed to {critique.attribution.value} but the critique carried "
            f"no mutation to act on: {critique.summary}"
        )


# --- 收敛判据 ---------------------------------------------------------------
#
# 在此之前循环只有一条停止条件：轮数用完。14 次运行里大半是那么停的，而它
# 什么也不说明——「跑完了」会被读成「收敛了」。

#: 同一个 (层, 证据量) 被连续归因多少次之后，认为这一层对这个瓶颈无能为力。
#: 3 而不是 2：一次重试是正常的（变异可能第一次没写对），两次还没动就不是
#: 运气问题了。实测那一轮同一个瓶颈被指认了 **5** 次。
_BOTTLENECK_PATIENCE = 3

#: 目标值的相对改进小于这个数就不算进展。
#:
#: 1e-3 的依据是**离散性**而不是拟合：阵列规模、queue_depth、divider 级数都
#: 是离散档位，真实的改进至少是百分之几量级（16x8 -> 16x16 是 100%）。比它
#: 小的只可能是浮点噪声——实测 5 轮的利用率相同到 16 位小数，用 `>` 会把
#: 尾数差当成改进。
_PROGRESS_EPSILON = 1e-3


def _bottleneck_key(critique) -> tuple:
    """一条归因指向的「层 + 量」。

    用 `evidence` 而不是 `summary`：前者是结构化字段路径（实测那一轮连续
    五次都是 `['predicted.clock', 'plan.queue']`），后者是自由文本，同一个
    瓶颈每轮措辞都不同，比不出「又是它」。
    """
    return (critique.attribution.value, tuple(sorted(critique.evidence)))


@dataclass(frozen=True)
class _MutationRow:
    """一次变异在共享板上的那一行。

    **必须是 dataclass**：`record_stage` 走 `canonical_json` -> `to_primitive`，
    而它只认 dataclass。用普通对象会在真实流程里直接抛
    `TypeError: Object of type _MutationRow is not JSON serializable`——
    单元测试覆盖不到这条路径，是端到端检查抓出来的。
    """

    module: str
    accepted: bool
    attempts: int
    component: str | None
    measured_critical_path_ns: float | None
    measured_area_um2: float | None
    status: str | None = None
    error: str | None = None


def _mutation_row(outcome):
    """一次变异在板子上的那一行：改了哪个模块、过没过门、量到了什么。"""
    from fast.agents.codesign import component_of_module

    module = getattr(outcome, "module", "")
    metrics = getattr(outcome, "metrics", {}) or {}
    return _MutationRow(
        module=module,
        accepted=bool(getattr(outcome, "accepted", False)),
        attempts=getattr(outcome, "attempts", 0),
        component=component_of_module(module),
        measured_critical_path_ns=metrics.get("critical_path_ns"),
        measured_area_um2=metrics.get("area_um2"),
    )


def _objective_of_report(report) -> float | None:
    """一轮的目标值：**延迟，越小越好**。没验证过或没通过的轮次不算数。

    三个门，每一个都出过事：

    1. **保真度**必须真的跑过 RTL。L1 那一档的利用率是 planner 自己代价模型
       算的（证据字段自己写着 NOT INDEPENDENT），拿它当进展等于让规划者
       给自己打分。
    2. **功能必须通过**。原来只查 fidelity 字符串——一个 L2 **失败**的轮次
       照样被当成进展参与收敛计算。"跑过 RTL"不等于"结果是对的"。
    3. **目标用统一的那个**（`ObjectiveSpec`）。这里曾经用吞吐，而内层按
       edp 排、报告用 (延迟, 功耗) 帕累托——三处对"变好"的定义都不同。

    时钟优先用**实测**：µArch 的变异改的是 RTL，计划里的 `predicted_clock_ns`
    是模型算的，模型不知道 RTL 变了。
    """
    from fast.agents.codesign import effective_clock_ns

    evaluation = getattr(report, "evaluation", None)
    plan = getattr(report, "compiler", None)
    if evaluation is None or plan is None:
        return None
    if not str(getattr(evaluation, "fidelity", "")).startswith("L2"):
        return None
    if not getattr(evaluation, "functional_passed", False):
        return None

    cycles = getattr(plan, "predicted_cycles", None)
    clock = getattr(plan, "predicted_clock_ns", None)
    outcome = getattr(report, "mutation", None)
    if outcome is not None and getattr(outcome, "accepted", False):
        from fast.agents.codesign import component_of_module

        component = component_of_module(getattr(outcome, "module", ""))
        measured = (getattr(outcome, "metrics", {}) or {}).get("critical_path_ns")
        if component and measured:
            clock = effective_clock_ns(
                num_rows=getattr(plan, "num_rows", 32),
                pe_per_row=getattr(plan, "pe_per_row", 4),
                queue_depth=getattr(plan, "queue_depth", 0),
                divider_stages=getattr(plan, "divider_stages", 8),
                measured={component: measured},
            )
    if not cycles or not clock:
        return None
    return cycles * clock          # ns，越小越好

def _pareto_of_report(report):
    """Modelled Pareto progress on function-checked designs, not measured energy."""
    from fast.agents.pareto import valid_vector
    latency_ns = _objective_of_report(report)
    power_mw = getattr(getattr(report, "compiler", None), "predicted_power_mw", None)
    if not valid_vector((latency_ns, power_mw)):
        return None
    kernel = getattr(report, "kernel", None)
    spec = getattr(report, "spec", None)
    if kernel is not None and spec is not None:
        if kernel.status is not Status.PASSED or kernel.quality_loss > spec.epsilon:
            return None
    return (latency_ns * 1e-9, latency_ns * power_mw * 1e-12)


def _round_fingerprint(report):
    """一轮的结果指纹：计划的形状 + 实测到的量。

    只取**被测量的**字段。两轮指纹相同 = 中间那次变异什么都没改。
    拿不到 report（测试里会传 None）就返回 None，永不相等。
    """
    if report is None:
        return None
    plan = getattr(report, "compiler", None)
    evaluation = getattr(report, "evaluation", None)
    if plan is None or evaluation is None:
        return None
    return (
        getattr(plan, "num_rows", None), getattr(plan, "pe_per_row", None),
        getattr(plan, "queue_depth", None), getattr(plan, "divider_stages", None),
        getattr(plan, "bank_count", None), getattr(plan, "sram_bytes", None),
        # 计划预测的周期数也是这一轮的身份：两轮预测周期不同就是两个不同的
        # 设计点，哪怕形状参数碰巧一样。漏了它会把有改进的一轮误判成空转。
        getattr(plan, "predicted_cycles", None),
        getattr(plan, "predicted_clock_ns", None),
        getattr(evaluation, "functional_passed", None),
        getattr(evaluation, "pe_utilization", None),
        getattr(evaluation, "cycles", None), getattr(evaluation, "area", None),
        getattr(plan, "predicted_power_mw", None),
        # **RTL 也算进指纹。** 一次成功的变异改的是 Chisel 源文件，而
        # 利用率/面积这些是从计划算的、不会动；只看它们的话一次真正改了
        # RTL 的轮次会被误判成「什么都没改」而把循环停掉。
        _rtl_state(report),
    )


def _rtl_state(report):
    """这一轮 RTL 处于什么状态：变异过哪个模块、成功没有、改成什么样。

    源码摘要用哈希，不放原文——指纹只是拿来比相等的。
    """
    outcome = getattr(report, "mutation", None)
    if outcome is None:
        return None
    source = getattr(outcome, "source", None)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16] if source else None
    return (getattr(outcome, "module", ""), getattr(outcome, "accepted", False), digest)

def _takes_history(critic) -> bool:
    """规则版 Critic 不吃跨轮历史，LLM 版吃。

    用签名探测而不是 isinstance：两者只共享 schema，不共享基类——这正是
    「契约不变、实现可换」想要的性质。
    """
    import inspect

    try:
        return "history" in inspect.signature(critic.run).parameters
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class LoopReport:
    """一次闭环运行：kernel 搜索 + 每轮的完整报告 + 为什么停下来。

    `stopped_because` 不是装饰。循环停下来有很多种原因——Critic 判 STOP、
    轮数用完、归因到一个还没接上的层——**它们的下一步完全不同**，混成
    「跑完了」会让人以为搜索收敛了。
    """

    search: KernelSearchReport
    rounds: tuple[RunReport, ...]
    stopped_because: str

    @property
    def last(self) -> RunReport | None:
        return self.rounds[-1] if self.rounds else None


class FiveAgentFlow:
    def __init__(
        self,
        kernel: KernelAgent,
        compiler: CompilerAgent,
        uarch: UArchAgent,
        evaluator: EvaluatorAgent,
        critic: CriticAgent,
        *,
        store: ExperimentStore | None = None,
        db: ExperimentDB | None = None,
        # **同一份不可变的约束交给所有阶段**（见下面的赋值）。
        specs: ArchSpecs | None = None,
        # 模型的真实 head 维度，和分块尺寸 `tile_d` 是两回事。
        head_dim: int = 64,
        sequence_length_override: int | None = None,
    ):
        self.kernel = kernel
        self.compiler = compiler
        self.uarch = uarch
        self.evaluator = evaluator
        self.critic = critic
        self.store = store
        self.db = db
        # **同一份不可变的约束交给所有阶段。** CLI 声明的约束原来只到
        # Critic 和报告，而规划路径用的是 `plan()` 里的 `ArchSpecs()` 默认值
        # ——「声明的约束」和「搜索实际用的约束」可以不是一个，事后拒绝
        # 代替不了约束内搜索。
        self.specs = specs
        # 模型的真实 head 维度。代价模型必填（见 `estimate` 的说明）。
        self.head_dim = head_dim
        #: 共享板上这次循环的 run_id。 写第一轮时填上，
        #: 之后用来查轨迹（组装 prompt）和验证过的最优点。
        self.run_id: str | None = None
        # Compiler Agent 现在自己就是 planner：软硬件参数在同一次搜索里定。
        # 以前这里注入一个可选的 CoOptimizer，于是有两条产出同类型但质量
        # 完全不同的 `CompilerSchedule` 的路径——那个歧义是架构没划清的痕迹。
        self.last_plan_search = None
        #: 上一次规划实际执行的干预，供报告说明「这一轮改了什么」。
        self.last_intervention = None

    def run(self, spec: ExperimentSpec, *, template_id: str) -> RunReport:
        key = f"{spec.experiment_id}/{spec.candidate_id}"
        from fast.agents.codesign import DEFAULT_OBJECTIVE
        cache_input = {"spec": spec, "template_id": template_id,
                       "arch_specs": self.specs, "head_dim": self.head_dim,
                       "objective": getattr(self.compiler, "objective", None) or DEFAULT_OBJECTIVE,
                       "cost_model_version": "energy-latency-si-v1"}
        if self.store is not None:
            cached = self.store.get(key, "report", digest_json(cache_input))
            if cached is not None:
                return replace(
                    run_report_from_dict(cached),
                    cache_hits=("kernel", "compiler", "uarch", "evaluator", "critic"),
                )

        kernel = self.kernel.run(spec)
        report = self._downstream(spec, kernel, template_id, label=spec.candidate_id)
        if self.store is not None:
            self._cache(key, cache_input, report)
        return report

    def _cache(self, key: str, cache_input: dict, report: RunReport) -> None:
        """Cache each stage on the inputs that produced it, plus the whole report."""
        spec, kernel = report.spec, report.kernel
        compiler, hardware = report.compiler, report.hardware
        evaluation, critique = report.evaluation, report.critique
        self.store.put(key, "kernel", spec, kernel)
        self.store.put(key, "compiler", kernel, compiler)
        self.store.put(key, "uarch", compiler, hardware)
        self.store.put(key, "evaluator", (spec, hardware), evaluation)
        self.store.put(key, "critic", (spec, kernel, compiler, hardware, evaluation), critique)
        self.store.put(key, "report", cache_input, report)

    def search_then_build(
        self,
        spec: ExperimentSpec,
        *,
        template_id: str,
        proposer=None,
        space=None,
        batch: int = 4,
        candidates: int = 3,
        candidate_index: int = 0,
    ) -> tuple[KernelSearchReport, RunReport | None]:
        """搜索 kernel 空间，把第 `candidate_index` 个候选交给下游。

        proposal 里 Kernel Agent 的产出是「map the sparsity-accuracy Pareto
        frontier」和复数的 sparse-index profiles。**K 个候选不是用来并行
        评估的，是 Critic 在算法层的动作空间**：归因到算法层时，mutation
        从「盲目调一个参数」变成「换到候选 #2」——一个已经量过精度和稀疏度
        的点，不用重测。
        """
        search = self.kernel.search(
            spec, proposer=proposer, space=space, batch=batch,
            candidate_count=candidates, db=self.db,
        )
        chosen = _pick_candidate(search, candidate_index)
        if chosen is None:
            return search, None

        kernel = kernel_result_from_measurement(search, chosen)
        report = self._downstream(
            spec, kernel, template_id, label=chosen.label,
            candidates=search.candidates, candidate_index=candidate_index,
        )
        return search, report


    def run_loop(
        self,
        spec: ExperimentSpec,
        *,
        template_id: str,
        rounds: int = 3,
        candidates: int = 3,
        proposer=None,
        space=None,
        batch: int = 4,
    ) -> "LoopReport":
        """闭环：搜一次 kernel，然后按 Critic 的归因迭代。

        ## 一轮只变一层

        串行循环靠**跨轮对比**做归因（并行扇出靠同轮的受控对比）。同一轮里
        改两层，下一轮就分不清是哪一处改动起的作用。所以每轮只施加 Critic
        给出的**一个**变异。

        ## kernel 只搜一次

        K 个候选是 Critic 在算法层的动作空间，不是每轮重搜的东西：归因到
        算法层时，变异是「换到候选 #2」——一个精度和稀疏度都已经量过的点。
        重搜等于把已经花掉的测量预算再花一遍。

        ## 停止

        Critic 说 STOP，或者轮数用完，或者变异指向一个已经试过的状态。
        """
        search = self.kernel.search(
            spec, proposer=proposer, space=space, batch=batch,
            candidate_count=candidates, db=self.db,
        )
        if _pick_candidate(search, 0) is None:
            return LoopReport(search=search, rounds=(), stopped_because="no kernel candidate cleared epsilon")

        history: list[RunReport] = []
        state = _LoopState(
            candidate_index=0,
            labels=tuple(item.label for item in search.candidates),
        )
        stopped = f"exhausted {rounds} rounds"

        for _ in range(rounds):
            chosen = _pick_candidate(search, state.candidate_index)
            kernel = kernel_result_from_measurement(search, chosen)
            report = self._round(
                spec, kernel, template_id, state,
                label=chosen.label, candidates=search.candidates,
                history=tuple(history),
            )
            history.append(report)

            critique = report.critique
            if critique.decision is Decision.STOP:
                stopped = f"critic stopped: {critique.summary}"
                break

            advanced, why = state.apply(critique, report)
            if not advanced:
                stopped = why
                break

        return LoopReport(search=search, rounds=tuple(history), stopped_because=stopped)

    def _round(self, spec, kernel, template_id, state, *, label, candidates, history):
        """按 Critic 上一轮的归因，**只重做该重做的那一层**。

        重跑整轮是错的，不只是慢：归因到 µArch 却顺带重新规划，下一轮就分不清
        改善来自 RTL 修复还是来自新计划——「一轮只变一层」就失效了。

            KERNEL / COMPILER / PLANNER_MODEL   重新规划（工作负载或约束变了）
            UARCH                               保计划，只重新实现
            EVALUATOR                           保计划和硬件，只重新评估
        """
        if state.plan is None or state.replan:
            # Critic 提的干预（钉住某个维度、收紧时钟上限）要**真的进这次
            # 搜索**，否则规则 proposer 会给出完全相同的计划，这一轮就是空转。
            intervention = state.pending_plan
            space = intervention.restrict(CoDesignSpace()) if intervention else None
            specs = self.specs
            if intervention is not None and intervention.max_clock_ns:
                # 时钟上限翻成频率下限——`violations()` 认的是 target_mhz。
                floor_mhz = 1000.0 / intervention.max_clock_ns
                base = specs or ArchSpecs()
                specs = replace(base, target_mhz=max(base.target_mhz, floor_mhz))
            compiler = self.compiler.plan(
                kernel, sequence_length=spec.sequence_length, specs=specs,
                head_dim=self.head_dim, space=space, **algorithm_parameters(kernel),
            )
            self.last_intervention = intervention
            state.pending_plan = None
            self.last_plan_search = self.compiler.last_search
            state.plan = compiler
            state.hardware = None
        else:
            compiler = state.plan

        mutation_outcome = None
        if state.hardware is None or state.reimplement:
            # 归因到 µArch 时**先改 RTL 再实现**。改写由 `RtlMutator` 做，
            # 能不能用由机械门判——LLM 碰不到金标准和 testbench。
            if state.pending_uarch is not None:
                mutation_outcome = self.uarch.mutate(
                    state.pending_uarch,
                    symptom=state.pending_symptom,
                    target=getattr(state.pending_uarch, "expected_effect", ""),
                )
                state.pending_uarch = None
                state.pending_symptom = ""
            hardware = self.uarch.run(compiler, template_id=template_id)
            state.hardware = hardware
        else:
            hardware = state.hardware

        evaluation = self.evaluator.run(spec, hardware, compiler, kernel)
        critique = self.critic.run(
            spec, kernel, compiler, hardware, evaluation,
            candidates=candidates, candidate_index=state.candidate_index,
            **({"history": history} if _takes_history(self.critic) else {}),
        )
        self._record(spec, kernel, compiler, hardware, evaluation, critique, label,
                     round_index=len(history), mutation=mutation_outcome)
        return RunReport(spec, kernel, compiler, hardware, evaluation, critique,
                         mutation=mutation_outcome)

    def _downstream(self, spec, kernel, template_id, *, label: str,
                    candidates: tuple = (), candidate_index: int = 0) -> RunReport:
        """Compiler(planner) -> uArch(implementer) -> Evaluator -> Critic.

        一条路径，没有分支。planner 规划完整的硬件配置，implementer 只负责
        把它实现出来并给出证据。
        """
        compiler = self.compiler.plan(
                kernel, sequence_length=spec.sequence_length, specs=self.specs,
                head_dim=self.head_dim, **algorithm_parameters(kernel),
            )
        self.last_plan_search = self.compiler.last_search
        hardware = self.uarch.run(compiler, template_id=template_id)

        evaluation = self.evaluator.run(spec, hardware, compiler, kernel)
        critique = self.critic.run(
            spec, kernel, compiler, hardware, evaluation,
            candidates=candidates, candidate_index=candidate_index,
        )

        self._record(spec, kernel, compiler, hardware, evaluation, critique, label)
        # `_downstream` 是一次性的单程路径，没有「上一轮的变异」可施加。
        return RunReport(spec, kernel, compiler, hardware, evaluation, critique)

    def _record(self, spec, kernel, compiler, hardware, evaluation, critique, label,
                *, round_index: int = 0, mutation=None):
        """把一轮的每一层写进共享库。分层重入下这尤其重要：某一层这一轮
        没有重跑，它在库里仍然要有一行，否则 cross_layer 视图 join 不上，
        跨轮对比就断了。"""
        if self.db is None:
            return
        run_id = self.db.start_run(spec, proposer="flow")
        # The cross_layer view starts from the kernel row, so a candidate that
        # entered through run() rather than a search still needs one; without
        # it every downstream stage is recorded but nothing can be joined.
        self.db.record_measurements(run_id, [measurement_from_kernel_result(label, kernel)])
        self.db.record_stage(run_id, label, "compiler", compiler, round_index=round_index)
        self.db.record_stage(run_id, label, "uarch", hardware, round_index=round_index)
        self.db.record_stage(run_id, label, "evaluator", evaluation, round_index=round_index)
        self.db.record_attribution(run_id, label, critique, round_index=round_index)
        # 变异实测到的模块关键路径要进板子，否则它对目标的影响不可见——
        # 实测撞到过：两次变异 accepted=True 而延迟四轮完全没动。
        if mutation is not None:
            self.db.record_stage(run_id, label, "uarch_mutation",
                                 _mutation_row(mutation), round_index=round_index)
        self.run_id = run_id
        self.db.finish_run(run_id)


def _pick_candidate(search: KernelSearchReport, index: int):
    """取第 index 个候选；没有候选时退回 `best`。

    退回是为了让只关心单点的老调用路径继续能跑，不是因为退回值等价——
    候选列表是按硬件相关的多样性挑的，`best` 只是最稀疏的那个。
    """
    if search.candidates:
        return search.candidates[min(index, len(search.candidates) - 1)]
    return search.best


# Compatibility for older replay scripts; new callers use schemas.conversions.
_as_kernel_result = kernel_result_from_measurement
_as_measurement = measurement_from_kernel_result
