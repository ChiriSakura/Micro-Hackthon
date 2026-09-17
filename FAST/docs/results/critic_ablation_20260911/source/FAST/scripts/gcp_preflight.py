"""Check every precondition for bringing up a CHIA/GCP cluster. Creates nothing.

The script answers one question: if ``chia up`` were run right now, what would
stop it? It reports each precondition as OK, MISSING or BLOCKED, and exits
non-zero when anything would fail, so it can gate a provisioning step.

    python FAST/scripts/gcp_preflight.py --config FAST/configs/chia/fast-gcp.yaml
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from typing import Any

OK, MISSING, BLOCKED, SKIPPED = "ok", "missing", "blocked", "skipped"


class Report:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(self, name: str, status: str, detail: str, fix: str | None = None) -> str:
        self.checks.append({"check": name, "status": status, "detail": detail, "fix": fix})
        return status

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [item for item in self.checks if item["status"] in {MISSING, BLOCKED}]

    def render(self) -> str:
        symbols = {OK: "  OK    ", MISSING: "  MISSING", BLOCKED: "  BLOCKED", SKIPPED: "  skipped"}
        lines = []
        for item in self.checks:
            lines.append(f"{symbols[item['status']]}  {item['check']}: {item['detail']}")
            if item["fix"] and item["status"] in {MISSING, BLOCKED}:
                lines.append(f"            fix: {item['fix']}")
        return "\n".join(lines)


def check_packages(report: Report) -> None:
    for module, hint in (
        ("chia", "pip install chialoops==1.0.1"),
        ("ray", "pip install 'ray[default]'"),
        ("google.cloud.compute_v1", "pip install google-cloud-compute"),
        ("google.auth", "pip install google-auth"),
        ("yaml", "pip install pyyaml"),
    ):
        try:
            imported = __import__(module, fromlist=["__version__"])
            report.add(f"package {module}", OK, getattr(imported, "__version__", "installed"))
        except ImportError:
            report.add(f"package {module}", MISSING, "not importable", hint)


def check_gcloud(report: Report) -> None:
    binary = shutil.which("gcloud")
    if binary is None:
        report.add(
            "gcloud CLI", MISSING, "not on PATH",
            "only needed to obtain credentials; install from "
            "https://cloud.google.com/sdk/docs/install or copy an existing ADC file here",
        )
        return
    try:
        # gcloud starts slowly off shared storage; it is optional, so never block on it.
        completed = subprocess.run([binary, "version"], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        report.add("gcloud CLI", OK, f"{binary} (present; version probe timed out)")
        return
    version = completed.stdout.splitlines()
    report.add("gcloud CLI", OK, version[0] if version else binary)


def check_credentials(report: Report) -> tuple[Any, str | None]:
    explicit = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    adc = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    try:
        import google.auth
        credentials, project = google.auth.default()
    except Exception as exc:
        source = explicit or (str(adc) if adc.is_file() else "no ADC file found")
        report.add(
            "GCP credentials", MISSING, f"{type(exc).__name__}: {exc} (looked at {source})",
            "run 'gcloud auth application-default login --no-launch-browser' on a machine with a "
            "browser and copy application_default_credentials.json here, or export "
            "GOOGLE_APPLICATION_CREDENTIALS=<service-account.json>",
        )
        return None, None
    report.add("GCP credentials", OK, f"loaded, quota project {project or 'unset'}")
    return credentials, project


def check_compute_api(report: Report, credentials, project: str | None, zone: str) -> None:
    if credentials is None:
        report.add("Compute Engine API", SKIPPED, "no credentials to test with")
        return
    if not project:
        report.add("Compute Engine API", MISSING, "no project resolved from credentials",
                   "export GOOGLE_CLOUD_PROJECT=<project-id>")
        return
    try:
        from google.cloud import compute_v1
        client = compute_v1.InstancesClient(credentials=credentials)
        instances = list(client.list(project=project, zone=zone))
    except Exception as exc:
        report.add("Compute Engine API", BLOCKED, f"{type(exc).__name__}: {exc}",
                   "enable compute.googleapis.com and confirm the account has compute.instances.list")
        return
    report.add("Compute Engine API", OK,
               f"reachable; {len(instances)} instance(s) already in {project}/{zone}")


def check_images(report: Report, credentials, parsed: dict[str, Any] | None) -> None:
    """A bad image family is only discovered when the instance is created.

    By then CHIA has already created firewall rules, so the failure is neither
    free nor clean. Resolving the image here costs one read-only API call.
    """
    nodes = (parsed or {}).get("nodes") or {}
    if credentials is None or not nodes:
        report.add("worker images", SKIPPED, "no credentials or no node types")
        return
    from google.cloud import compute_v1

    client = compute_v1.ImagesClient(credentials=credentials)
    for name, cfg in nodes.items():
        image = getattr(cfg, "image", "") or ""
        # projects/<project>/global/images/family/<family>
        parts = image.split("/")
        if "family" not in parts:
            report.add(f"image for {name}", SKIPPED, f"{image or 'default'} is not a family reference")
            continue
        project, family = parts[1], parts[-1]
        try:
            resolved = client.get_from_family(project=project, family=family, timeout=60)
        except Exception as exc:
            report.add(
                f"image for {name}", BLOCKED, f"{project}/{family} does not resolve: {type(exc).__name__}",
                "list the real families: ImagesClient(...).list(project='ubuntu-os-cloud'). "
                "Ubuntu 24.04+ families carry an architecture suffix, e.g. ubuntu-2404-lts-amd64",
            )
            continue
        report.add(f"image for {name}", OK, f"{family} -> {resolved.name}")


def check_https(report: Report, host: str) -> None:
    try:
        with socket.create_connection((host, 443), timeout=10):
            report.add(f"outbound https to {host}", OK, "reachable")
    except OSError as exc:
        report.add(f"outbound https to {host}", BLOCKED, str(exc),
                   "the control machine needs outbound 443 to the Google APIs")


def check_head_is_local(report: Report, head_ip: str) -> None:
    """CHIA binds tunnel listeners to head_ip on whichever machine runs `chia up`.

    A head_ip belonging to a *different* but reachable machine passes every other
    check and then fails with "Cannot assign requested address" - after the cloud
    instance has been created and billed for.
    """
    import subprocess as sp

    try:
        output = sp.run(["hostname", "-I"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, sp.SubprocessError) as exc:
        report.add("head_ip is local", SKIPPED, f"could not list local addresses: {exc}")
        return
    local = output.split()
    if head_ip in local:
        report.add("head_ip is local", OK, f"{head_ip} is an address on {socket.gethostname()}")
        return
    candidates = [ip for ip in local if not ip.startswith(("10.0.", "127."))]
    report.add(
        "head_ip is local", BLOCKED,
        f"{head_ip} is not an address on this machine ({', '.join(local) or 'none found'})",
        f"set HEAD_IP to this machine's own address"
        + (f", e.g. {candidates[0]}" if candidates else "")
        + " and re-render the config; CHIA cannot bind a tunnel to another host's IP",
    )


def check_ssh_head(report: Report, head_ip: str, ssh_user: str | None, key: str | None) -> None:
    """CHIA drives the head over SSH, so the head must accept public-key auth."""
    target = f"{ssh_user}@{head_ip}" if ssh_user else head_ip
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
               "-o", "ConnectTimeout=10", "-o", "PreferredAuthentications=publickey"]
    if key and Path(key).expanduser().is_file():
        command += ["-i", str(Path(key).expanduser())]
    command += [target, "true"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=40)
    except (OSError, subprocess.SubprocessError) as exc:
        report.add(f"ssh to head {target}", BLOCKED, str(exc))
        return
    if completed.returncode == 0:
        report.add(f"ssh to head {target}", OK, "public-key login works")
        return
    stderr = completed.stderr.strip().splitlines()
    detail = stderr[-1] if stderr else f"exit code {completed.returncode}"
    if "Authentications that can continue" in completed.stderr or "publickey" not in completed.stderr:
        fix = ("this host refuses public-key SSH, so it cannot be the CHIA head; "
               "put the head on a cloud VM and point provider.head_ip at it")
    else:
        fix = "install the public key in the head's ~/.ssh/authorized_keys"
    report.add(f"ssh to head {target}", BLOCKED, detail, fix)


def check_config(report: Report, path: Path | None) -> dict[str, Any] | None:
    if path is None:
        report.add("cluster config", SKIPPED, "no --config given")
        return None
    if not path.is_file():
        report.add("cluster config", MISSING, f"{path} does not exist",
                   "copy configs/chia/fast-gcp.yaml.example and fill in the placeholders")
        return None
    try:
        from chia.cluster.config import load_raw_config, parse_gcp_nodes
        raw = load_raw_config(str(path))
        parsed = parse_gcp_nodes(raw)
    except Exception as exc:
        report.add("cluster config", BLOCKED, f"{type(exc).__name__}: {exc}",
                   "fix the YAML, or export the environment variables it interpolates")
        return None
    if parsed is None:
        report.add("cluster config", MISSING, "parsed, but it declares no gcp_nodes block")
        return {"raw": raw, "gcp": None}
    nodes, project, zone, _network, _subnetwork = parsed
    total = sum(cfg.count for cfg in nodes.values())
    report.add("cluster config", OK,
               f"{path.name} parses: project {project}, zone {zone}, "
               f"{total} worker(s) across {len(nodes)} type(s)")
    return {"raw": raw, "gcp": parsed, "project": project, "zone": zone, "nodes": nodes}


def check_cost_guardrails(report: Report, parsed: dict[str, Any] | None) -> None:
    if not parsed or not parsed.get("nodes"):
        report.add("cost guardrails", SKIPPED, "no node types to price")
        return
    unbounded = [name for name, cfg in parsed["nodes"].items() if not cfg.spot]
    detail = ", ".join(
        f"{name}={cfg.count}x{cfg.machine_type}{' (spot)' if cfg.spot else ''}"
        for name, cfg in parsed["nodes"].items()
    )
    if unbounded:
        report.add("cost guardrails", MISSING, f"{detail}; on-demand: {', '.join(unbounded)}",
                   "prefer spot for batch workers, set a billing budget alert, and always "
                   "run 'chia down' when a run finishes — a budget alert warns, it does not cap")
    else:
        report.add("cost guardrails", OK, f"{detail}; all workers are spot")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--zone", default=None, help="override the zone used for the API probe")
    parser.add_argument("--head-ip", default=None, help="override provider.head_ip for the SSH probe")
    parser.add_argument("--json", type=Path, default=None, help="also write the report as JSON")
    args = parser.parse_args()

    report = Report()
    check_packages(report)
    check_gcloud(report)
    check_https(report, "compute.googleapis.com")
    parsed = check_config(report, args.config)
    credentials, project = check_credentials(report)
    zone = args.zone or (parsed or {}).get("zone") or "us-central1-a"
    check_compute_api(report, credentials, project or (parsed or {}).get("project"), zone)
    check_images(report, credentials, parsed)

    raw = (parsed or {}).get("raw") or {}
    head_ip = args.head_ip or raw.get("provider", {}).get("head_ip")
    if head_ip:
        auth = raw.get("auth", {})
        check_head_is_local(report, head_ip)
        check_ssh_head(report, head_ip, auth.get("ssh_user"), auth.get("ssh_private_key"))
    else:
        report.add("ssh to head", SKIPPED, "no head_ip known")
    check_cost_guardrails(report, parsed)

    print(report.render())
    blocked = report.failed
    print()
    print(f"{len(report.checks) - len(blocked)}/{len(report.checks)} preconditions satisfied.")
    if blocked:
        print("Not ready to provision. Outstanding: " + ", ".join(item["check"] for item in blocked))
    else:
        print("Ready: 'chia up --dry-run <config>' is the next step; it still creates nothing.")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"checks": report.checks}, indent=2) + "\n", encoding="utf-8")
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
