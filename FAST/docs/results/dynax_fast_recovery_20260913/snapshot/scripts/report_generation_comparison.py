#!/usr/bin/env python3
"""Compare matched generated designs in latency vs fixed-work energy efficiency.

Raw results remain immutable. Post-route remeasurements are plotted separately
from pre-layout estimates, and an observed frontier may contain only one point.
"""
import argparse
import csv
import json
from pathlib import Path


def frontier(rows):
    valid=[r for r in rows if r['feasible'] and r['energy_nj']>0 and r['latency_ns']>0]
    return [r for r in valid if not any(q['latency_ns']<=r['latency_ns'] and q['efficiency_gqueries_per_j']>=r['efficiency_gqueries_per_j']
                and (q['latency_ns']<r['latency_ns'] or q['efficiency_gqueries_per_j']>r['efficiency_gqueries_per_j']) for q in valid)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--on',type=Path,required=True);p.add_argument('--off',type=Path,required=True)
    p.add_argument('--physical',type=Path,action='append',default=[],help='revalidation.json file, original_run/round must identify an arm')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dense-ops-per-query',type=int,default=24,help='Fixed dense-equivalent QK+AV work, 2 ops/MAC; threshold task=24')
    args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    runs={};records=[];sources={}
    for arm,path in [('critic',args.on),('no_critic',args.off)]:
        summary=json.loads((path/'summary.json').read_text());task=json.loads((path/'task.json').read_text())
        runs[arm]={'run':str(path.resolve()),'status':summary['status'],'error':summary.get('error'),
                   'agent_calls':summary['agent_calls'],'task':task,'records':summary['rounds']}
        sources[str(path.resolve())]=arm
        for record in summary['rounds']:
            e=record.get('evaluation',{})
            if e.get('complete'):records.append((arm,record['round'],record['config'],e))
    fields=['algorithm','seed','constraints','max_loops','compiler_attempts','module_attempts','assembly_attempts','module_workers','activity']
    for name in fields:
        if runs['critic']['task'].get(name)!=runs['no_critic']['task'].get(name):raise ValueError('Unmatched experiment field '+name)
    # Hash inventories of the imported source files are the matched starting condition.
    provenance=[json.loads((p/'round_01/initial_design/provenance.json').read_text()) for p in (args.on,args.off)]
    if provenance[0]['source_hashes']!=provenance[1]['source_hashes']:raise ValueError('Different starting RTL')
    for path in args.physical:
        r=json.loads(path.read_text());arm=sources.get(str(Path(r['original_run']).resolve()))
        if arm is None:raise ValueError('Physical measurement not from either compared run')
        if r.get('evaluation',{}).get('complete'):
            config=runs[arm]['records'][r['original_round']-1]['config']
            records.append((arm,r['original_round'],config,r['evaluation']))
    rows=[]
    for arm,number,config,e in records:
        rows.append({'arm':arm,'round':number,'config':json.dumps(config,sort_keys=True),
            'backend':e.get('ppa_backend','yosys_opensta'),'feasible':e['feasible'],
            **{k:e[k] for k in ('latency_ns','energy_nj','area_um2','power_mw','quality_loss')},
            'efficiency_gqueries_per_j':1/e['energy_nj'],
            'dense_equivalent_tops_per_w':args.dense_ops_per_query/(1000*e['energy_nj'])})
    with (out/'points.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    fronts={backend:frontier([r for r in rows if r['backend']==backend]) for backend in sorted({r['backend'] for r in rows})}
    (out/'comparison.json').write_text(json.dumps({'runs':runs,'points':rows,'frontiers':fronts,
        'fixed_dense_ops_per_query':args.dense_ops_per_query,
        'scope':'single matched starting design, one generation run per arm; budgets matched by rounds, actual calls may differ; not statistical ablation'},indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,len(fronts),figsize=(6*len(fronts),4.8),squeeze=False)
    for ax,(backend,front) in zip(axes[0],fronts.items()):
        for arm,color,marker in [('critic','#126e82','o'),('no_critic','#c15b36','s')]:
            group=[r for r in rows if r['backend']==backend and r['arm']==arm]
            for r in group:
                ax.scatter(r['latency_ns'],r['dense_equivalent_tops_per_w'],color=color,marker=marker if r['feasible'] else 'x',s=75)
                ax.annotate(f'{arm} R{r["round"]}',(r['latency_ns'],r['dense_equivalent_tops_per_w']),xytext=((8,12+18*(r['round']-1)) if arm=='critic' else (8,-18-18*(r['round']-1))),textcoords='offset points',fontsize=8)
        for r in front:ax.scatter(r['latency_ns'],r['dense_equivalent_tops_per_w'],s=180,facecolors='none',edgecolors='black',linewidths=1.5)
        ax.set(xlabel='Latency (ns) — lower is better',ylabel='Energy efficiency (dense-equivalent TOPS/W) ↑',title=backend+'\nObserved Pareto points circled')
        ax.grid(alpha=.2);ax.margins(x=.4,y=.35)
    fig.tight_layout();fig.savefig(out/'latency_energy_efficiency.png',dpi=180);fig.savefig(out/'latency_energy_efficiency.pdf');plt.close(fig)
    lines=['# Critic 生成对照：Latency–Energy Efficiency','',
        '两组使用相同起始源码、任务输入和约束，各最多 3 轮（第 1 轮为基线重新验证与测量）。实际调用次数另列，不把相同轮数等同于相同 token/时间成本。',
        '此处是单次匹配起点的先导对照，不是多 seed 统计消融。所有点均由真实生成 RTL 的独立 E2E/PPA 得到。',
        '', 'Energy Efficiency 使用固定 query/J；附列 dense-equivalent TOPS/W，QK+AV 按每 MAC 两个操作计算，threshold 任务每 query 固定 24 ops，不按实际稀疏执行次数修改分子。',
        '能量口径仍为工具建模功耗 × 单次查询延迟，不是芯片实测或饱和流水吞吐下的能效。预布局与布局布线结果分开比较。','',
        '| Backend | Arm | Round | Config | E2E latency ns | Energy efficiency Gqueries/J | Dense-equiv TOPS/W | Area µm² | Power mW | Feasible |',
        '|---|---|---:|---|---:|---:|---:|---:|---:|---|']
    for r in rows:lines.append(f'| {r["backend"]} | {r["arm"]} | {r["round"]} | {r["config"]} | {r["latency_ns"]:.5g} | {r["efficiency_gqueries_per_j"]:.6g} | {r["dense_equivalent_tops_per_w"]:.6g} | {r["area_um2"]:.6g} | {r["power_mw"]:.6g} | {r["feasible"]} |')
    lines+=['','![Latency–Energy Efficiency](latency_energy_efficiency.png)','']
    for backend,front in fronts.items():lines += [f'{backend} 观测到的 Pareto 集合：'+', '.join(f'{r["arm"]} R{r["round"]}' for r in front)+'。只有一个非支配点时也如实保留，不人为制造权衡曲线。','']
    for arm,r in runs.items():lines += [f'{arm}：状态 `{r["status"]}`，错误 `{r["error"]}`，调用次数 `{r["agent_calls"]}`。','']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(out/'RESULTS.md')

if __name__=='__main__':main()
