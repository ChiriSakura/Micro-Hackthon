"""哪个 Agent 用哪个模型，以及为什么。

## 默认从 flash 换成 pro

原来所有地方都默认 `gemini-2.5-flash`——那是**最快最便宜**的一档，不是最强的。
提案的预算表里 Gemini API 是 $700 / 约 70M tokens，是单项最大的一笔；用 flash
等于把预算留着不花却拿不到质量。

但也不该无脑全上 pro：三个 Agent 的任务难度差好几个数量级。

## 逐 Agent 的选择

    Agent          任务                                   模型      理由
    kernel         从枚举表里选标签 + 引用数字说理由        pro       多维取舍推理
    compiler       提议调度与硬件参数                      pro       同上，且空间更大
    uarch-compose  选模板 + 定参数                        flash     基本是查表
    uarch-mutate   **写 Chisel RTL**                      pro       见下
    critic         归因                                   pro       跨轮对比推理

`uarch-mutate` 没有商量余地。这一轮四个 RTL 修改里，「线性 reduce 链改成相对
计数器」要同时理解三件事：Chisel 的 `reduce` 是左结合、它综合出来是 numRows 级
比较器链、以及 19 ns 正比于行数是那个链的签名。这不是一个便宜模型能做的推理。

`uarch-compose` 用 flash 是因为它真的只是「在注册表里挑一个、把参数填进
ParameterRange」——校验由代码做，模型只负责选。

## 温度

提议类任务用 0.2：要的是在证据上推理，不是多样性——多样性由 proposer 的
探索逻辑提供，不该由采样噪声提供。写 RTL 用 0.0：同一个症状应该得到同一个
修复，否则内循环的「连续两次同类失败」这种判据没有意义。
"""

from __future__ import annotations

from dataclasses import dataclass


# 最强的那一档。改这里一个常量，所有默认值跟着变——散在各个 CLI 的默认参数里
# 是上一版的做法，改一次要找五个地方。
STRONGEST = "gemini-2.5-pro"
CHEAP = "gemini-2.5-flash"


@dataclass(frozen=True)
class ModelChoice:
    """一个 Agent 角色的模型配置。"""

    role: str
    model: str
    temperature: float
    why: str


ROLES: dict[str, ModelChoice] = {
    "kernel": ModelChoice(
        "kernel", STRONGEST, 0.2,
        "在精度/稀疏度/硬件代价三者之间取舍，要引用测量值说理由",
    ),
    "compiler": ModelChoice(
        "compiler", STRONGEST, 0.2,
        "在软硬件耦合的空间里提议设计点，维度比 kernel 更多",
    ),
    "uarch-compose": ModelChoice(
        "uarch-compose", CHEAP, 0.2,
        "在注册表里选模板并填参数；合法性由代码校验，模型只负责选",
    ),
    "uarch-mutate": ModelChoice(
        "uarch-mutate", STRONGEST, 0.0,
        "写 Chisel RTL。温度 0：同一个症状要得到同一个修复，否则内循环的"
        "「连续两次同类失败」判不出来",
    ),
    "critic": ModelChoice(
        "critic", STRONGEST, 0.2,
        "跨轮对比归因，要把一个症状对应到某一层",
    ),
}


def model_for(role: str) -> ModelChoice:
    """某个角色该用哪个模型。未知角色按最强的来。

    未知角色不该悄悄退到便宜的那档——一个没人想过的新角色，猜错方向的代价
    是产出质量，而不是账单。
    """
    return ROLES.get(role, ModelChoice(role, STRONGEST, 0.2, "unknown role: defaults to the strongest model"))
