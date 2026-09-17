"""五个 Agent，以及把 Compiler 和 µArch 耦合起来的协同优化器。

    kernel      精度、稀疏率、分布画像        + quality gate
    compiler    tile、布局、并行度            + schedule gate
    uarch       从已验证模板组合硬件候选      + verified-template gate
    evaluator   把某档保真度归一化成统一契约  + functional gate
    critic      证据绑定的归因与 mutation

Compiler 和 µArch 在概念上是相邻两层，实际上是**双向耦合**的：
硬件约束会反向裁剪调度空间。所以真正的搜索发生在 `cooptimizer.py`，
上面两个类只负责各自的单点产出与门限。

支撑模块：`templates.py`（模板注册表与证据字段）、`codesign.py`
（协同设计空间与一阶代价模型）、`proposers.py`（sweep 对照 / LLM 提议）、
`llm_backends.py`（Vertex AI 调用路径）。
"""

from fast.agents.compiler import CompilerAgent
from fast.agents.critic import CriticAgent
from fast.agents.evaluator import EvaluatorAgent
from fast.agents.kernel import KernelAgent
from fast.agents.uarch import TemplateRecord, UArchAgent

__all__ = [
    "CompilerAgent",
    "CriticAgent",
    "EvaluatorAgent",
    "KernelAgent",
    "TemplateRecord",
    "UArchAgent",
]
