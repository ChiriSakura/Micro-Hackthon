#!/usr/bin/env python3
"""Post-run RQ1 evaluation; no LLM calls and no feedback into the search."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.artifacts import create_archive
from fast.fullstack.library import Library, save, digest
from fast.fullstack.recovery import read_summary
from report_generated_run import report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--tool-root', type=Path, required=True)
    p.add_argument('--holdout-seed', type=int, default=20260916)
    p.add_argument('--holdout-count', type=int, default=4096)
    args = p.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    run = args.run.resolve()
    result = {'run': str(run), 'status': 'aborted_without_summary', 'rounds': [], 'qualified_pareto_rounds': []}
    summary = read_summary(run)
    if summary['rounds']:
        task = json.loads((run / 'task.json').read_text())
        if args.holdout_seed in task.get('quality_validation_seeds', []):
            raise ValueError('Final holdout seed must differ from selection-validation seeds')
        report(run, out / 'measurements')
        result['summary_recovered'] = not (run/'summary.json').exists()
        result.update(algorithm=task['algorithm'], status=summary['status'], error=summary.get('error'),
                      agent_calls=summary['agent_calls'], search_pareto_rounds=summary['pareto_rounds'])
        library = Library(args.catalog, out / 'holdout_library')
        inventory = json.loads((run/'library_manifest.json').read_text())
        key = 'algorithm:'+task['algorithm']
        if (library.files[key]['sha256'] != inventory['files'][key]['sha256']
                or digest(Path(inventory['files'][key]['snapshot'])) != inventory['files'][key]['sha256']):
            raise ValueError('Final evaluation algorithm differs from frozen run')
        if summary.get('reference_integrity') is False:
            raise ValueError('Cannot qualify a run with failed reference integrity')
        algorithm = library.algorithm(task['algorithm'])
        for record in summary['rounds']:
            if 'config' not in record:
                continue
            heldout = algorithm.measure(record['config'], args.holdout_seed, args.holdout_count, boundaries=False)
            row = {'round': record['round'], 'config': record['config'], 'calibration': record.get('profile'),
                   'heldout': heldout, 'evaluation': record.get('evaluation'), 'status': record['status'],
                   'critique': record.get('critique'), 'critique_applied': record.get('critique_applied', False)}
            result['rounds'].append(row)
            save(out / 'results.json', result)
            if record['round'] not in summary['pareto_rounds']:
                continue
            checks = {}
            common = ['--run', str(run), '--round', str(record['round']), '--catalog', str(args.catalog),
                      '--tool-root', str(args.tool_root)]
            scripts = Path(__file__).parent
            commands = {
                'gates': [sys.executable, str(scripts / 'verify_routed_design.py'), *common],
                'rtl_holdout': [sys.executable, str(scripts / 'verify_generated_holdout.py'), *common,
                    '--seeds', '101', '211', '307', '401', '503', '--ppa-backend', 'yosys_opensta', '--timeout', '900']}
            for name, command in commands.items():
                dest = out / f'{name}_round_{record["round"]}'
                try:
                    proc = subprocess.run([*command, '--output', str(dest)], capture_output=True, text=True, timeout=2400)
                    (out / f'{name}_round_{record["round"]}.log').write_text(proc.stdout + proc.stderr)
                    checks[name] = {'returncode': proc.returncode, 'passed': False}
                    if (dest / 'summary.json').exists():
                        checks[name]['summary'] = json.loads((dest / 'summary.json').read_text())
                        checks[name]['passed'] = proc.returncode == 0 and checks[name]['summary']['passed']
                except (OSError, subprocess.TimeoutExpired) as exc:
                    checks[name] = {'passed': False, 'error': str(exc)}
                row['independent_checks'] = checks
                save(out / 'results.json', result)
            qualified = (heldout['quality_loss'] <= task['constraints']['max_quality_loss'] and heldout['sparsity'] > 0
                         and all(c['passed'] for c in checks.values()))
            row['independently_qualified'] = qualified
            if qualified:
                result['qualified_pareto_rounds'].append(record['round'])
        library.check()
    usage = []
    for path in sorted((run / 'agent_calls').rglob('*.json')):
        call = json.loads(path.read_text())
        usage.append({'path': str(path.relative_to(run)), **{key: call.get(key) for key in
            ('role', 'success', 'wall_seconds', 'usage', 'error')}})
    result['call_costs'] = usage
    result['token_totals'] = {key: sum((c.get('usage') or {}).get(key) or 0 for c in usage)
                             for key in ('prompt_token_count', 'candidates_token_count', 'thoughts_token_count', 'total_token_count')}
    result['calls_missing_usage'] = sum(c.get('usage') is None for c in usage)
    save(out / 'results.json', result)
    if run.exists():
        save(out / 'archive_verification.json', create_archive({'run': run}, out / 'artifacts.tar.gz'))
    print(json.dumps({'status': result['status'], 'qualified': result['qualified_pareto_rounds']}))


if __name__ == '__main__':
    main()
