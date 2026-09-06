"""The runtime environment is what makes FAST importable on a machine that
never had it installed. If it ships nothing, remote tasks fail at import time
with an error that looks like a cluster problem."""

from __future__ import annotations

from pathlib import Path

import pytest

from fast.runtime.runtime_env import PACKAGE_ROOT, fast_runtime_env


def test_the_fast_package_itself_is_shipped():
    environment = fast_runtime_env()

    assert environment["py_modules"] == [str(PACKAGE_ROOT)]
    assert (Path(environment["py_modules"][0]) / "__init__.py").is_file()
    assert (Path(environment["py_modules"][0]) / "schemas" / "models.py").is_file()


def test_nothing_extra_is_installed_by_default():
    """Resolving wheels per worker is slow and drifts from the head's pins."""
    environment = fast_runtime_env()

    assert "pip" not in environment
    assert "env_vars" not in environment


def test_extra_modules_and_env_vars_are_passed_through(tmp_path):
    extra = tmp_path / "extra_pkg"
    extra.mkdir()
    (extra / "__init__.py").touch()

    environment = fast_runtime_env(extra_py_modules=[extra], env_vars={"HF_HUB_OFFLINE": 1})

    assert str(extra) in environment["py_modules"]
    assert environment["env_vars"] == {"HF_HUB_OFFLINE": "1"}


def test_a_missing_extra_module_fails_before_the_cluster_is_touched(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        fast_runtime_env(extra_py_modules=[tmp_path / "absent"])


def test_pip_is_included_only_when_asked_for():
    environment = fast_runtime_env(pip=["numpy==1.26.4"])

    assert environment["pip"] == ["numpy==1.26.4"]
