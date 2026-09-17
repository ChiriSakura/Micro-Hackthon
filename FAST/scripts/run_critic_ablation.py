"""Run one preregistered Critic ablation cell; use a scheduler array for the grid."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fast.experiments.critic_ablation import atomic_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study', type=Path, required=True)
    p.add_argument('--index', type=int, required=True)
    p.add_argument('--dynax-python', required=True)
    p.add_argument('--containers', required=True)
    p.add_argument('--liberty', required=True)
    p.add_argument('--gcp-project', required=True)
    args = p.parse_args()
    protocol = json.loads((args.study/'protocol.json').read_text())
    cell = protocol['runs'][args.index]
    out = args.study/'runs'/cell['id']
    out.parent.mkdir(exist_ok=True)
    command = [sys.executable, str(ROOT/'scripts/refine_rediscovery.py'),
        '--source', str(args.study/'prepared'/cell['case']), '--out', str(out),
        '--workload-cache', str(args.study/'prepared/workloads'),
        '--method', cell['proposer'], '--critic', cell['critic'], '--ablation', cell['ablation'],
        '--seed', str(cell['seed']), '--budget', '5', '--max-loops', '5',
        '--dynax-python', args.dynax_python, '--containers', args.containers,
        '--liberty', args.liberty, '--gcp-project', args.gcp_project]
    record = dict(cell=cell, command=command, state='running')
    logdir = args.study/'execution'; logdir.mkdir(exist_ok=True)
    atomic_json(logdir/f'{cell["id"]}.json', record)
    started = time.monotonic()
    with (logdir/f'{cell["id"]}.log').open('w') as log:
        done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    record.update(exit_code=done.returncode, wall_seconds=time.monotonic()-started, state='finished')
    path = out/'refinement.json'
    result = json.loads(path.read_text()) if path.exists() else {}
    complete = result.get('state') == 'finished' and result.get('loops_completed') == 5
    record['complete'] = complete
    atomic_json(logdir/f'{cell["id"]}.json', record)
    return 0 if complete else 2

if __name__ == '__main__':
    raise SystemExit(main())
