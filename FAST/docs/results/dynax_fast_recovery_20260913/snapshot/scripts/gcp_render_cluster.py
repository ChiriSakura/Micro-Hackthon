"""Render a runnable CHIA cluster config from the template plus the bootstrap.

The bootstrap script is the single source of truth for what a worker needs.
Rather than duplicating it inside the YAML, this renders it into each cloud node
type's ``setup_commands`` (base64-encoded, so no quoting can break it) and turns
off CHIA's default miniconda setup, which FAST does not use.

The Python and chialoops versions default to whatever the *current* interpreter
runs, because Ray refuses to join a cluster whose head differs on either - and it
compares the full X.Y.Z, so 3.12.9 and 3.12.3 are a mismatch. Render this on the
machine that will actually be the head.

    python FAST/scripts/gcp_render_cluster.py \
        --template FAST/configs/chia/fast-gcp.yaml.example \
        --out FAST/configs/chia/fast-gcp.yaml \
        --machine-type e2-standard-4
"""

from __future__ import annotations

import argparse
import base64
import importlib.metadata as metadata
import re
from pathlib import Path
import sys
from typing import Any

import yaml


RESERVED = {"project", "zone", "network", "subnetwork"}
# GCP standard machine names end in their vCPU count, e.g. e2-standard-4.
VCPU_SUFFIX = re.compile(r"-(\d+)$")
SCRIPT_PATH = Path(__file__).resolve().parent / "gcp_worker_bootstrap.sh"
REMOTE_PATH = "~/fast_bootstrap.sh"


def head_python_version() -> str:
    """The FULL version: Ray compares X.Y.Z and refuses to join on any difference."""
    return ".".join(str(part) for part in sys.version_info[:3])


def head_chia_version() -> str:
    try:
        return metadata.version("chialoops")
    except metadata.PackageNotFoundError:
        return "1.0.1"


def setup_commands(script: str, environment: dict[str, str]) -> list[str]:
    """Ship the bootstrap to the worker and run it, without a shared filesystem."""
    payload = base64.b64encode(script.encode("utf-8")).decode("ascii")
    exports = " ".join(f"{key}={value}" for key, value in sorted(environment.items()))
    return [
        f"echo {payload} | base64 -d > {REMOTE_PATH}",
        f"chmod +x {REMOTE_PATH}",
        f"{exports} bash {REMOTE_PATH}",
    ]


def render(
    template: dict[str, Any],
    script: str,
    *,
    python_version: str,
    chia_version: str,
    machine_type: str | None,
    image: str | None,
    count: int | None,
    setup_timeout: int,
    with_verilator: bool,
    with_chisel: bool,
) -> dict[str, Any]:
    nodes = template.get("gcp_nodes")
    if not isinstance(nodes, dict):
        raise SystemExit("template has no gcp_nodes section; nothing to bootstrap")

    environment = {
        "FAST_PYTHON_VERSION": python_version,
        "FAST_CHIA_VERSION": chia_version,
        "FAST_WITH_VERILATOR": "1" if with_verilator else "0",
        "FAST_WITH_CHISEL": "1" if with_chisel else "0",
    }
    commands = setup_commands(script, environment)

    machine_types: dict[str, str] = {}
    rendered = 0
    for name, node in nodes.items():
        if name in RESERVED or not isinstance(node, dict):
            continue
        node["skip_default_setup"] = True  # CHIA's default installs miniconda; FAST uses a venv
        node["setup_timeout"] = setup_timeout
        node["setup_commands"] = commands
        if machine_type:
            node["machine_type"] = machine_type
        if image:
            node["image"] = image
        if count is not None:
            node["count"] = count
        machine_types[name] = node.get("machine_type", "")
        rendered += 1
    if rendered == 0:
        raise SystemExit("gcp_nodes contains no machine types to bootstrap")
    _align_cpu_resources(template, machine_types)
    return template


def _align_cpu_resources(template: dict[str, Any], machine_types: dict[str, str]) -> list[str]:
    """Keep declared Ray resources from exceeding the machine's real vCPU count.

    A node type advertising more CPUs than it has makes Ray oversubscribe it, and
    the symptom is a slow, thrashing worker rather than an error.
    """
    notes = []
    node_types = template.get("available_node_types") or {}
    for name, machine_type in machine_types.items():
        match = VCPU_SUFFIX.search(machine_type or "")
        resources = (node_types.get(name) or {}).get("resources")
        if match is None or not isinstance(resources, dict):
            continue
        vcpus = int(match.group(1))
        for key, value in list(resources.items()):
            if isinstance(value, int) and value > vcpus:
                resources[key] = vcpus
                notes.append(f"{name}.{key}: {value} -> {vcpus} (machine has {vcpus} vCPU)")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--script", type=Path, default=SCRIPT_PATH)
    parser.add_argument("--python-version", default=None, help="exact X.Y.Z; defaults to this interpreter's")
    parser.add_argument("--chia-version", default=None, help="defaults to the installed chialoops")
    parser.add_argument("--machine-type", default=None, help="override every worker machine type")
    parser.add_argument("--image", default=None, help="override every worker image")
    parser.add_argument("--count", type=int, default=None, help="override every worker count")
    parser.add_argument("--setup-timeout", type=int, default=2400)
    parser.add_argument("--with-verilator", action="store_true")
    parser.add_argument("--with-chisel", action="store_true")
    args = parser.parse_args()

    python_version = args.python_version or head_python_version()
    chia_version = args.chia_version or head_chia_version()
    template = yaml.safe_load(args.template.read_text(encoding="utf-8"))
    script = args.script.read_text(encoding="utf-8")

    rendered = render(
        template, script,
        python_version=python_version,
        chia_version=chia_version,
        machine_type=args.machine_type,
        image=args.image,
        count=args.count,
        setup_timeout=args.setup_timeout,
        with_verilator=args.with_verilator,
        with_chisel=args.with_chisel,
    )

    header = (
        "# GENERATED by FAST/scripts/gcp_render_cluster.py - do not edit by hand.\n"
        f"# bootstrap : {args.script}\n"
        f"# head match: Python {python_version}, chialoops {chia_version}\n"
        "# Edit the template or the bootstrap script and re-render instead.\n"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(header + yaml.safe_dump(rendered, sort_keys=False, width=10_000), encoding="utf-8")

    node_types = rendered.get("available_node_types") or {}
    workers = {name: node for name, node in rendered["gcp_nodes"].items()
               if name not in RESERVED and isinstance(node, dict)}
    print(f"wrote {args.out}")
    print(f"  head match  : Python {python_version}, chialoops {chia_version}")
    for name, node in workers.items():
        resources = (node_types.get(name) or {}).get("resources", {})
        print(f"  {name}: {node.get('count', 1)}x {node.get('machine_type')} "
              f"{'spot' if node.get('spot') else 'on-demand'}, image {node.get('image', '').split('/')[-1]}")
        print(f"    resources : {resources}")
    print(f"  extras      : verilator={args.with_verilator}, chisel={args.with_chisel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
