#!/usr/bin/env python3
"""Export measured per-round results for any FAST algorithm and PPA backend.

Original records remain unchanged. Missing measurements stay empty; failed
rounds are retained and never filled using analytical estimates.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.library import save
from fast.fullstack.recovery import read_summary


FIELDS = (
    "round", "status", "ppa_backend", "complete", "feasible", "cases", "cycles",
    "frequency_mhz", "latency_ns", "area_um2", "power_mw", "energy_nj",
    "energy_efficiency_queries_per_joule", "slack_ns", "hold_slack_ns",
    "route_drc_violations", "quality_loss", "critic_layer", "critique_applied",
)


def report(run: Path, output: Path) -> dict:
    summary = read_summary(run)
    task = json.loads((run / "task.json").read_text())
    rows = []
    for record in summary["rounds"]:
        evaluation = record.get("evaluation") or {}
        verification = evaluation.get("verification") or {}
        row = {key: evaluation.get(key) for key in FIELDS}
        row.update(round=record["round"], status=record["status"],
                   cases=verification.get("cases"), cycles=verification.get("mean_cycles"),
                   critic_layer=(record.get("critique") or {}).get("layer"),
                   critique_applied=record.get("critique_applied", False))
        rows.append(row)
    result = {"algorithm": task["algorithm"], "status": summary["status"],
              "constraints": task["constraints"], "agent_calls": summary["agent_calls"],
              "reference_integrity": summary["reference_integrity"],
              "pareto_rounds": summary["pareto_rounds"], "rounds": rows,
              "scope": "Measured points from this run only; not a controlled ablation or global optimum"}
    output.mkdir(parents=True, exist_ok=True)
    save(output / "metrics.json", result)
    with (output / "metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    lines = [f'# {task["algorithm"]}：逐轮测量', '',
             f'运行状态：`{summary["status"]}`。非支配轮次：`{summary["pareto_rounds"]}`。', '',
             '| 轮次 | 后端 | 可行 | 延迟 ns | 单元面积 µm² | 功耗 mW | 能量 nJ | 能效 Gqueries/J |',
             '|---|---|---|---:|---:|---:|---:|---:|']
    def number(value):
        return '—' if value is None else f'{value:.9g}'
    for row in rows:
        efficiency = row['energy_efficiency_queries_per_joule']
        values = [str(row['round']), str(row['ppa_backend'] or '—'), str(row['feasible']),
                  *[number(row[key]) for key in ('latency_ns', 'area_um2', 'power_mw', 'energy_nj')],
                  number(None if efficiency is None else efficiency / 1e9)]
        lines.append('| ' + ' | '.join(values) + ' |')
    lines += ['', '功耗的方法、活动率、工艺角与物理范围以原始 evaluation 为准。'
              '缺失字段保留为空；失败轮次不补入估算值。单次迭代改善不等于完成 Critic 消融。', '']
    (output / 'MEASUREMENTS.md').write_text('\n'.join(lines))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    result = report(args.run, args.output)
    print(json.dumps({'status': result['status'], 'rounds': len(result['rounds'])}))


if __name__ == '__main__':
    main()
