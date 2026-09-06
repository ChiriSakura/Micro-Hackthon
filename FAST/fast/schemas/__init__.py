"""Agent 之间的版本化协议。

所有跨 Agent 的数据都是 `models.py` 里的 frozen dataclass，带
`schema_version`。这样做的两个理由：结果可以内容哈希后缓存
（见 `fast/storage/sqlite.py`），以及协议变更能被显式发现而不是静默错位。
"""

from fast.schemas.models import *  # noqa: F401,F403
