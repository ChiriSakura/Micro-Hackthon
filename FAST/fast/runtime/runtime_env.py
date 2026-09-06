"""Ship the FAST package to remote Ray workers.

A cloud worker is bootstrapped with `chialoops` only; FAST's own code is not
installed there. Ray's ``py_modules`` uploads the package to the cluster's
object store and makes it importable on every worker, so a worker stays generic
and never needs redeploying when FAST changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def fast_runtime_env(
    *,
    extra_py_modules: Iterable[str | Path] = (),
    env_vars: dict[str, str] | None = None,
    pip: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build the runtime environment that makes ``fast`` importable remotely.

    ``pip`` is deliberately optional and empty by default: resolving wheels on
    every worker is slow and can silently drift from the head's pinned versions,
    so anything a worker needs at import time belongs in the bootstrap script.
    """
    if not (PACKAGE_ROOT / "__init__.py").is_file():
        raise RuntimeError(f"{PACKAGE_ROOT} is not an importable package; py_modules would ship nothing")

    modules = [str(PACKAGE_ROOT)]
    for module in extra_py_modules:
        path = Path(module).resolve()
        if not path.exists():
            raise FileNotFoundError(f"py_modules entry does not exist: {path}")
        modules.append(str(path))

    environment: dict[str, Any] = {"py_modules": modules}
    if env_vars:
        environment["env_vars"] = {str(k): str(v) for k, v in env_vars.items()}
    if pip:
        environment["pip"] = list(pip)
    return environment
