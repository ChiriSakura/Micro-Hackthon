"""LLM 版 Critic：归因到层，并给出**可检验的**变异目标。

## 契约不变，实现可换

规则版 `CriticAgent` 的契约不是「结论对不对」，而是**每个结论都必须指向产生
它的那条证据**——`Critique.evidence` 里放的是字段路径而不是自然语言理由。
这个类产出同一个 schema，所以下游（尤其是分层重入）完全不用改。

## 为什么归因值得上最强的模型

归因是**跨轮对比推理**：这一轮和上一轮变了什么、哪个数动了、动的方向对不对。
规则版只能做单点的 if 链——它判不出「三个候选都撞同一个瓶颈，所以不是算法层」
这种需要对照的结论。

## 输出必须带可检验的目标

派发变异时说「让它更快」是没用的：内循环没法判断自己成功了没有。
`Mutation.expected_effect` 要装的是「关键路径降到 2.23 ns 以下」这种能被
测量证伪的目标。这一轮有过一个反例——XOR 散列通过了全部的门却是负收益，
如果没有可检验目标，它会被当成成功。

## 幻觉的代价

层名和字段名都对着枚举校验，越界的归因被拒并记进 `rejected`，然后回落到
规则版。**一次幻觉的代价因此是零，而且是可见的。**
"""

from __future__ import annotations

import json
import re

from fast.agents.critic import CriticAgent
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


CRITIC_PROMPT = """You are the Critic in a hardware/software co-design loop for \
dynamic sparse attention. You read one round's results and decide WHICH LAYER the \
bottleneck belongs to, then dispatch a mutation for that layer.

**The algorithm is fixed: {algorithm}.** It was given to the loop, not chosen by
it. Every candidate below is a CONFIGURATION of {algorithm}. A "kernel" mutation
therefore means "use a different {algorithm} configuration" -- never "use a
different algorithm".

## What is being optimised, and what is merely allowed

This is a CONSTRAINED optimisation:

    minimise   (latency L(x), energy E(x)) as a Pareto set
    subject to accuracy loss <= {epsilon}
               area          <= {max_area}
               power         <= {max_power}
               clock         >= {min_mhz}

Energy is joules per SAME completed workload: E = power_mW * 1e-3 * latency_s.
Energy efficiency is completed tasks/J = 1/E, not executed sparse MACs/J.
Preserve a slower design when it saves energy: neither trade-off dominates the
other. Area and accuracy are constraints, not Pareto axes. Do not scalarise to
EDP. Energy currently has PARTIAL model coverage; never call it measured
whole-design energy, even when RTL functionality passed.

**The accuracy budget is a GATE, not a score.** Every configuration below has
already passed it. Inside the budget, a loss of +0.0271 and a loss of +0.0008
are EQUALLY ACCEPTABLE -- "lower loss" is NOT "better". Ranking candidates by
quality_loss means optimising a constraint instead of the objective.

This has actually happened: the loop switched away from a configuration with
loss +0.0271 (well inside the 0.05 budget) toward one with +0.0008, calling the
first "unacceptable". The one it abandoned was 2x FASTER -- 29,522 ns against
61,606 ns, at the same hardware and slightly lower power -- because it was
sparser, so the array had less work to do. It dominated the replacement on both
objectives. That round threw away the best design in the whole run.

**Sparsity is what buys latency.** A sparser configuration does less work, so
prefer it whenever it still clears the accuracy gate. Only reach for a less
sparse one when the sparse one FAILS a constraint, or when a measurement shows
it hurts the hardware (for example an imbalance that starves the array).

## Why the layer matters

The next round re-enters at the layer you name, and ONLY at that layer:

  kernel         swap to another already-measured {algorithm} configuration, then replan
  compiler       keep the candidate, replan under a new constraint
  uarch          keep the candidate AND the plan, rewrite RTL and re-simulate
  planner_model  the cost model is wrong; recalibrate it, then replan
  evaluator      the plan and hardware stand; escalate the fidelity

Naming the wrong layer wastes a round AND destroys the comparison: if two layers
change at once, the next round cannot attribute anything.

## This round

current {algorithm} configuration: {method}
  sparsity {sparsity:.4f} (higher = less work = lower latency)
  quality_loss {loss:+.4f} (gate: <= {epsilon}; inside the gate this is not a score)
other measured {algorithm} configurations: {menu}

plan: {plan}
predicted: cycles {p_cycles}, area {p_area}, power {p_power}, clock {p_clock}

hardware: {hardware}
evaluation ({fidelity}): {measured}

## Earlier rounds

{history}

## What is measured, and what is not

These are Nangate45 measurements. Do not re-derive them.

  execution array critical path   2.230 ns (448 MHz) — the ceiling
  queue depth 0/2/4/8             2.273 / 2.528 / 2.760 / 3.140 ns
  queue utilisation (xm)          0.708 / 0.832 / 0.864 / 0.867 — saturates
  divider 0/4/8/12 stages         14.780 / 3.269 / 1.980 / 1.546 ns
  bank conflict at 8 banks        xm 2.14x, nm 1.19x, topk 1.79x, sanger 1.28x
                                  (这是**跨算法**的对照。算法已经固定，所以这一行
                                   只说明数量级，不能用来在候选之间做选择——候选
                                   都是同一个算法的不同配置。)
  SRAM                            about 4.0-5.4 um^2 per byte

**Which number drives which metric.** Citing a real measurement that does not
feed the metric you are explaining is still a wrong attribution:

  pe_utilization   <- tile load imbalance and queue_depth ONLY.
                      Measured on block_scheduler.scala. Bank conflicts do
                      NOT enter it. Each candidate's measured tile imbalance
                      is listed with it below; a switch aimed at utilization
                      MUST go to a candidate with a LOWER one.
  cycles / DRAM    <- sparsity, bank conflict rate, queue utilisation.
  area / power     <- num_rows, pe_per_row, divider_stages, sram_bytes.
  clock period     <- queue_depth and divider_stages (the two tables above).

Fidelities below L2 never run RTL: their functional_passed is "not checked",
NOT "failed". Do not attribute a functional failure that was never tested.

## Reply

ONLY a JSON object, no prose, no fence:

  {{"attribution": "<one of: kernel, compiler, uarch, evaluator, planner_model>",
    "decision": "<one of: continue, revert, stop>",
    "summary": "<one sentence naming the number that drove this>",
    "evidence": ["<field path, e.g. evaluation.pe_utilization>", ...],
    "mutations": [
      {{"layer": "<same set as attribution>",
        "field": "<what to change; to switch the kernel candidate use exactly
                   \"candidate\" and put its label in value>",
        "operation": "<increase|decrease|switch|recalibrate|rewrite>",
        "value": <number or string>,
        "expected_effect": "<a TARGET a measurement can falsify, e.g. 'critical path below 2.230 ns'>",
        "risk": "<what this trade costs>"}}
    ]}}

Every evidence entry must be a field path from the data above, not prose."""



def _imbalance(item, num_rows: int = 32) -> str:
    """一个候选实测的 tile 内不均衡度，没测到就说没测到。

    返回 "not measured" 而不是一个中性默认值：一个看起来像测量的占位数会
    让模型据它推理，而这正是这里要防的那种错。
    """
    profile = getattr(item, "profile", None)
    if profile is None:
        return "not measured"
    try:
        # **实测值，不接受回退。** 全局 `load_imbalance` 顶替会把一个放大
        # 约 1.9-2.5 倍、而且排序不同的量当成 tile 不均衡度喂给模型——
        # 模型据它做的比较全是错的，而且看不出来。
        measured = profile.tile_imbalance_measured(num_rows)
    except Exception:  # noqa: BLE001 - profile 形状不对时不该让归因整个失败
        return "not measured"
    return "not measured" if measured is None else f"{measured:.3f}"

_LAYERS = {layer.value: layer for layer in Layer}
_DECISIONS = {decision.value: decision for decision in Decision}


class LLMCriticAgent:
    """LLM 归因，schema 和门与规则版完全一致。"""

    def __init__(self, llm, *, model_name: str = "llm", fallback: CriticAgent | None = None,
                 specs=None):
        self.llm = llm
        self.name = f"llm-critic:{model_name}"
        self.fallback = fallback or CriticAgent()
        self.rejected: list[str] = []
        # 约束（面积/功耗/频率预算）。写进 prompt 是为了让「什么是目标、什么
        # 只是可行域」在模型眼里是分开的——不给就报 "not given"，**不要编一个
        # 默认值**：一个模型以为存在的预算会让它优化一个没人要求的东西。
        self.specs = specs

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
        history: tuple = (),
    ) -> Critique:
        # 硬门先走规则版：模板没通过验证、kernel 没过精度门这类判断是**规则**
        # 不是判断力，交给模型只会引入不确定性。模型只在「有数据可读」的
        # 情况下才被问。
        if kernel.status is not Status.PASSED or hardware is None or not hardware.verified_template:
            return self.fallback.run(spec, kernel, compiler, hardware, evaluation,
                                     candidates=candidates, candidate_index=candidate_index)

        prompt = self._prompt(spec, kernel, compiler, hardware, evaluation,
                              candidates, candidate_index, history)
        try:
            reply = self.llm.prompt(prompt)
            text = reply.result if hasattr(reply, "result") else str(reply)
            success = getattr(reply, "success", True)
        except Exception as exc:
            self.rejected.append(f"llm call failed: {type(exc).__name__}: {exc}")
            return self.fallback.run(spec, kernel, compiler, hardware, evaluation,
                                     candidates=candidates, candidate_index=candidate_index)
        if not success:
            self.rejected.append(f"llm returned failure: {getattr(reply, 'stderr', '')[:200]}")
            return self.fallback.run(spec, kernel, compiler, hardware, evaluation,
                                     candidates=candidates, candidate_index=candidate_index)

        critique = self._parse(text)
        if critique is None:
            return self.fallback.run(spec, kernel, compiler, hardware, evaluation,
                                     candidates=candidates, candidate_index=candidate_index)
        return critique

    def review_search(self, context) -> Critique:
        """Use actual rediscovery evidence without the legacy calibration menu."""
        from fast.agents.rediscovery_critic import SEARCH_PROMPT, validate_review
        from fast.schemas.models import digest_json
        import time

        if not hasattr(self, "search_calls"):
            self.search_calls = []
        prompt = SEARCH_PROMPT + json.dumps(context, allow_nan=False)
        started = time.monotonic()
        call = {"context_sha256": digest_json(context), "successful": False}
        try:
            reply = self.llm.prompt(prompt)
            if not getattr(reply, "success", True):
                raise ValueError(f"LLM failure: {getattr(reply, 'stderr', '')[:200]}")
            text = reply.result if hasattr(reply, "result") else str(reply)
            call["reply"] = text
            critique = self._parse(text)
            if critique is None:
                raise ValueError("invalid Critique JSON")
            validate_review(critique, context)
            call["successful"] = True
            return critique
        except Exception as exc:
            call["fallback_reason"] = f"{type(exc).__name__}: {exc}"
            self.rejected.append(call["fallback_reason"])
            return self.fallback.review_search(context)
        finally:
            call["wall_seconds"] = time.monotonic() - started
            self.search_calls.append(call)

    # -- prompt ------------------------------------------------------------

    def _prompt(self, spec, kernel, compiler, hardware, evaluation,
                candidates, index, history) -> str:
        # **每个候选都带上它实测的 tile 不均衡度。**
        #
        # 不带的后果这一轮真撞到了：模型看到「xm 的 bank 冲突 2.14x 最高」就
        # 建议换候选——它引的是真实测量，只是那个量**不驱动**
        # pe_utilization。给了正确的量，「换过去会不会更好」才是可判定的。
        #
        # 给的必须是**实测值**：`tile_imbalance_for` 在字段缺失时会退回全局
        # `load_imbalance`，那个数放大约 1.9-2.5 倍且排序不同。所以这里走
        # `tile_imbalance_measured`，没测到就明说没测到。
        menu = ", ".join(
            f"#{i} {item.label} (sparsity {item.actual_sparsity:.3f}, "
            f"loss {item.quality_loss:+.4f} [inside gate], "
            f"tile imbalance {_imbalance(item)})"
            for i, item in enumerate(candidates) if i != index
        ) or "none left"
        specs = self.specs
        return CRITIC_PROMPT.format(
            algorithm=str(kernel.sparse_method).split(":")[0],
            epsilon=f"{spec.epsilon:.4f}",
            max_area=f"{specs.max_area_um2:,.0f} um^2" if specs else "not given",
            max_power=(f"{specs.max_power_mw:,.0f} mW"
                       if specs and specs.max_power_mw else "not given"),
            min_mhz=f"{specs.target_mhz:,.0f} MHz" if specs else "not given",
            method=kernel.sparse_method,
            sparsity=kernel.actual_sparsity,
            loss=kernel.quality_loss,
            menu=menu,
            plan=_plan_line(compiler),
            p_cycles=_num(compiler.predicted_cycles if compiler else None),
            p_area=_num(compiler.predicted_area_um2 if compiler else None),
            p_power=_num(compiler.predicted_power_mw if compiler else None),
            p_clock=_num(compiler.predicted_clock_ns if compiler else None, "{:.3f}"),
            hardware=(
                f"{hardware.pe_rows}x{hardware.pe_cols} queue {hardware.queue_depth} "
                f"sram {hardware.sram_bytes} template {hardware.template_id}"
            ),
            fidelity=evaluation.fidelity if evaluation else "none",
            measured=_measured_line(evaluation),
            history=_history_lines(history),
        )

    # -- parsing -----------------------------------------------------------

    def _parse(self, text: str) -> Critique | None:
        payload = _extract_json_object(text)
        if payload is None:
            self.rejected.append(f"reply was not a JSON object: {text.strip()[:160]}")
            return None

        layer = _LAYERS.get(str(payload.get("attribution", "")).strip().lower())
        if layer is None:
            self.rejected.append(
                f"attribution {payload.get('attribution')!r} is not one of {sorted(_LAYERS)}"
            )
            return None
        decision = _DECISIONS.get(str(payload.get("decision", "")).strip().lower())
        if decision is None:
            self.rejected.append(
                f"decision {payload.get('decision')!r} is not one of {sorted(_DECISIONS)}"
            )
            return None

        # schema 强制「每个结论必须至少引用一条证据」——归因的可审计性来自
        # 结构，不来自模型。模型没给证据时**拒绝**，不要让它在构造时抛异常：
        # 一次幻觉的代价应该是「回落到规则版」，不是「整轮崩掉」。
        evidence = tuple(str(item) for item in (payload.get("evidence") or ()) if str(item).strip())
        if not evidence:
            self.rejected.append("critique cited no evidence field")
            return None

        mutations = []
        for entry in payload.get("mutations") or ():
            mutation = self._as_mutation(entry)
            if mutation is not None:
                mutations.append(mutation)

        return Critique(
            status=Status.PASSED,
            attribution=layer,
            decision=decision,
            summary=str(payload.get("summary", ""))[:400],
            evidence=evidence[:8],
            mutations=tuple(mutations),
        )

    def _as_mutation(self, entry) -> Mutation | None:
        if not isinstance(entry, dict):
            self.rejected.append(f"mutation is not an object: {str(entry)[:120]}")
            return None
        layer = _LAYERS.get(str(entry.get("layer", "")).strip().lower())
        if layer is None:
            self.rejected.append(f"mutation layer {entry.get('layer')!r} is unknown")
            return None
        effect = str(entry.get("expected_effect", "")).strip()
        if not effect:
            # 没有可检验目标的变异不能派发：内循环判不出自己成功了没有，
            # 而「通过门 != 有效」这一课是 XOR 散列教的。
            self.rejected.append(f"mutation on {entry.get('field')!r} has no expected_effect")
            return None
        return Mutation(
            layer=layer,
            field=str(entry.get("field", ""))[:64],
            operation=str(entry.get("operation", ""))[:32],
            value=entry.get("value", 0),
            expected_effect=effect[:300],
            risk=str(entry.get("risk", ""))[:300],
        )


# -- formatting helpers ----------------------------------------------------

def _num(value, fmt: str = "{:,.0f}") -> str:
    return "not predicted" if value is None else fmt.format(value)


def _plan_line(plan: CompilerSchedule | None) -> str:
    if plan is None or plan.status is not Status.PASSED:
        return f"no plan ({plan.error if plan else 'missing'})"
    return (
        f"{plan.num_rows}x{plan.pe_per_row} regWidth {plan.reg_width} "
        f"queue {plan.queue_depth} divider {plan.divider_stages} "
        f"banks {plan.bank_count} sram {plan.sram_bytes} "
        f"tiles {plan.tile_q}/{plan.tile_k}/{plan.tile_d} layout {plan.data_layout}"
    )


def _measured_line(evaluation: EvaluationResult | None) -> str:
    if evaluation is None:
        return "no evaluation"
    parts = [f"functional_passed={evaluation.functional_passed}"]
    for name in ("cycles", "pe_utilization", "area", "power", "edp"):
        value = getattr(evaluation, name, None)
        if value is not None:
            parts.append(f"{name}={value:,.4g}")
    return ", ".join(parts)


def _history_lines(history: tuple) -> str:
    """走过的每一轮：**计划、实测、归因**，按轮排。

    原来每行只有归因和一句话，没有任何数字——于是模型看不到「改了那一层
    之后指标怎么动」，而那正是跨轮归因唯一的依据。这份轨迹的持久副本在共享板
    上（`ExperimentDB.trajectory()`），提案 Table II 里 Orchestrator 的输出
    写的就是 "Prompts, shared state"。

    **没跑过 RTL 的轮次要标出来。** 那些轮次的利用率是 planner 自己代价模型
    算的（证据字段自己写着 NOT INDEPENDENT），拿它和验证过的轮次并排比较，
    等于让规划者给自己打分。实测有一次 7 轮里 4 轮是这样。
    """
    if not history:
        return "  (this is the first round)"
    rows = []
    for index, report in enumerate(history):
        critique = report.critique
        plan, evaluation = report.compiler, report.evaluation
        shape = (
            f"{plan.num_rows}x{plan.pe_per_row} q={plan.queue_depth}"
            if plan is not None else "no plan"
        )
        verified = (getattr(evaluation, "fidelity", "") or "").startswith("L2")
        util = getattr(evaluation, "pe_utilization", None)
        measured = (
            f"util {util:.3f}" if util is not None else "util not measured"
        )
        area = getattr(plan, "predicted_area_um2", None)
        if area:
            measured += f", predicted area {area:,.0f} um^2"
        flag = "" if verified else "  [NOT RTL-VERIFIED: these numbers come from the planner's own cost model]"
        rows.append(
            f"  round {index}: {report.kernel.sparse_method}  {shape}  {measured}{flag}\n"
            f"      -> {critique.attribution.value} / {critique.decision.value}: "
            f"{critique.summary[:110]}"
        )
    return "\n".join(rows)


def _extract_json_object(text: str):
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
