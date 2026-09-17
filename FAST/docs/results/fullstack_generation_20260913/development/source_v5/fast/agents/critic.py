"""Critic Agent：证据绑定的瓶颈归因，以及下一轮的 mutation。

在流水线里的位置：Kernel → Compiler → µArch → Evaluator → **Critic**。

规则版实现。它的契约不是「结论对不对」，而是**每个结论都必须指向产生它的
那条证据**：`Critique.evidence` 里放的是字段路径（如
`evaluation.functional_passed`），不是自然语言理由。这样做的目的是让
LLM 版本后续可以直接替换实现而不改 schema——归因的可审计性来自结构，
不来自模型。

归因到 `Layer`（KERNEL / COMPILER / UARCH / EVALUATOR）之后，
`Mutation` 描述下一轮该改哪一层的哪个字段、预期效果和风险。
跨层归因需要各 Agent 的搜索历史，那份共享数据在
`fast/storage/experiment_db.py` 的 `cross_layer` 视图里。
"""

from __future__ import annotations

from fast.schemas.models import (
    CompilerSchedule,
    Critique,
    Decision,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelResult,
    Layer,
    Mutation,
    Status,
)


class CriticAgent:
    """Evidence-bound rule critic; an LLM can later propose the same schema."""

    def review_search(self, context) -> Critique:
        """Analyse joint-search evidence using the same Critique contract."""
        from fast.agents.rediscovery_critic import rule_review
        return rule_review(context)

    def run(
        self,
        spec: ExperimentSpec,
        kernel: KernelResult,
        compiler: CompilerSchedule | None,
        hardware: HardwareCandidate | None,
        evaluation: EvaluationResult | None,
        *,
        candidates: tuple = (),
        candidate_index: int = 0,
    ) -> Critique:
        """归因，并给出下一轮的变异向量。

        `candidates` 是 Kernel Agent 交上来的候选列表。**它不是用来并行评估
        的，是这个 Agent 在算法层的动作空间**：归因到算法层时，变异从
        「盲目调一个参数」变成「换到候选 #2」——一个精度和稀疏度都已经量过的
        点，不用重测。

        一轮只变一层。串行循环靠跨轮对比做归因，同一轮里改两层就没法归因了。
        """
        if kernel.status is not Status.PASSED:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.KERNEL,
                decision=Decision.REVERT,
                summary="quality loss exceeds the configured epsilon",
                evidence=("kernel.quality_loss", "spec.epsilon"),
                mutations=(Mutation(
                    layer=Layer.KERNEL,
                    field="sparsity_x",
                    operation="increase",
                    value=1,
                    expected_effect="retain more attention values and reduce quality loss",
                    risk="lower sparsity and speedup",
                ),),
            )
        # 模板本身没通过验证门的话，这一条最根本——它会让 planner 也一起
        # 失败（可行性检查查不到模板），但根因不在规划里。先判它，否则归因
        # 会落在「规划找不到可行点」上，指向一个错误的层。
        if hardware is not None and not hardware.verified_template:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.UARCH,
                decision=Decision.REVERT,
                summary="no verified hardware candidate reached evaluation",
                evidence=("hardware.status", "hardware.verified_template"),
            )

        if compiler is not None and compiler.status is not Status.PASSED:
            # 规划失败有两种：约束太紧（换候选没用，要放宽约束），
            # 或者这个候选的工作量在任何可行硬件上都装不下（换候选有用）。
            # `compiler.error` 里带着具体的违反项，两者由它区分。
            switch = _switch_to_next(candidates, candidate_index)
            return Critique(
                status=Status.PASSED,
                attribution=Layer.COMPILER,
                decision=Decision.REVERT,
                summary=f"planner found no feasible hardware: {compiler.error}",
                evidence=("compiler.status", "compiler.error"),
                mutations=(switch,) if switch is not None else (),
            )

        # 实测和规划预测偏离过大 -> 瓶颈不在任何一层硬件，在代价模型里。
        model_gap = _planner_model_gap(compiler, evaluation)
        if model_gap is not None:
            return model_gap

        if hardware is None or hardware.status is not Status.PASSED:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.UARCH,
                decision=Decision.REVERT,
                summary="no verified hardware candidate reached evaluation",
                evidence=("hardware.status", "hardware.verified_template"),
            )
        if evaluation is None:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.EVALUATOR,
                decision=Decision.REVERT,
                summary="no evaluation reached the critic",
                evidence=("evaluation.functional_passed",),
            )

        # **「没检查」和「检查失败」是两件事。**
        #
        # 只有 L2 才真的跑 RTL；L0 和 L1 的 `functional_passed` 恒为 False——
        # 那是「这一档回答不了这个问题」，不是「这个设计功能不对」。把前者当
        # 后者会让循环在第 0 轮就以「功能验证失败」停下，而它根本没验证过。
        #
        # 保真度阶梯本身（什么时候该升到 L2）是 Evaluator 的决策，现在还没做。
        can_check_function = "rtl" in (evaluation.fidelity or "").lower()
        if can_check_function and not evaluation.functional_passed:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.UARCH,
                decision=Decision.REVERT,
                summary="RTL simulation did not match the golden model",
                evidence=("evaluation.functional_passed", "evaluation.log_uri",
                          "evaluation.fidelity"),
            )
        if evaluation.pe_utilization is not None and evaluation.pe_utilization < 0.70:
            # 低利用率的根因是**行长不均衡**，而它由稀疏方法决定——实测同样
            # 稀疏度下 nm 的 tile 内不均衡度是 1.00 而 xm 是 1.41。所以第一
            # 手段是换一个已经量过的候选，不是盲目调并行度。
            switch = _switch_to_next(candidates, candidate_index, for_utilisation=True)
            return Critique(
                status=Status.PASSED,
                attribution=Layer.KERNEL if switch is not None else Layer.COMPILER,
                decision=Decision.CONTINUE,
                summary=(
                    "PE utilization is below target; the row-length spread is set "
                    "by the sparse method"
                    if switch is not None else
                    "PE utilization is below target and no other candidate remains"
                ),
                evidence=(
                    "evaluation.pe_utilization",
                    "kernel.profile.tile_load_imbalance",
                    "compiler.queue_depth",
                ),
                mutations=(switch,) if switch is not None else (Mutation(
                    layer=Layer.COMPILER,
                    field="queue_depth",
                    operation="increase",
                    value=2,
                    expected_effect="let a finished row start the next tile early",
                    risk="deeper queues lengthen the critical path (measured "
                         "3.140 ns at depth 8 against the array's 2.230 ns)",
                ),),
            )
        summary = (
            "acceptance gates passed"
            if can_check_function else
            f"acceptance gates passed on metrics, but {evaluation.fidelity} cannot "
            f"confirm functional correctness"
        )
        return Critique(
            status=Status.PASSED,
            attribution=Layer.EVALUATOR,
            decision=Decision.STOP,
            summary=summary,
            evidence=("kernel.quality_loss", "evaluation.fidelity",
                      "evaluation.pe_utilization"),
        )


# 实测和规划预测允许的最大相对偏差。超过就认为代价模型本身有问题。
#
# 25%：实测标定点自己的离散度在 ±13% 量级（每 lane 功耗两个标定点相差 21%），
# 所以阈值必须明显高于噪声，否则每一轮都会归因到模型。而这一轮撞到的真实
# 偏差是 40 倍、200 倍、44 倍——真出问题时不会差一点点。
_PLANNER_MODEL_TOLERANCE = 0.25


def _planner_model_gap(
    compiler: CompilerSchedule, evaluation: EvaluationResult | None
) -> Critique | None:
    """实测偏离规划预测太多时，瓶颈在代价模型里，不在任何一层硬件。

    **这一类错误此前全靠人发现**：SRAM 面积系数小 40 倍、EDP 公式里没有时钟
    周期（差 44 倍）、功耗是任意单位（32x4 算出 2.85 而实测 398.7 mW）。
    它们的共同形状是「没有任何东西会报错」——流水线照常跑完，数字看起来正常，
    只是它描述的不是被测的那个东西。

    让循环能自己发现这件事，是它比逐层调优强的地方之一。
    """
    if evaluation is None or evaluation.status is not Status.PASSED:
        return None

    # **评估必须是独立的测量，否则这个判据没有意义。** `L1-analytical-
    # shared-model` 是 planner 用来挑设计的那同一个代价模型——拿一个模型和
    # 它自己比，然后断言模型错了，是循环论证。
    #
    # 但共用模型下两边真的对不上时，那是**实现 bug**（同一个公式两处实现
    # 分叉了），不是标定问题。两者的下一步完全不同，所以归因也不同。
    shared_model = "shared-model" in (evaluation.fidelity or "")

    pairs = (
        ("area", compiler.predicted_area_um2, evaluation.area),
        ("power", compiler.predicted_power_mw, evaluation.power),
        ("cycles", compiler.predicted_cycles, evaluation.cycles),
    )
    for name, predicted, measured in pairs:
        if predicted is None or measured is None or predicted <= 0:
            continue
        error = abs(measured - predicted) / predicted
        if error <= _PLANNER_MODEL_TOLERANCE:
            continue
        if shared_model:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.INFRASTRUCTURE,
                decision=Decision.REVERT,
                summary=(
                    f"planner and evaluator share one cost model but disagree on "
                    f"{name} by {error * 100:.0f}%; one of the two implementations "
                    f"has drifted"
                ),
                evidence=(f"compiler.predicted_{name}", f"evaluation.{name}",
                          "evaluation.fidelity"),
            )
        if True:
            return Critique(
                status=Status.PASSED,
                attribution=Layer.PLANNER_MODEL,
                decision=Decision.CONTINUE,
                summary=(
                    f"measured {name} {measured:,.0f} is {error * 100:.0f}% away from "
                    f"the planned {predicted:,.0f}; the cost model, not the hardware, "
                    f"is what is wrong"
                ),
                evidence=(f"compiler.predicted_{name}", f"evaluation.{name}"),
                mutations=(Mutation(
                    layer=Layer.PLANNER_MODEL,
                    field=name,
                    operation="recalibrate",
                    value=round(measured / predicted, 4),
                    expected_effect=f"scale the {name} model onto the measurement",
                    risk="one measurement is not a calibration; confirm the "
                         "direction holds at another design point first",
                ),),
            )
    return None


def _tile_imbalance(item, num_rows: int = 32) -> float | None:
    """**只认实测值。** 没测到返回 None，不用全局 `load_imbalance` 顶替。

    顶替的后果是拿两个不同的量比大小：同一个 `xm:32:16:64`，全局是 2.666
    而实测 tile(32) 是 1.425，且两者的**排序不同**。这条判据要决定「换过去
    是不是更均衡」，用混着两种量的数比出来的结论没有意义。
    """
    profile = getattr(item, "profile", None)
    if profile is None:
        return None
    try:
        measured = profile.tile_imbalance_measured(num_rows)
    except Exception:  # noqa: BLE001 - profile 形状不对不该让归因整个失败
        return None
    return None if measured is None else float(measured)


def _switch_to_next(candidates: tuple, index: int, *,
                    for_utilisation: bool = False) -> Mutation | None:
    """换到另一个候选。没有更好的就返回 None，不编一个动作出来。

    **换过去必须在「要修的那个量」上确实更好。** 原来这里无条件走
    `index + 1`，而候选的排序不是按不均衡度来的。实测（作业 17248126，同一个
    算法的不同配置）tile(32) 不均衡度 `xm:32:4:64` 是 1.576、`xm:32:16:64`
    是 1.425、`xm:32:32:64` 是 1.336——顺序上的下一个恰好更均衡是运气，不是
    判据。换错了没有任何东西会报错：下一轮照常跑完，只是那个动作和它宣称的
    目的相反。

    `for_utilisation=True` 时按实测 tile 不均衡度挑最小的未访问候选；否则
    保持顺序推进（「规划不出可行硬件」要换的是代价更低的点，不是更均衡的点）。
    """
    if not candidates:
        return None

    if for_utilisation:
        current = _tile_imbalance(candidates[index]) if index < len(candidates) else None
        scored = [
            (value, i) for i, item in enumerate(candidates)
            if i != index and (value := _tile_imbalance(item)) is not None
        ]
        # 没有实测不均衡度就退回顺序推进——猜一个默认值等于凭空造证据。
        if scored:
            best_value, best_index = min(scored)
            if current is not None and best_value >= current:
                return None  # 没有更均衡的候选，换过去只会更差
            nxt = candidates[best_index]
            return Mutation(
                layer=Layer.KERNEL,
                field="candidate_index",
                operation="switch",
                value=best_index,
                expected_effect=(
                    f"PE utilization rises: {nxt.label} has tile imbalance "
                    f"{best_value:.3f} against the current "
                    f"{current:.3f}" if current is not None else
                    f"PE utilization rises: {nxt.label} has tile imbalance "
                    f"{best_value:.3f}"
                ),
                risk=(
                    f"sparsity changes to {nxt.actual_sparsity:.4f} and quality "
                    f"loss to {nxt.quality_loss:+.4f}"
                ),
            )

    if index + 1 >= len(candidates):
        return None
    nxt = candidates[index + 1]
    return Mutation(
        layer=Layer.KERNEL,
        field="candidate_index",
        operation="switch",
        value=index + 1,
        expected_effect=(
            f"measure nothing new: {nxt.label} already has quality_loss "
            f"{nxt.quality_loss:+.4f} at sparsity {nxt.actual_sparsity:.4f}"
        ),
        risk="a less sparse candidate does more work per token",
    )
