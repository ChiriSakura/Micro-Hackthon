"""µArch Agent：implementer——决定**怎么造出来**，并证明它对。

在流水线里的位置：Kernel → Compiler → **µArch** → Evaluator → Critic。

## 职责边界

Compiler Agent（planner）已经决定了造什么：阵列形状、队列深度、bank 数、
SRAM 容量、除法器级数。这个 Agent **只负责实现那份计划**——检索模板、
组合、仿真、给出证据。

**它不再自己推导任何参数。** 此前这里有

    pe_rows = max(1, min(8, schedule.parallelism))

——阵列形状是规划决策，藏在实现者里，于是「谁决定阵列是 32x4」没有唯一答案。

## 门：从「出身」改成「证据」

提案的原话是这个 Agent「通过组合已验证的 Chisel 模块来保证硬件有效性，
而不是无约束地生成 RTL」。**那句话说的是输出的性质，不是产生它的方式。**

所以门问的不是「这个模板在白名单上吗」，而是「**这个实例有没有仿真证据**」：

  1. 模板存在且通过过验证
  2. 计划里的参数落在模板的 `ParameterRange` 内
  3. 参数落在该模板 `verified_scope` 记录的范围内，否则标注为外推

第 3 条是新加的，而且它让保证**变强**了。注册表里的 scope 长这样：

    topk: "m=64 n=16 bits=16; 8 blocks x 16 lanes against torch.topk"

也就是说今天用 m=32 实例化 TopK，本来就已经是一次没有证据的外推——只是
那个外推被 `verified=True` 这个布尔值盖住了。

「能 elaborate、lint 干净」是绝不能当作通过的那个状态：DynaX 的 6 个缺陷里
有 2 个就是 lint 干净、只有仿真才暴露的。

## 后续：Critic 驱动的 RTL 变异

Critic 归因到这一层时会派发变异向量，那时这个 Agent 进入内循环
（改 RTL → elaborate → 未改动的金标准 TB → 综合），次数封顶。
金标准模型和 testbench 对它**只读**——那是唯一真正危险的作弊路径。
"""

from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass

from fast.agents.codesign import tile_working_set_bytes
from fast.agents.templates import TemplateRegistry, required_col_select_bits
from fast.schemas.models import CompilerSchedule, HardwareCandidate, Status


# 允许的 SRAM 容量档位，和 `cooptimizer.SRAM_CHOICES` 一致。
_SRAM_CHOICES: tuple[int, ...] = (65_536, 131_072, 262_144)


def sram_for_schedule(schedule: CompilerSchedule, data_width: int) -> int:
    """装得下这份调度的最小 SRAM 档位。

    **不能用一个固定的默认值。** 原来写死 262144（256 KB），而
    `CompilerAgent` 发出的 64/64/32 调度只需要驻留 12,288 字节——21 倍。
    SRAM 现在是实测计价的：256 KB 是 1,049,989 um^2，64 KB 是 262,497，
    差 787,492——比整个 RePEArray_S（372,000）还多。

    装不下最大档位时返回最大档位，让 `violations()` 在「working set 超过
    sram_bytes」那一条上明确报错，而不是在这里悄悄放大。
    """
    needed = tile_working_set_bytes(
        schedule.tile_q, schedule.tile_k, schedule.tile_d, data_width
    )
    for choice in _SRAM_CHOICES:
        if choice >= needed:
            return choice
    return _SRAM_CHOICES[-1]



#: 只有综合能测到的那些词。症状里出现它们时，门要打开综合（并在配了
#: OpenSTA 时跑 STA），否则变异的目标是一个门看不见的数。
_PHYSICAL_WORDS = (
    "critical path", "clock", "frequency", "mhz", "ns", "timing", "slack",
    "area", "um^2", "um2", "cells", "power", "mw",
)


def _mentions_physical(text: str) -> bool:
    # 按词边界匹配：`ns` 是「i**ns**tead」的子串，子串匹配会把一个纯功能
    # 症状判成「需要综合」，白等一次综合。
    from fast.agents.rtl_mutation import contains_word

    return any(contains_word(text, word) for word in _PHYSICAL_WORDS)

@dataclass(frozen=True)
class TemplateRecord:
    template_id: str
    digest: str
    manifest_uri: str
    verified: bool


class UArchAgent:
    """Realises one plan out of independently verified Chisel templates."""

    def __init__(self, templates: tuple[TemplateRecord, ...],
                 registry: TemplateRegistry | None = None,
                 *,
                 mutator=None,
                 chisel_root: Path | None = None):
        self.templates = {item.template_id: item for item in templates}
        # 完整注册表带着 `ParameterRange` 和 `verified_scope`；上面那个最小
        # 协议只有 4 个字段，不够判断参数是否落在验证过的范围内。
        self.registry = registry
        # `RtlMutator`：LLM 改一个 Chisel 模块，机械门判它能不能用。
        #
        # **不给就没有 RTL 变异**，而那时「保计划、重新实现」在构造上是空转：
        # `run(plan, template_id)` 是计划的纯函数，同一份计划必然给出同一份
        # 硬件。实测撞到过——三轮的计划和 util 逐字节相同，循环照常跑完。
        self.mutator = mutator
        self.chisel_root = Path(chisel_root) if chisel_root else None
        #: 最近一次变异的完整记录（成功和失败都留）。归因到 µArch 层需要它。
        self.last_mutation = None

    def mutate(self, mutation, *, symptom: str, target: str):
        """按 Critic 的一条 µArch 变异改写一个 Chisel 模块。

        返回 `MutationOutcome`，或者在**做不了**的时候返回一个说明为什么的
        失败记录——「没配 mutator」「指不到有门的模块」「源文件不在」都要
        说出来，因为它们和「改了但没过门」的下一步完全不同。
        """
        from fast.agents.rtl_gate import resolve_module
        from fast.agents.rtl_mutation import MutationOutcome

        def refused(reason: str):
            outcome = MutationOutcome(module="", accepted=False, attempts=0,
                                      source=None, gates=(), reason=reason)
            self.last_mutation = outcome
            return outcome

        if self.mutator is None or self.chisel_root is None:
            return refused("µArch 没有配置 RTL 变异器：重新实现在构造上是空转")

        # **主语在变异里，对比对象在叙述里。** Critic 的那句话经常拿别的模块
        # 作参照——实测「the queue's 2.528 ns critical path, which is slower
        # than the execution array's 2.230 ns」里 "execution array" 比 "queue"
        # 长，只看全文会去改 RePE，而要改的是队列。所以字段和值单独作为
        # `subject` 优先匹配。
        subject = " ".join(str(part) for part in (
            getattr(mutation, "field", ""), getattr(mutation, "value", ""),
        ) if part)
        text = " ".join(str(part) for part in (
            subject, getattr(mutation, "expected_effect", ""), symptom,
        ) if part)
        module, why = resolve_module(text, subject=subject)
        if module is None:
            return refused(why)

        from fast.agents.rtl_gate import MODULES

        source = self.chisel_root / MODULES[module].source
        if not source.is_file():
            return refused(f"{module} 的源文件不在：{source}")

        # **症状是时序/面积时，门必须综合。** 不综合的门只跑 elaborate +
        # 仿真，而关键路径和面积在仿真里根本不存在——模型被要求改进一个门
        # 无法观察的数，改完也说不出有没有用。实测的症状正是这一类
        # （「queue 的 2.528 ns 限制了时钟」）。
        #
        # 综合不放进默认路径是因为它慢；按症状开，而不是一直开。
        wants_synthesis = _mentions_physical(f"{subject} {symptom} {target}")
        gate = getattr(self.mutator, "gate", None)
        previous = getattr(gate, "synthesise", None)
        if wants_synthesis and gate is not None and not previous:
            gate.synthesise = True

        # 目标优先用调用方给的，否则用变异自带的 `expected_effect`——
        # 那本来就是「一个测量能证伪的目标」（prompt 里要求它可证伪）。
        # 两个都没有才说没有：`RtlMutator` 的 prompt 靠它判「改了但没用」。
        try:
            outcome = self.mutator.mutate(
                source, module, symptom=symptom,
                target=(target or getattr(mutation, "expected_effect", "")
                        or "no target given"),
            )
        finally:
            # 只为这一次变异开的综合，用完还回去——留着会让后面每一次
            # 功能类变异都白等一次综合。
            if wants_synthesis and gate is not None and previous is not None:
                gate.synthesise = previous
        self.last_mutation = outcome
        return outcome

    def run(
        self,
        plan: CompilerSchedule,
        *,
        template_id: str,
    ) -> HardwareCandidate:
        """把一份计划实现成带证据的硬件候选。

        计划里已经有全部参数，所以这里没有任何默认值可选——**一个实现者
        不该有「默认阵列形状」这种东西**。
        """
        template = self.templates.get(template_id)
        # 计划被跳过时它的字段是 0，`sram_for_schedule` 会给出最小档位。
        # 失败路径也要报一个具体容量：返回 None 会让下游算面积时炸在离
        # 原因很远的地方。
        resolved_sram = (
            plan.sram_bytes if plan.status is Status.PASSED
            else sram_for_schedule(plan, plan.data_width)
        )

        if template is None or not template.verified:
            return self._rejected(
                plan, template_id, template, resolved_sram,
                Status.FAILED, False,
                "template is absent or has not passed the verification gate",
            )
        if plan.status is not Status.PASSED:
            return self._rejected(
                plan, template_id, template, resolved_sram,
                Status.SKIPPED, True, "compiler plan gate failed",
            )

        # 参数必须落在模板允许的取值内。这是「组合已验证模块」这句话里
        # **可机械检查**的那一半。
        problems = self._admits(plan)
        if problems:
            return self._rejected(
                plan, template_id, template, resolved_sram,
                Status.FAILED, True, "; ".join(problems),
            )

        return HardwareCandidate(
            status=Status.PASSED,
            template_id=template_id,
            template_digest=template.digest,
            verified_template=True,
            # 直接来自计划，不再自己推导。
            pe_rows=plan.num_rows,
            pe_cols=plan.pe_per_row,
            queue_depth=plan.queue_depth,
            sram_bytes=resolved_sram,
            data_width=plan.data_width,
            manifest_uri=template.manifest_uri,
            topk_m=plan.block_m,
            topk_n=plan.kept_per_block,
            reg_width=plan.reg_width,
            col_select_bits=required_col_select_bits(plan.block_m),
        )

    def _admits(self, plan: CompilerSchedule) -> tuple[str, ...]:
        """计划里的参数落在模板允许的范围内吗。"""
        if self.registry is None:
            return ()
        problems: list[str] = []
        array = self.registry.by_id("repe_array")
        if array is not None:
            problems.extend(array.admits(
                numRows=plan.num_rows, peCountPerRow=plan.pe_per_row,
                regWidth=plan.reg_width, bits=plan.data_width,
                colSelectBits=required_col_select_bits(plan.block_m),
            ))
        topk = self.registry.by_id("topk")
        if topk is not None:
            problems.extend(topk.admits(
                m=plan.block_m, n=plan.kept_per_block, bits=plan.data_width
            ))
        return tuple(problems)

    def _rejected(self, plan, template_id, template, sram, status, verified, reason):
        return HardwareCandidate(
            status=status,
            template_id=template_id,
            template_digest="" if template is None else template.digest,
            verified_template=verified,
            pe_rows=0,
            pe_cols=0,
            queue_depth=plan.queue_depth,
            sram_bytes=sram,
            data_width=plan.data_width,
            manifest_uri="" if template is None else template.manifest_uri,
            error=reason,
        )


def elaborate_spec(plan: CompilerSchedule, *, head_dim: int) -> str:
    """把一份计划变成 `Elaborate.scala` 认识的参数串。

    **这是「计划」变成「设计」的那一步。** 在它之前，planner 能说出
    「32x4、queue 2、8 banks」，但 `Elaborate.gen()` 是一个固定的目标枚举，
    `AttentionTile` 被写死在 tileQ=4/tileK=32/headDim=8——系统能**规划**出
    DynaX 尺寸，却造不出它。

    `head_dim` 来自工作负载（模型的 head 维度），不在计划里：它是被跑的那个
    模型的性质，不是设计的自由参数。传错的话造出来的是另一个设计，而它看
    起来完全正常，所以这里要求显式传入而不是给默认值。
    """
    if plan.status is not Status.PASSED:
        raise ValueError(f"cannot elaborate a plan that did not pass: {plan.error}")
    fields = {
        "bits": plan.data_width,
        # PrePEA 的高度 = 同时处理的 query 行数 = 阵列行数。
        "tileQ": plan.num_rows,
        # TopK 的 m。
        "tileK": plan.block_m,
        "headDim": head_dim,
        "keptPerRow": plan.kept_per_block,
        "peCountPerRow": plan.pe_per_row,
        "dividerStages": plan.divider_stages,
    }
    return "PLAN:" + ",".join(f"{k}={v}" for k, v in fields.items())


def passes_for(plan: CompilerSchedule) -> int:
    """一行的保留列要分几趟才能喂完。

    **DynaX-S 是 kept=16 / pe=4 -> 4 趟，而多趟累加从没验证过。**
    `attention_tile.scala` 有 `sched_pass` 输入，但 testbench 的注释写着
    `kKept = 8 // == peCountPerRow，所以 scheduler.passes = 1`。论文尺寸
    会第一次走多趟路径。
    """
    return -(-plan.kept_per_block // max(plan.pe_per_row, 1))
