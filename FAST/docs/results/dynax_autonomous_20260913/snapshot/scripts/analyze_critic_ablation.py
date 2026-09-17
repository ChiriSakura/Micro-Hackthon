"""Aggregate the preregistered grid without dropping failed/unfinished runs."""
import argparse
import csv
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fast.experiments.critic_ablation import atomic_json


def hypervolume(points, reference):
    """Union of minimizing rectangles, with fixed reference and no per-arm scaling."""
    xref, yref = reference
    height, area = yref, 0.0
    for x,y in sorted(points):
        if 0 <= x < xref and 0 <= y < height:
            area += (xref-x)*(height-y)
            height = y
    return area


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader(); writer.writerows(rows)


def analyze(study, out):
    out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((study/'protocol.json').read_text())
    run_rows, rounds, reviews, audit_errors = [], [], [], []
    raw = {}
    ref = protocol['proxy_hypervolume_reference']
    reference = ref['latency_s'], ref['energy_j']
    for cell in protocol['runs']:
        path = study/'runs'/cell['id']/'refinement.json'
        data = json.loads(path.read_text()) if path.exists() else {}
        raw[cell['id']] = data
        if data:
            source_path = study/'prepared'/cell['case']/'search.json'
            source_data = json.loads(source_path.read_text())
            if data['parent_search_sha256'] != hashlib.sha256(source_path.read_bytes()).hexdigest():
                audit_errors.append(f'{cell["id"]}: parent source mismatch')
            if data['algorithm'] != protocol['algorithm'] or data['quality_loss'] > protocol['epsilon'] or data['seed'] != cell['seed']:
                audit_errors.append(f'{cell["id"]}: fixed algorithm/quality/seed mismatch')
            if cell['arm'] == 'no_independent':
                pure = {json.dumps(d['point'],sort_keys=True):d.get('analytical_violations',[]) for d in source_data['designs']+data['candidates']}
                for review in data['critic_reviews']:
                    ctx = review['context']
                    if ctx['validation'] or any(h['feasible'] != (not pure[json.dumps(h['point'],sort_keys=True)]) for h in ctx['history']):
                        audit_errors.append(f'{cell["id"]}: independent feedback leaked into blind critic')
        run = {**cell, 'state': data.get('state','missing'), 'evaluated': len(data.get('candidates', [])),
               'recovered': False, 'first_verified_loop': None, 'best_latency_us': None,
               'best_design_id': None, 'final_verified': False, 'final_latency_us': None,
               'analytical_rejections': 0, 'independent_attempts': 0, 'independent_function_passes': 0,
               'verified_candidates': 0, 'critic_reviews': len(data.get('critic_reviews', [])),
               'critic_applied': 0, 'critic_fallbacks': 0, 'proposer_fallback_batches': data.get('fallback_batches',0),
               'api_calls': 0, 'api_failed': 0, 'api_wall_seconds': 0.0, 'wall_seconds':data.get('wall_seconds'),
               'proxy_hypervolume_normalized': 0.0}
        points, incumbent = [], None
        previous_signature = tuple(data.get('parent_point',{}).get(k) for k in ('num_rows','pe_per_row','queue_depth'))
        signatures = set()
        for design in data.get('candidates', []):
            verified = design.get('module_verified',False)
            independent = design.get('independent_results', [])
            measurements = independent[0].get('metrics', {}) if independent else {}
            attempts = any(s['stage'] == 'validate' for s in design.get('stages', []))
            latency = design.get('scheduler_latency_s')
            energy = design.get('scheduler_uniform_activity_energy_j')
            signature = tuple(design['point'][k] for k in ('num_rows','pe_per_row','queue_depth'))
            same_scheduler = signature == previous_signature
            previous_signature = signature if attempts else previous_signature
            if attempts: signatures.add(signature)
            rid = design.get('critic_review_id')
            review = next((r for r in data.get('critic_reviews',[]) if r['review_id']==rid),None)
            action = review['critique']['mutations'][0] if review and review['critique']['mutations'] else None
            run['analytical_rejections'] += bool(design.get('analytical_violations'))
            run['independent_attempts'] += attempts
            run['independent_function_passes'] += bool(independent and all(r['passed'] for r in independent))
            run['verified_candidates'] += verified
            run['critic_applied'] += rid is not None
            if verified:
                if run['first_verified_loop'] is None:
                    run['first_verified_loop'] = design['iteration']+1
                if incumbent is None or latency < incumbent['scheduler_latency_s']:
                    incumbent = design
                if energy is not None:
                    points.append((latency,energy))
                validation_path = path.parent/design['design_id']/'rtl/validation.json'
                v = json.loads(validation_path.read_text())
                immutable = path.parent/design['design_id']/'design.json'
                if (not v['sources_unchanged'] or not v['complete_captured_task'] or v['fixed_frequency_mhz'] != 350
                    or v['design_id'] != design['design_id'] or v['design_sha256'] != hashlib.sha256(immutable.read_bytes()).hexdigest()
                    or not all(r['passed'] and r['frequency_feasible'] and r['metrics']['slack_ns'] >= 0 for r in v['results'])):
                    audit_errors.append(f'{cell["id"]}/{design["design_id"]}: verification identity/gate mismatch')
            rounds.append(dict(run_id=cell['id'], case=cell['case'], arm=cell['arm'], seed=cell['seed'],
                loop=design['iteration']+1, design_id=design['design_id'], **design['point'],
                analytical_pass=not design.get('analytical_violations'), analytical_violations=json.dumps(design.get('analytical_violations',[])),
                model_latency_us=design['metrics'].get('seconds',0)*1e6,
                model_energy_uj=design['metrics'].get('energy_j',0)*1e6,
                scheduler_signature=str(signature), same_scheduler_as_previous=bool(attempts and same_scheduler),
                independent_attempted=attempts, function_pass=bool(independent and all(r['passed'] for r in independent)),
                verified=verified, cycles=measurements.get('cycles'), area_um2=measurements.get('area_um2'),
                slack_ns=measurements.get('slack_ns'), max_frequency_mhz=measurements.get('max_frequency_mhz'),
                uniform_activity_power_mw=measurements.get('estimated_power_mw'), assumed_activity=measurements.get('assumed_activity'),
                latency_us=latency*1e6 if latency is not None else None,
                uniform_activity_energy_nj=energy*1e9 if energy is not None else None,
                best_so_far_latency_us=incumbent['scheduler_latency_s']*1e6 if incumbent else None,
                recovered_so_far=incumbent is not None, critic_applied=rid is not None,
                critic_action=f"{action['field']}={action['value']}" if action else None,
                critic_fallback=bool(review and review.get('fallback_reason')),
                proposal_seconds=design.get('proposal_seconds'), wall_seconds=design.get('wall_seconds'),
                proxy_hypervolume_normalized=hypervolume(points,reference)/(reference[0]*reference[1])))
        run['unique_scheduler_signatures_validated'] = len(signatures)
        candidates = data.get('candidates', [])
        if candidates:
            final = candidates[-1]
            run['final_verified'] = final.get('module_verified',False)
            run['final_latency_us'] = final.get('scheduler_latency_s',0)*1e6 if run['final_verified'] else None
        if incumbent:
            run.update(recovered=True,best_latency_us=incumbent['scheduler_latency_s']*1e6,
                best_design_id=incumbent['design_id'], best_point=json.dumps(incumbent['point'],sort_keys=True))
        if data.get('state') == 'finished':
            expected_incumbent = incumbent['design_id'] if incumbent else None
            if data.get('best_verified_design_id') != expected_incumbent:
                audit_errors.append(f'{cell["id"]}: persisted incumbent does not match verified minimum latency')
        for review in data.get('critic_reviews',[]):
            run['critic_fallbacks'] += bool(review.get('fallback_reason'))
            reviews.append(dict(run_id=cell['id'], review_id=review['review_id'],
                phase=review['context']['phase'], decision=review['critique']['decision'],
                summary=review['critique']['summary'], evidence=json.dumps(review['critique']['evidence']),
                mutations=json.dumps(review['critique']['mutations']), fallback_reason=review.get('fallback_reason'),
                outcome=json.dumps(review['outcome'])))
        for role,calls in data.get('api_calls',{}).items():
            run[f'{role}_api_calls'] = len(calls)
            for call in calls:
                run['api_calls'] += 1
                run['api_failed'] += call.get('success') is False
                run['api_wall_seconds'] += call.get('wall_seconds',0)
        run['proxy_hypervolume_normalized'] = hypervolume(points,reference)/(reference[0]*reference[1])
        run_rows.append(run)
    aggregates = []
    groups = defaultdict(list)
    for row in run_rows:
        groups[(row['case'],row['arm'])].append(row)
    for (case,arm), items in groups.items():
        successful = [r for r in items if r['recovered']]
        aggregates.append(dict(case=case,arm=arm,runs=len(items),
            completed=sum(r['state']=='finished' and r['evaluated']==5 for r in items),
            recovered=sum(r['recovered'] for r in items),final_verified=sum(r['final_verified'] for r in items),
            first_loops=[r['first_verified_loop'] for r in items],
            best_latency_us=[r['best_latency_us'] for r in items],
            mean_best_latency_us_successful=statistics.mean(r['best_latency_us'] for r in successful) if successful else None,
            median_first_loop_successful=statistics.median(r['first_verified_loop'] for r in successful) if successful else None,
            evaluated=sum(r['evaluated'] for r in items),independent_attempts=sum(r['independent_attempts'] for r in items),
            verified_candidates=sum(r['verified_candidates'] for r in items),
            mean_wall_seconds=statistics.mean(r['wall_seconds'] for r in items if r['wall_seconds'] is not None) if any(r['wall_seconds'] is not None for r in items) else None,
            api_calls=sum(r['api_calls'] for r in items),api_failed=sum(r['api_failed'] for r in items),
            critic_applied=sum(r['critic_applied'] for r in items),critic_fallbacks=sum(r['critic_fallbacks'] for r in items),
            mean_proxy_hypervolume=statistics.mean(r['proxy_hypervolume_normalized'] for r in items)))
    shadow_pairs = []
    for seed in range(3):
        off, shadow = raw[f'main32_off_s{seed}'],raw[f'main32_shadow_s{seed}']
        a,b=off.get('candidates',[]),shadow.get('candidates',[])
        complete = len(a)==len(b)==5
        same = [d['point'] for d in a] == [d['point'] for d in b]
        shadow_pairs.append(dict(seed=seed,complete=complete,identical_candidates=same,
            identical_verdicts=[d['module_verified'] for d in a]==[d['module_verified'] for d in b]))
        if complete and not same: audit_errors.append(f'shadow pair {seed} diverged')
    source = json.loads((study/'source_manifest.json').read_text())
    snapshot = Path(source['snapshot'])
    changed = [name for name,digest in source['files'].items() if not (snapshot/name).exists()
        or hashlib.sha256((snapshot/name).read_bytes()).hexdigest()!=digest]
    audit_errors.extend('source changed: '+name for name in changed)
    main_runs = [r for r in run_rows if r['case']=='main32']
    if all(r['state']=='finished' for r in main_runs):
        common_k = min(r['independent_attempts'] for r in main_runs)
        matched = []
        for run in main_runs:
            prefix = [r for r in rounds if r['run_id']==run['id'] and r['independent_attempted']][:common_k]
            successful = [r for r in prefix if r['verified']]
            matched.append(dict(run_id=run['id'],arm=run['arm'],seed=run['seed'],
                independent_budget=common_k,recovered=bool(successful),
                best_latency_us=min((r['latency_us'] for r in successful),default=None)))
        atomic_json(out/'equal_rtl_budget_posthoc.json',dict(scope='Post-hoc sensitivity analysis; unchanged primary 5-loop results',
            common_budget=common_k,runs=matched))
    frontier = []
    for row in rounds:
        if not row['verified'] or row['uniform_activity_energy_nj'] is None: continue
        vector = row['latency_us'],row['uniform_activity_energy_nj']
        peers = [r for r in rounds if r['case']==row['case'] and r['verified'] and r['uniform_activity_energy_nj'] is not None]
        if not any(r['latency_us']<=vector[0] and r['uniform_activity_energy_nj']<=vector[1]
            and (r['latency_us']<vector[0] or r['uniform_activity_energy_nj']<vector[1]) for r in peers):
            frontier.append(row)
    atomic_json(out/'scheduler_proxy_frontier.json',frontier)
    result = dict(protocol=protocol,aggregates=aggregates,run_count=len(run_rows),
        all_complete=all(r['state']=='finished' and r['evaluated']==5 for r in run_rows),
        shadow_pairs=shadow_pairs,audit_errors=audit_errors,source_files_checked=len(source['files']),
        source_unchanged=not changed)
    atomic_json(out/'summary.json',result)
    write_csv(out/'runs.csv',run_rows); write_csv(out/'rounds.csv',rounds); write_csv(out/'reviews.csv',reviews)
    atomic_json(out/'runs.json',run_rows)
    return result,run_rows,rounds


def plots(out, summary, runs, rounds):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors=dict(off='#666666',rule='#0072B2',llm='#D55E00',shadow='#9999CC',no_independent='#CC79A7',local_random='#009E73')
    fig, axes = plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,case in zip(axes,['main32','confirm16']):
        arms=[r['arm'] for r in summary['aggregates'] if r['case']==case]
        for arm in arms:
            selected=[r for r in runs if r['case']==case and r['arm']==arm]
            y=[sum(r['first_verified_loop'] is not None and r['first_verified_loop']<=i for r in selected)/len(selected) for i in range(6)]
            ax.plot(range(6),y,'o-',label=arm,color=colors[arm],alpha=.8)
        ax.set(title=case, xlabel='Candidate evaluation / loop', ylabel='Fraction recovered',xticks=range(6),ylim=(-.05,1.05))
        ax.grid(alpha=.2); ax.legend(fontsize=8)
    for suffix in ('png','pdf'): fig.savefig(out/f'recovery.{suffix}',dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,case in zip(axes,['main32','confirm16']):
        for arm in dict.fromkeys(r['arm'] for r in rounds if r['case']==case):
            selected=[r for r in rounds if r['case']==case and r['arm']==arm and r['verified'] and r['uniform_activity_energy_nj'] is not None]
            ax.scatter([r['latency_us'] for r in selected],[r['uniform_activity_energy_nj'] for r in selected],label=arm,color=colors[arm],alpha=.7,s=45)
        ax.set(title=case+' (verified points)',xlabel='Scheduler latency at 350 MHz (µs)',ylabel='Uniform-activity scheduler energy proxy (nJ)')
        ax.grid(alpha=.2); ax.legend(fontsize=8)
    for suffix in ('png','pdf'): fig.savefig(out/f'scheduler_proxy_pareto.{suffix}',dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for ax,metric,ylabel in zip(axes,['best_latency_us','wall_seconds'],['Best verified scheduler latency (µs)','Run wall time (s)']):
        arms=[r['arm'] for r in summary['aggregates'] if r['case']=='main32']
        for i,arm in enumerate(arms):
            selected=[r for r in runs if r['case']=='main32' and r['arm']==arm]
            for r in selected:
                if r[metric] is not None:
                    ax.scatter(i+(r['seed']-1)*.12,r[metric],color=colors[arm],marker=['o','s','^'][r['seed']],s=45)
            values=[r[metric] for r in selected if r[metric] is not None]
            if metric == 'best_latency_us' and len(values) < len(selected):
                ax.annotate(f'{len(selected)-len(values)}/{len(selected)} failed', (i,.90),
                    xycoords=('data','axes fraction'), ha='center', fontsize=9, color=colors[arm])
            if values: ax.plot([i-.3,i+.3],[statistics.mean(values)]*2,color=colors[arm],lw=2)
        ax.set(xticks=range(len(arms)),xticklabels=arms,ylabel=ylabel,title='Main32: points = repeats; line = mean of available values')
        ax.tick_params(axis='x',rotation=25);ax.grid(axis='y',alpha=.2)
    for suffix in ('png','pdf'):fig.savefig(out/f'quality_cost.{suffix}',dpi=180)
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--plots',action='store_true'); args=p.parse_args()
    result,runs,rounds=analyze(args.study,args.out)
    if args.plots: plots(args.out,result,runs,rounds)
    print(json.dumps({k:result[k] for k in ('all_complete','source_unchanged','audit_errors','aggregates')},indent=2))

if __name__=='__main__':main()
