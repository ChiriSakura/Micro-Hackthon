"""The rendered cluster config is what provisions real, billed machines.

These tests pin the properties that fail expensively: a Python or Ray version
that silently refuses to join, a worker advertising more CPUs than it has, and a
bootstrap that does not survive the trip through the YAML.
"""

from __future__ import annotations

import base64
import copy
import importlib.util
from pathlib import Path
import re

import pytest
import yaml

SPEC = importlib.util.spec_from_file_location(
    "gcp_render_cluster", Path(__file__).resolve().parents[1] / "scripts" / "gcp_render_cluster.py"
)
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "configs" / "chia" / "fast-gcp.yaml.example"
BOOTSTRAP_PATH = Path(__file__).resolve().parents[1] / "scripts" / "gcp_worker_bootstrap.sh"

DEFAULTS = dict(
    python_version="3.12.14", chia_version="1.0.1", machine_type=None, image=None,
    count=None, setup_timeout=2400, with_verilator=False, with_chisel=False,
)


def _template() -> dict:
    return yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))


def _render(**overrides) -> dict:
    options = {**DEFAULTS, **overrides}
    return renderer.render(_template(), BOOTSTRAP_PATH.read_text(encoding="utf-8"), **options)


def _worker(rendered: dict, name: str = "fast_cpu_worker") -> dict:
    return rendered["gcp_nodes"][name]


def test_bootstrap_survives_the_round_trip_through_yaml(tmp_path):
    rendered = _render()
    document = yaml.safe_load(yaml.safe_dump(rendered))
    commands = _worker(document)["setup_commands"]

    payload = re.match(r"echo (\S+) \| base64 -d", commands[0]).group(1)
    decoded = base64.b64decode(payload).decode("utf-8")

    assert decoded == BOOTSTRAP_PATH.read_text(encoding="utf-8")
    assert commands[-1].endswith("bash ~/fast_bootstrap.sh")


def test_head_versions_are_pinned_into_the_worker_environment():
    commands = _worker(_render(python_version="3.11.7", chia_version="1.2.3"))["setup_commands"]

    assert "FAST_PYTHON_VERSION=3.11.7" in commands[-1]
    assert "FAST_CHIA_VERSION=1.2.3" in commands[-1]


def test_the_pinned_python_carries_the_patch_level():
    """Ray compares X.Y.Z, so shipping only "3.12" lets a 3.12.3 worker try to join
    a 3.12.14 head and fail with a version mismatch after the VM is billed for."""
    commands = _worker(_render())["setup_commands"]

    assert "FAST_PYTHON_VERSION=3.12.14" in commands[-1]
    assert renderer.head_python_version().count(".") == 2


def test_chia_default_miniconda_setup_is_disabled():
    worker = _worker(_render())

    assert worker["skip_default_setup"] is True
    assert worker["setup_timeout"] == 2400


@pytest.mark.parametrize(
    ("machine_type", "expected"),
    [("e2-standard-4", 4), ("c3-standard-8", 8), ("e2-standard-16", 16)],
)
def test_declared_cpu_resources_never_exceed_the_machine(machine_type, expected):
    rendered = _render(machine_type=machine_type)
    resources = rendered["available_node_types"]["fast_cpu_worker"]["resources"]

    assert resources["fast_cpu"] == min(8, expected)
    assert all(value <= expected for value in resources.values() if isinstance(value, int))


def test_a_machine_type_without_a_cpu_suffix_leaves_resources_alone():
    rendered = _render(machine_type="custom-machine")
    resources = rendered["available_node_types"]["fast_cpu_worker"]["resources"]

    assert resources["fast_cpu"] == 8


def test_extras_are_off_unless_asked_for():
    off = _worker(_render())["setup_commands"][-1]
    on = _worker(_render(with_verilator=True, with_chisel=True))["setup_commands"][-1]

    assert "FAST_WITH_VERILATOR=0" in off and "FAST_WITH_CHISEL=0" in off
    assert "FAST_WITH_VERILATOR=1" in on and "FAST_WITH_CHISEL=1" in on


def test_a_template_without_cloud_workers_is_rejected():
    template = _template()
    template.pop("gcp_nodes")

    with pytest.raises(SystemExit, match="no gcp_nodes"):
        renderer.render(template, "#!/bin/sh\n", **DEFAULTS)


def test_reserved_keys_are_not_treated_as_machine_types():
    rendered = _render()

    for key in ("project", "zone"):
        assert not isinstance(rendered["gcp_nodes"][key], dict)


def test_only_cloud_workers_are_declared_and_bootstrapped():
    """The head runs its own raylet via `ray start --head`; a head-local worker
    entry would be a second raylet on the same shared login node, and it must
    never be handed the cloud worker bootstrap either way."""
    rendered = _render()
    node_types = rendered["available_node_types"]

    assert set(node_types) == {"fast_cpu_worker"}
    assert "fast_head" not in rendered["gcp_nodes"]
    assert "fast-env" in " ".join(node_types["fast_cpu_worker"]["worker_env_commands"])


def test_the_head_ray_start_caps_its_cpu_footprint():
    """Autodetected CPUs on a 28-core, heavily shared login node make Ray prestart
    28 workers and miss its raylet startup deadline."""
    commands = " ".join(_render()["head_start_ray_commands"])

    assert "--num-cpus=" in commands
    assert "--object-store-memory=" in commands


def test_the_head_pins_a_temp_dir_that_cloud_workers_also_have():
    """Ray reuses the head's session directory path on every worker verbatim, so a
    head temp dir under /scratch makes the GCP worker fail with EACCES."""
    commands = " ".join(_render()["head_start_ray_commands"])

    assert "--temp-dir=/tmp/ray" in commands
