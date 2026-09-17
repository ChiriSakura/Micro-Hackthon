"""闭环编排：五个 Agent 的顺序、门限传播和缓存控制。

`flow.py` 的职责是「门限失败时后面的阶段不许假装成功」——
上游 `SKIPPED` 或 `FAILED` 时，下游必须显式跳过并在报告里留下原因，
而不是拿默认值继续算下去。
"""

from fast.orchestrator.flow import FiveAgentFlow

__all__ = ["FiveAgentFlow"]
