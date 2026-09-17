"""Runtime configuration loading for DynaX model implementations.

★ FAST 改动：加了 `_OVERRIDE` 上下文管理器和 `_FILE_CACHE`。
原实现每次调用都读盘，且只能从文件取配置——这让「一次加载模型、
在同一进程内扫多种稀疏方法」无法实现，而那正是 run_eval_matrix.py
保证所有方法看到相同权重与相同 token 窗口的前提。
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Any, Iterator


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "config.json"

_OVERRIDE: dict[str, Any] | None = None
_FILE_CACHE: dict[tuple[str, int, int], dict[str, Any]] = {}


def load_dynax_config() -> dict[str, object]:
    """Load the per-run config, falling back to the repository default.

    The config is consulted once per attention call, so file contents are cached
    on ``(path, mtime, size)``. An explicit in-process override always wins,
    which lets one driver sweep several methods without rewriting files.
    """
    if _OVERRIDE is not None:
        return _OVERRIDE
    config_path = Path(os.environ.get("DYNAX_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    stat = config_path.stat()
    key = (str(config_path), stat.st_mtime_ns, stat.st_size)
    cached = _FILE_CACHE.get(key)
    if cached is None:
        with config_path.open("r", encoding="utf-8") as config_file:
            cached = json.load(config_file)
        _FILE_CACHE[key] = cached
    return cached


def set_dynax_config(config: dict[str, Any] | None) -> None:
    """Install (or clear with ``None``) an in-process configuration override."""
    global _OVERRIDE
    _OVERRIDE = None if config is None else dict(config)


@contextmanager
def dynax_config(config: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Apply a configuration override for the duration of the block."""
    previous = _OVERRIDE
    set_dynax_config(config)
    try:
        yield dict(config)
    finally:
        set_dynax_config(previous)
