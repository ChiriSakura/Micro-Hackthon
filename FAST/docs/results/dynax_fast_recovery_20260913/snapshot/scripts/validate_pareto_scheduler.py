"""Fresh RTL/STA validation of a queue-depth adaptation on frozen trace tiles.

Scope is ONLY BlockScheduler. It measures scheduler cycles, logic area and
pre-layout timing. It deliberately does not manufacture full-attention energy.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.agents.rtl_gate import LocalRtlGate, MODULES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--method", default="xm")
    parser.add_argument("--design", type=Path, help="Use the exact exported FAST candidate's label/rows/PE/M/depth")
    parser.add_argument("--tile-offset", type=int, default=256)
    parser.add_argument("--tile-count", type=int, default=128)
    parser.add_argument("--depths", type=int, nargs="+", default=[0, 2, 4])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--containers", type=Path, required=True)
    parser.add_argument("--liberty", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--frequency-mhz", type=float, default=350)
    args = parser.parse_args()
    design = json.loads(args.design.read_text()) if args.design else None
    rows, pes, block = 32, 4, 64
    if design:
        point = design["point"]
        rows, pes, block = point["num_rows"], point["pe_per_row"], design["algorithm"]["block_m"]
        args.method, args.depths = design["label"], [point["queue_depth"]]
    if args.tile_offset < 0 or args.tile_count < 0 or args.frequency_mhz <= 0:
        parser.error("invalid trace slice or frequency")
    if not set(args.depths) <= {0, 2, 4, 8, 16}:
        parser.error("supported scheduler depths: 0, 2, 4, 8, 16")
    # A fresh directory prevents stale build artifacts from passing a failed run.
    args.out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[2]
    payload = json.loads(args.workload.read_text())
    if payload["tile"]["rows"] != rows or payload["tile"]["block"] != block:
        parser.error("trace rows/block do not match the candidate hardware")
    all_tiles = payload["methods"][args.method]["tiles"]
    if args.tile_count == 0:
        args.tile_count = len(all_tiles) - args.tile_offset
    if args.tile_count <= 0:
        parser.error("trace contains no active tiles")
    tiles = all_tiles[args.tile_offset:args.tile_offset+args.tile_count]
    if len(tiles) != args.tile_count:
        parser.error("requested trace slice not available")
    sliced = {**payload, "methods": {args.method: {"tiles": tiles}}}
    workload = args.out / "workload.json"
    workload.write_text(json.dumps(sliced))
    source_files = [*sorted((repo/"FAST/hardware/chisel").rglob("*.scala")),
                    repo/"FAST/hardware/tb/tb_block_scheduler.cpp",
                    repo/"FAST/hardware/tb/gen_ports.py"]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        "scope": f"BlockScheduler, {rows} rows x {pes} PE, M={block}; not full attention",
        "design_id": design["design_id"] if design else None,
        "design_sha256": digest(args.design) if design else None,
        "selected_algorithm": design["algorithm"] if design else None,
        "complete_captured_task": payload["methods"][args.method].get("complete_task", False)
                                  and args.tile_offset == 0 and args.tile_count == len(all_tiles),
        "workload_source_sha256": digest(args.workload),
        "workload_slice_sha256": digest(workload), "source": payload["source"],
        "trace_slice": [args.tile_offset, args.tile_offset+args.tile_count],
        "not_a_heldout_model": True, "fixed_frequency_mhz": args.frequency_mhz,
        "sources": {str(p.relative_to(repo)): digest(p) for p in source_files},
        "liberty_sha256": digest(args.liberty), "results": [],
        "energy_j": None, "energy_reason": "no workload-activity power measurement",
    }
    base = MODULES["BlockSched_S4"]
    gate = LocalRtlGate(repo=repo, work_root=args.out/"build", containers=args.containers,
                        python=args.python, workload=workload, liberty=args.liberty,
                        synthesise=True, sta_container=args.containers/"opensta.sif",
                        clock_period_ns=1000 / args.frequency_mhz,
                        timeout_seconds=600)
    for depth in args.depths:
        target = f"BlockSched_R{rows}P{pes}M{block}Q{depth}" if design else f"BlockSched_S{depth}"
        ports = ["--module", "BlockScheduler", "--rows", str(rows), "--pes", str(pes),
                 "--queue-depth", str(depth), "--col-bits", str(math.ceil(math.log2(block)))]
        MODULES[target] = replace(base, target=target, ports_args=tuple(ports),
                                 stimulus_args=("--method", args.method, "--pe", str(pes),
                                                "--max-tiles", str(args.tile_count)))
        started = time.monotonic()
        stages = gate.check(repo/"FAST/hardware/chisel/src/main/scala"/base.source, target)
        metrics = {}
        for stage in stages:
            if stage.passed:
                metrics.update(stage.metrics)
        passed = len(stages) == 3 and all(s.passed for s in stages)
        period = metrics.get("critical_path_ns")
        slack = metrics.get("slack_ns")
        feasible = bool(passed and period and slack is not None and slack >= 0)
        result = {"depth": depth, "passed": passed, "frequency_feasible": feasible,
                  "wall_seconds": time.monotonic()-started, "metrics": metrics,
                  "stages": [asdict(s) for s in stages],
                  "latency_s": (metrics["cycles"]/(args.frequency_mhz*1e6)
                                if feasible and "cycles" in metrics else None)}
        manifest["results"].append(result)
        (args.out/"validation.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        print(f"{target}: passed={passed}, frequency_feasible={feasible}, {metrics}", flush=True)
    unchanged = all(digest(p) == manifest["sources"][str(p.relative_to(repo))] for p in source_files)
    manifest["sources_unchanged"] = unchanged
    (args.out/"validation.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if unchanged and all(r["passed"] and r["frequency_feasible"] for r in manifest["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
