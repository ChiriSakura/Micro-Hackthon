"""Render the exhaustive process appendix from analyzed ablation artifacts."""
import argparse
import csv
import json
from pathlib import Path


def fmt(value, digits=3):
    if value is None or value == '': return '—'
    try: return f'{float(value):.{digits}f}'
    except (ValueError, TypeError): return str(value)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    summary=json.loads((args.out/'summary.json').read_text())
    assert summary['all_complete'], 'Cannot render final process report with unfinished runs'
    assert not summary['audit_errors'], summary['audit_errors']
    rows=list(csv.DictReader((args.out/'rounds.csv').open()))
    lines=['# 完整实验过程','',
        '每次最多 5 轮；每轮只有一个新的解析模型候选评估。L1 拒绝不进入 RTL。下面面积/功耗仅属于 BlockScheduler，功耗使用统一活动率 0.0213；时序不通过时不报告可用 latency。完整参数、预测指标和记录 ID 见 `rounds.csv`；完整原始分析见各运行 `refinement.json` / `api_*.json`。','']
    for cell in summary['protocol']['runs']:
        raw=json.loads((args.study/'runs'/cell['id']/'refinement.json').read_text())
        lines += [f'## {cell["id"]}','',
            f'Proposer={cell["proposer"]}；Critic={cell["critic"]}；ablation={cell["ablation"]}；seed={cell["seed"]}；墙钟时间 {raw["wall_seconds"]:.1f}s。',
            f'保留的最优已验证方案：`{raw["best_verified_design_id"]}`。原始记录：[refinement.json](raw/runs/{cell["id"]}/refinement.json)。','',
            '| loop | 实际动作 | rows/PE/queue | L1 | 独立门 | latency µs | 面积 µm² | slack ns | 功耗估计 mW |',
            '|---|---|---|---|---|---|---|---|---|']
        selected=[r for r in rows if r['run_id']==cell['id']]
        for r in selected:
            gate='通过' if r['verified']=='True' else '时序失败' if r['function_pass']=='True' else '未执行' if r['independent_attempted']=='False' else '功能/工具失败'
            action=r['critic_action'] or ('proposer 提议（Critic shadow）' if cell['arm']=='shadow' else 'proposer 提议')
            lines.append(f'| {r["loop"]} | {action} | {r["num_rows"]}/{r["pe_per_row"]}/{r["queue_depth"]} | {"通过" if r["analytical_pass"]=="True" else "拒绝"} | {gate} | {fmt(r["latency_us"],6)} | {fmt(r["area_um2"])} | {fmt(r["slack_ns"],4)} | {fmt(r["uniform_activity_power_mw"],6)} |')
        lines += ['','Critic 分析及执行记录：','']
        if not raw['critic_reviews']: lines.append('- 无 Critic 调用。')
        for i,review in enumerate(raw['critic_reviews'],1):
            action=json.dumps(review['critique']['mutations'],ensure_ascii=False)
            lines.append(f'- 第 {i} 次分析：{review["critique"]["summary"]}；动作 `{action}`；执行状态 `{review["outcome"].get("state")}`；回退原因 `{review.get("fallback_reason")}`。')
        lines += ['']
    (args.out/'PROCESS.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
