"""持久化：缓存、清单、跨 Agent 共享的搜索数据。

    sqlite.py         内容哈希缓存：同样的输入不重复测量
    manifest.py       候选目录、artifact 校验值、工具版本
    experiment_db.py  各 Agent 的搜索记录，含 `cross_layer` 视图

`experiment_db` 存在的理由是 Critic 的**跨层归因**：要判断瓶颈在哪一层，
需要同时看到 Kernel 的候选、Compiler 的调度、µArch 的模板和 Evaluator 的
结果，这些必须落在同一个可 JOIN 的地方，而不是各自留在内存里。
"""

from fast.storage.manifest import RunManifest, now
from fast.storage.experiment_db import ExperimentDB
from fast.storage.sqlite import ExperimentStore

__all__ = ["ExperimentDB", "ExperimentStore", "RunManifest", "now"]
