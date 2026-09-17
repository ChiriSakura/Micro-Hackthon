import json
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parent
paths = json.loads((root/'paths.json').read_text())
subprocess.run(['squeue','-j',paths['job_id']+','+paths['post_guard_job_id'],'-o','%.18i %.24j %.10T %.12M %.25R'])
run = Path(paths['run'])
if (run/'events.json').exists():
    events = json.loads((run/'events.json').read_text())
    print('Recent events:', [{k:e[k] for k in ('stage','module','attempt','passed') if k in e} for e in events[-5:]])
if (run/'summary.json').exists():
    d=json.loads((run/'summary.json').read_text()); print('Summary:',d['status'],d.get('error'),d.get('pareto_rounds'))
for p in sorted(run.glob('round_*/build_*/hammer/result.json')):
    d=json.loads(p.read_text()); print(str(p.relative_to(run)),{k:d.get(k) for k in ['active_stage','complete','feasible','slack_ns','hold_slack_ns','route_drc_violations','area_um2','power_mw','latency_ns']})
    logs = sorted(p.parent.glob('par-rundir/openroad-*.log'))
    if logs and not d.get('complete'): print('OpenROAD:', '\n'.join(logs[-1].read_text(errors='replace').splitlines()[-4:]))
