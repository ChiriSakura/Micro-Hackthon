#!/usr/bin/env python3
"""Refresh the RQ1 report from immutable run records, including unfinished runs."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.report_evidence import load_followups


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment', type=Path, required=True)
    args = p.parse_args(); root = args.experiment
    rows, runs, designs = [], [], ['# RQ1 软件配置与生成硬件', '']
    for job in read(root / 'jobs.json', []):
        requested_run = Path(job['run'])
        run = requested_run
        if not (run/'summary.json').exists() and not list(run.glob('round_*/result.json')) and job.get('previous_run'):
            run = Path(job['previous_run'])
        summary = read(run / 'summary.json', {})
        post = read(Path(job['output']) / 'results.json', {})
        events = read(run / 'events.json', [])
        calls = [read(f, {}) for f in (run / 'agent_calls').rglob('*.json')]
        read_ids = sorted({ref['id'] for event in events if event.get('stage') == 'compiler_library_read'
                           for ref in event.get('references', [])})
        plans = [read(f, {}) for f in run.glob('round_*/build_*/system_plan.json')]
        assigned = sorted({ref for plan in plans for module in plan.get('modules', [])
                           for ref in module.get('reference_ids', [])})
        requested_links = sorted({ref for plan in plans for module in plan.get('modules', [])
                                  for ref in module.get('linked_reference_ids', [])})
        audit = {'algorithm': job['algorithm'], 'job_id': job['job_id'],
                 'status': 'resume_not_started' if run != requested_run else summary.get('status', post.get('status', 'running_or_pending')),
                 'evidence_run': str(run),
                 'last_event': events[-1].get('stage') if events else None,
                 'error': summary.get('error'), 'agent_calls_started': len(calls),
                 'agent_calls_finished': sum('response' in c for c in calls),
                 'token_total_recorded': sum((c.get('usage') or {}).get('total_token_count') or 0 for c in calls),
                 'calls_missing_usage': sum('response' in c and c.get('usage') is None for c in calls),
                 'search_pareto_rounds': summary.get('pareto_rounds', []),
                 'qualified_pareto_rounds': post.get('qualified_pareto_rounds', [])}
        audit.update(references_read=read_ids, references_assigned=assigned,
                     references_link_requested=requested_links)
        runs.append(audit)
        designs += [f'## {job["algorithm"]} / 参考库使用审计', '',
                    f'已读取：{read_ids}。', '', f'已分配（包含失败的计划）：{assigned}。', '',
                    f'请求原生链接：{requested_links}。读取或分配不证明正确复用；成功设计的链接见逐轮计划。', '']
        records = summary.get('rounds') or [read(f, {}) for f in sorted(run.glob('round_*/result.json'))]
        for record in records:
            e = record.get('evaluation') or {}
            prof = record.get('profile') or {}
            held = next((r for r in post.get('rounds', []) if r['round'] == record['round']), {})
            if 'independently_qualified' not in held:
                historical = read(Path(job.get('previous_output', root/'_absent'))/'results.json', {}).get('rounds', [])
                if job['algorithm'] == 'rq1_dynax_xm':
                    historical += read(root/'dynax_baseline/results.json', {}).get('rounds', [])
                for old in historical:
                    old_e = old.get('evaluation') or {}
                    if (old.get('independently_qualified') and old.get('config') == record.get('config')
                            and e.get('design_sha256') and old_e.get('design_sha256') == e['design_sha256']
                            and e.get('artifacts') and old_e.get('artifacts') == e['artifacts']):
                        held = old
            row = {'algorithm': job['algorithm'], 'round': record['round'], 'status': record['status'],
                   'error': record.get('error'),
                   'config': json.dumps(record.get('config'), sort_keys=True),
                   'calibration_rmse': prof.get('quality_loss'), 'calibration_sparsity': prof.get('sparsity'),
                   'selection_worst_rmse': prof.get('selection_quality_loss'),
                   'heldout_rmse': held.get('heldout', {}).get('quality_loss'),
                   'heldout_sparsity': held.get('heldout', {}).get('sparsity'),
                   'search_feasible': e.get('feasible'), 'independently_qualified': held.get('independently_qualified'),
                   'critic_layer': (record.get('critique') or {}).get('layer'),
                   'critique_applied': record.get('critique_applied', False)}
            config = record.get('config') or {}
            row['xm_collapses_to_fixed_nm'] = (config.get('n1') == config.get('n2') and config.get('t1_quarters') == 0
                                                if job['algorithm'] == 'rq1_dynax_xm' and config else None)
            for key in ('area_um2', 'power_mw', 'frequency_mhz', 'latency_ns', 'energy_nj',
                        'energy_efficiency_queries_per_joule', 'energy_efficiency_dense_equivalent_tops_per_w',
                        'slack_ns', 'hold_slack_ns', 'route_drc_violations'):
                row[key] = e.get(key)
            rows.append(row)
            designs += [f'## {job["algorithm"]} / round {record["round"]}', '',
                        '软件配置：`' + row['config'] + '`。', '']
            if record.get('error'):
                designs += ['失败记录：' + record['error'], '']
            if 'selection_quality_loss' in prof:
                designs += [f'校准＋选参验证集最差 RMSE：{prof["selection_quality_loss"]:.6g}；'
                            '最终留出集独立评估，不反馈搜索。', '']
            if record.get('rollback_to_round'):
                if record.get('prior_evaluations') and e.get('complete'):
                    designs += [f'历史PPA尝试曾回退至R{record["rollback_to_round"]}；同轮重测现已完成，上述数值来自当前测量。原记录保留历史回退标记。', '']
                else:
                    designs += [f'本候选失败，恢复 R{record["rollback_to_round"]}；'
                            f'Critic 测量证据来自 R{record.get("critique_evidence_round")}，不是本轮新 PPA。', '']
            if row['xm_collapses_to_fixed_nm']:
                designs += ['注意：该 X:M 配置 n1=n2 且 t1=0，退化为固定 N:M 配额；不得计为保留动态块配额特性的成功。', '']
            plan = record.get('system_plan') or {}
            if plan:
                designs += [f'语言：{plan["language"]}；顶层：`{plan["top"]}`。', '', plan.get('rationale', ''), '',
                            '| 模块 | 职责 | 子模块 | 只读链接 |', '|---|---|---|---|']
                for module in plan.get('modules', []):
                    clean = lambda x: str(x).replace('|', '/').replace('\n', ' ')
                    designs.append('| ' + ' | '.join(map(clean, [module['name'], module['purpose'],
                        ', '.join(module['dependencies']), ', '.join(module.get('linked_reference_ids', []))])) + ' |')
            advice = record.get('critique')
            if advice:
                designs += ['', 'Critic 原始结构化建议：', '', '```json', json.dumps(advice, ensure_ascii=False, indent=2), '```', '',
                            f'下一轮是否开始尝试该建议：{record.get("critique_applied", False)}。这不单独证明建议正确或有效。', '']
    followups = load_followups(root)
    for r in followups:
        designs += [f'## {r["algorithm"]} / {r["display_label"]}（诊断辅助修复）', '',
            f'独立验收：{r["qualified"]}；详情见[修复报告]({r["report"]})。原五候选保持独立。', '',
            '软件配置：`' + json.dumps(r['config'], sort_keys=True) + '`。', '',
            '系统计划与末轮Critic：', '', '```json',
            json.dumps({'plan': r['system_plan'], 'critic': r['critique']}, indent=2, ensure_ascii=False), '```', '']
    result = {'followups': followups, 'updated_utc': datetime.now(timezone.utc).isoformat(), 'runs': runs, 'rounds': rows}
    (root / 'metrics.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    (root / 'DESIGNS.md').write_text('\n'.join(designs) + '\n')
    if rows:
        with (root / 'metrics.csv').open('w', newline='') as stream:
            columns = list(rows[0]) + ['evidence_id', 'evidence_class', 'display_label']
            writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore'); writer.writeheader()
            writer.writerows({**r, 'evidence_id': f'{r["algorithm"]}_R{r["round"]}',
                'evidence_class': 'original_trajectory', 'display_label': f'R{r["round"]}'} for r in rows)
            writer.writerows({**r, 'config': json.dumps(r['config'], sort_keys=True)} for r in followups)
    lines = ['# RQ1 实验进度与结果', '', f'更新时间：{result["updated_utc"]}。协议见 [PROTOCOL.md](PROTOCOL.md)。', '',
             f'{len(runs)} 个算法运行；设计轮数、预算与共同约束以本批次 PROTOCOL.md 为准。', '',
             '| 算法 | 状态 | 最近事件 | 已返回/已发起调用 | 已记录 tokens | 搜索 Pareto | 独立验证通过的 Pareto |',
             '|---|---|---|---:|---:|---|---|']
    for r in runs:
        lines.append(f'| {r["algorithm"]} | {r["status"]} | {r["last_event"]} | {r["agent_calls_finished"]}/{r["agent_calls_started"]} | {r["token_total_recorded"]} | {r["search_pareto_rounds"]} | {r["qualified_pareto_rounds"]} |')
    lines += ['', '## 逐轮数据', '', '| 算法/轮次 | 校准 RMSE | 留出 RMSE | 搜索可行 | 面积 µm² | 功耗 mW | 延迟 ns | 能效 Gqueries/J | Critic |',
              '|---|---:|---:|---|---:|---:|---:|---:|---|']
    def num(x): return '—' if x is None else f'{x:.6g}'
    for r in rows:
        ee = r['energy_efficiency_queries_per_joule']
        lines.append('| ' + ' | '.join([f'{r["algorithm"]}/{r["round"]}', num(r['calibration_rmse']), num(r['heldout_rmse']),
            str(r['search_feasible']), num(r['area_um2']), num(r['power_mw']), num(r['latency_ns']),
            num(ee / 1e9 if ee else None), str(r['critic_layer'])]) + ' |')
    if not rows:
        lines += ['', '尚无完成的设计轮次。面积、功耗、能效均未填入估算值。']
    for r in runs:
        if r['error']:
            lines += ['', f'**{r["algorithm"]} 失败原因：** {r["error"]}']
    lines += ['', '## 迭代观察', '', '软件参数、模块划分与每轮 Critic 原文见 [DESIGNS.md](DESIGNS.md)。', '']
    for run in runs:
        candidates = [r for r in rows if r['algorithm'] == run['algorithm'] and r['search_feasible']]
        if not candidates:
            lines.append(f'- {run["algorithm"]}：当前没有满足全部搜索约束的点；不能填报有效能效改善。')
            continue
        first = candidates[0]
        efficient = max(candidates, key=lambda r: r['energy_efficiency_queries_per_joule'])
        fastest = min(candidates, key=lambda r: r['latency_ns'])
        gain = efficient['energy_efficiency_queries_per_joule'] / first['energy_efficiency_queries_per_joule']
        speed = first['latency_ns'] / fastest['latency_ns']
        lines.append(f'- {run["algorithm"]}：首个可行点 R{first["round"]}；最高能效 R{efficient["round"]} '
                     f'（相对首个可行点 {gain:.3f}×），最低延迟 R{fastest["round"]}（加速 {speed:.3f}×）。'
                     '这是单次搜索观察，非 Critic 因果消融。')
    if followups:
        lines += ['', '## 后续诊断辅助修复（不并入原五轮）', '',
                  '| 编号 | 算法 | 独立验收 | Setup/ns | Hold/ns | DRC | 延迟ns | 能效Gqueries/J |',
                  '|---|---|---|---:|---:|---:|---:|---:|']
        for r in followups:
            lines.append('| ' + ' | '.join([r['display_label'], r['algorithm'], str(r['qualified']),
                *[num(r[k]) for k in ('slack_ns','hold_slack_ns','route_drc_violations','latency_ns')],
                num(r['energy_efficiency_queries_per_joule']/1e9)]) + ' |')
            lines += ['', f'[完整修复报告]({r["report"]})；该点的成功不回写为原五轮自主成功。', '']
    lines += ['', '## 结论边界', '',
              '搜索可行要求校准精度、RTL E2E 与完整 Hammer 物理约束同时通过；独立合格还要求留出精度、额外 RTL 向量及布线后门级验证通过。空列表不是证明不存在可行设计。', '',
              '功耗来自布线寄生与统一活动率的工具分析，并非芯片实测。RMSE 是输出误差，不是模型任务准确率。本轮没有人工优化对照与重复实验，不能据此声称取代专家优化或证明 Critic 的因果收益。', '',
              '改善比例仅比较同一次运行内可行点，不把时序失败点当成有效初始基线。Critic 的建议被尝试、最终设计通过与可行指标改善是三个不同层次的证据。', '',
              '后续优先：增加独立重复运行；对相同起点做等预算 Critic ON/OFF；引入真实模型 QKV；扩展 head dimension/序列长度；比较固定模板与人工调参基线。', '']
    (root / 'RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps({'runs': len(runs), 'rounds': len(rows)}))


if __name__ == '__main__':
    main()
