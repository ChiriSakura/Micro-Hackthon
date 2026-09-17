"""µArch Agent 的 RTL 变异与内循环。

## 为什么允许改 RTL，而不是只组合模板

提案的附录写着这个 Agent「通过组合已验证的 Chisel 模块来保证硬件有效性，
而不是无约束地生成 RTL」。**那句话说的是输出的性质，不是产生它的方式**——
提案的 Fig. 1 里 Arch Agent 内部就画着 `Build chisel -> Verilator sim` 的
内循环，PPA 只接收过了那个循环的东西。

而纯组合拿不到这一轮最大的几个收益：

    改动                            效果                   组合能做到吗
    线性 reduce 链 -> 相对计数器     19.0 ns -> 2.27 ns     否，结构重写
    Queue(pipe = true)              吞吐 x2                否，参数不在接口上
    out_valid 打一拍                修正错误数据            否
    空行发空趟                      topk 0.394 -> 0.609    否

## 门：从「出身」改成「证据」

不问「这个模板在白名单上吗」，问「**这个实例有没有仿真证据**」。判据是

> **允许改实现，不允许改契约。**

金标准模型定义契约。RTL 可以随便重写，只要那份**没有改动的**金标准测试仍然
通过。这条可机械检查，而且这一轮验证过它管用：四个改动里有三个产出了逐位
相同的结果（BlockScheduler 重写后 20/20 个测量点不变，KeyFeeder 修 out_valid
后周期数完全不变）——那正是「保契约」的签名。

## 唯一真正危险的失败模式

**Agent 改金标准让自己的 RTL 通过。** 内循环让这个风险变高，因为失败会反复
回喂，而「让测试通过」是模型最自然会走的捷径。

防法是文件级的：金标准和 testbench 只读，每次门检查前后比对哈希，变了就直接
判失败。仓库里已有这条原则的先例——`hardware/README.md` 的「PrePEArray：参照
必须是软件，不能是镜像」。

## 通过门 != 有效

XOR 散列 bank 映射通过了全部的门（elaborate 过、32 个仿真点全 PASSED、面积只
多 192 um^2），实测却是负收益（nm 从 1.19x 恶化到 2.01x）。所以症状检查在内
循环**外面**，由 Critic 派发变异时一起给出可检验的目标。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
from typing import Protocol


# 内循环允许的尝试次数。次数封顶是唯一的停止准则——「无进展」「退化」这类
# 判据要先有可比的失败签名，而那要等真实运行数据积累出来。
DEFAULT_ATTEMPTS = 3

#: 门自己坏了（不是被测的 RTL 坏了）的诊断前缀。
#:
#: 定义在这里而不是 `rtl_gate` 里，是因为导入方向是 gate -> mutation
#: （gate 从这里拿 `GateResult`），反过来会成环。
INFRA_PREFIX = "[gate-infrastructure] "



def contains_word(haystack: str, needle: str) -> bool:
    """`needle` 是否作为**独立的词**出现在 `haystack` 里。

    这个会话里同一个子串错误犯了三次：`pe` 命中「pi**pe**line」和
    「**pe**riod」，把一条关于工作队列的变异解析成「改 RePE」；`ns` 命中
    「i**ns**tead」，把一个纯功能症状判成「需要综合」。短的技术词几乎必然是
    别的词的子串——所以匹配一律走这里，不要再写 `x in text`。

    两侧用「非字母数字」而不是 `\b`：`um^2` 这种带符号的单位在 `\b` 下
    行为不直观。
    """
    if not needle:
        return False
    return re.search(
        rf"(?<![a-z0-9]){re.escape(needle.lower())}(?![a-z0-9])",
        " ".join(str(haystack or "").lower().split()),
    ) is not None

@dataclass(frozen=True)
class GateResult:
    """一次门检查的结果。

    `diagnostics` 是回喂给模型的东西，**它的质量决定内循环能不能收敛**。
    这一轮我修四个 RTL 问题，每一次都是失败消息直接告诉我去哪里看：

        elaborate  "key_feeder.scala:160: ambiguous reference to overloaded
                    definition"                          <- 带行号
        数据失配    "第 1 组槽 4：列 45 取到 0x00FF，应为 0x013E"
                                                         <- 我一眼看出整组晚一拍
        判据失配    "深度 0 的利用率 0.3789 偏离 1/imbalance=0.3053 达 24.1%
                    （深度 0 应当是严格锁步；对不上说明屏障没起作用）"
                                                         <- 消息里带着假设
        综合时序    "时序不可信（INV_X1 单级 345.5ns，未插缓冲）"
        综合资源    "yosys produced no area (rc=-9)"      <- 只知道被 OOM 杀了

    第三类最有用：它不只说「不对」，还说了「**应当**是什么，对不上说明
    什么坏了」。只输出 FAILED 的 testbench 会让内循环退化成盲目重试。
    """

    stage: str          # elaborate / simulate / synthesize
    passed: bool
    diagnostics: str
    metrics: dict[str, float] = field(default_factory=dict)


class RtlGate(Protocol):
    """跑一个模块的门。实现可以在本地跑，也可以投 slurm。"""

    def check(self, module_path: Path, target: str) -> tuple[GateResult, ...]: ...


@dataclass(frozen=True)
class MutationOutcome:
    """一次变异尝试的完整记录。

    失败的尝试**也要留下**：哪个模块在第几次通过的、失败的原因是什么，
    正是「归因到 µArch 层」需要的证据。丢掉失败记录，Critic 下一轮就只能
    重新猜。
    """

    module: str
    accepted: bool
    attempts: int
    source: str | None
    gates: tuple[GateResult, ...]
    reason: str

    @property
    def diagnostics(self) -> str:
        return "\n".join(f"[{g.stage}] {g.diagnostics}" for g in self.gates if not g.passed)

    @property
    def metrics(self) -> dict[str, float]:
        """**通过的门量到了什么。**

        原来只留失败门的诊断，于是一次 `accepted=True` 的变异在报告里什么
        数字都没有——「过了门」和「改进了目标」是两回事，而后者才是变异的
        意义。实测就撞到了：三次变异全部 accepted，而关键路径只从 2.760 ns
        动到 2.736 ns（0.9%），目标是 2.230 ns（要 19%）。不记下来的话，
        报告读起来像成功。
        """
        out: dict[str, float] = {}
        for gate in self.gates:
            out.update(gate.metrics or {})
        return out


MUTATION_PROMPT = """You are the microarchitecture agent in a hardware/software \
co-design loop. You rewrite one Chisel module to fix one measured symptom.

## The symptom the critic attributed to this module

{symptom}

## The target that decides whether your change worked

{target}

This is checked AFTER the correctness gates, by measurement. A change that
passes every gate but does not move this number is rejected. (A previous
mutation — hashing the bank index to break stride aliasing — passed every gate
and was a performance regression.)

## What this module must guarantee, no matter how you rewrite it

{contract}

A rewrite that breaks any of these is rejected however much it improves the
target. These are the module's design contract, not the test's implementation.

## The rules

1. Rewrite ONLY the module below. Return the complete file, not a patch.
2. The golden model and the testbench are READ-ONLY and are not shown to you as
   editable text. Your rewrite must pass the EXISTING test unchanged.
3. Do not change the module's functional contract: same ports, same numerics,
   same cycle-level protocol. You may change the implementation freely —
   restructure logic, add or remove pipeline registers on internal paths,
   change reduction trees, change encodings of internal state.
4. Chisel is pinned to 3.6 (`edu.berkeley.cs`). `chisel3.experimental.FixedPoint`
   exists; Chisel 5 APIs do not.

## Things that have actually gone wrong in this codebase

- `Seq.reduce` is left-associative: it builds a LINEAR chain, not a tree. A
  32-element min-reduce over 16-bit values synthesised to 19.0 ns.
- `Queue(...)` defaults to `pipe = false`, so a depth-1 queue cannot enqueue in
  the cycle it dequeues: throughput halves.
- A register written in the same cycle a `done` flag is computed is not visible
  until the next cycle. Driving `valid` from that flag returns stale data.

## Attempt {attempt} of {attempts}

{history}

If a previous attempt is shown above, read what YOU changed and why the gate
rejected it before writing anything. Repeating the same edit wastes the budget.

## The module

```scala
{source}
```

Return ONLY the rewritten Scala file. No prose, no markdown fence, no
explanation."""


class RtlMutator:
    """LLM 改 RTL，机械门判它能不能用。"""

    def __init__(self, llm, gate: RtlGate, *, model_name: str = "llm",
                 attempts: int = DEFAULT_ATTEMPTS,
                 protected: tuple[Path, ...] = ()):
        self.llm = llm
        self.gate = gate
        self.name = f"llm-rtl:{model_name}"
        self.attempts = attempts
        # 金标准与 testbench 的路径。每次门检查前后比对哈希。
        self.protected = protected

    def mutate(
        self,
        module_path: Path,
        target_name: str,
        *,
        symptom: str,
        target: str,
    ) -> MutationOutcome:
        """改一个模块直到它过门，或者次数用完。

        次数用完时**回退到未变异的版本**并把整个尝试记录留下。流水线继续跑
        ——变异失败不该中断整条链路，和 LLM proposer 回落到确定性版本是同
        一个模式。
        """
        from fast.agents.rtl_gate import MODULES

        contract = getattr(MODULES.get(target_name), "contract", "")
        original = module_path.read_text(encoding="utf-8")
        before = self._protected_digest()
        history: list[str] = []
        gates: tuple[GateResult, ...] = ()

        for attempt in range(1, self.attempts + 1):
            source = self._ask(original, symptom, target, attempt, history, contract)
            if source is None:
                history.append(f"attempt {attempt}: the model returned nothing usable")
                continue

            module_path.write_text(source, encoding="utf-8")
            gates = self.gate.check(module_path, target_name)

            after = self._protected_digest()
            if after != before:
                # 改了金标准就直接判死，不给重试机会：这是唯一一条会让整个
                # 证据体系失效的路径，容忍一次就等于容忍。
                module_path.write_text(original, encoding="utf-8")
                return MutationOutcome(
                    module=target_name, accepted=False, attempts=attempt,
                    source=None, gates=gates,
                    reason="the mutation touched a read-only golden model or testbench",
                )

            failed = [g for g in gates if not g.passed]
            # **门自己坏了就立刻停。** 环境问题（缺依赖、缺工作量、容器不在）
            # 重试多少次都是同一个错，而每次重试都要花一次真实的 LLM 调用——
            # 实测浪费过 6 次：门用的解释器没有 torch，`gen_golden.py` 每次都
            # 以同一个 ImportError 失败，模型被要求「修一个它没弄坏的东西」。
            infra = [g for g in failed if INFRA_PREFIX in (g.diagnostics or "")]
            if infra:
                module_path.write_text(original, encoding="utf-8")
                return MutationOutcome(
                    module=target_name, accepted=False, attempts=attempt,
                    source=None, gates=gates,
                    reason=(
                        "门自己跑不起来，不是变异的问题——重试不会有帮助："
                        f"{infra[0].diagnostics.strip()[:300]}"
                    ),
                )
            if not failed:
                return MutationOutcome(
                    module=target_name, accepted=True, attempts=attempt,
                    source=source, gates=gates, reason="all gates passed",
                )
            # **把模型自己改了什么也回给它。** 原来只回诊断，模型看不到自己
            # 上一次写了什么，于是第 2、3 次很可能重复同一个错误——实测三次
            # 改写 BlockScheduler 都以「丢工作」告终。
            #
            # 全部失败阶段都回，不只是第一个：elaborate 过了而仿真挂了，和
            # 两级都挂，下一步完全不同。
            history.append("\n".join([
                f"### attempt {attempt} was REJECTED",
                _diff_summary(original, source),
                *(f"[{g.stage}] {g.diagnostics}" for g in failed),
            ]))
            module_path.write_text(original, encoding="utf-8")

        return MutationOutcome(
            module=target_name, accepted=False, attempts=self.attempts,
            source=None, gates=gates,
            reason=f"no mutation passed the gates in {self.attempts} attempts",
        )

    # -- internals ---------------------------------------------------------

    def _ask(self, source, symptom, target, attempt, history, contract="") -> str | None:
        prompt = MUTATION_PROMPT.format(
            symptom=symptom, target=target,
            contract=contract or "(no contract recorded for this module)",
            attempt=attempt, attempts=self.attempts,
            history="\n\n".join(history) if history else "(first attempt)",
            source=source,
        )
        try:
            reply = self.llm.prompt(prompt)
        except Exception:
            return None
        if not getattr(reply, "success", True):
            return None
        text = reply.result if hasattr(reply, "result") else str(reply)
        return _strip_fence(text) or None

    def _protected_digest(self) -> str:
        """金标准与 testbench 的内容哈希。

        比对的是**内容**不是修改时间：时间戳可以被写回原值，内容不能。
        """
        digest = hashlib.sha256()
        for path in sorted(self.protected):
            if path.is_dir():
                for item in sorted(path.rglob("*")):
                    if item.is_file():
                        digest.update(item.read_bytes())
            elif path.is_file():
                digest.update(path.read_bytes())
        return digest.hexdigest()



def _diff_summary(original: str, rewritten: str, *, context: int = 0,
                  max_lines: int = 60) -> str:
    """上一次尝试改了哪几行。

    回诊断而不回改动，等于让模型对着一个它看不见的东西调试。整份文件太长
    （会挤掉源码本身），所以只回 unified diff，并截断。
    """
    import difflib

    diff = list(difflib.unified_diff(
        original.splitlines(), rewritten.splitlines(),
        fromfile="before", tofile="after", n=context, lineterm="",
    ))
    if not diff:
        return "you returned the file unchanged"
    if len(diff) > max_lines:
        diff = diff[:max_lines] + [f"... ({len(diff) - max_lines} more diff lines)"]
    return "what you changed:\n" + "\n".join(diff)

def _strip_fence(text: str) -> str:
    """去掉围栏。要求严格（prompt 说 no fence），解析宽容。"""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped.strip()
