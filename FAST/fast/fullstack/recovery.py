"""Read durable run evidence and fork recovery without changing the original run."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

from .contracts import SystemPlan, pareto
from .library import digest, save


def read_summary(run):
    run = Path(run)
    path = run/'summary.json'
    summary = json.loads(path.read_text()) if path.exists() else {
        'status': 'interrupted_without_summary', 'error': 'No final summary; recovered durable round records',
        'reference_integrity': None, 'agent_calls': {}, 'rounds': []}
    records = {r['round']: r for r in summary.get('rounds', [])}
    for path in sorted(run.glob('round_*/result.json')):
        record = json.loads(path.read_text())
        records[record['round']] = record
    summary['rounds'] = [records[n] for n in sorted(records)]
    summary['pareto_rounds'] = pareto(summary['rounds'])
    return summary


def check_inventory(run, record):
    for field in ('sources', 'rtl_sources'):
        for relative, sha in record.get(field, {}).items():
            path = (run/relative).resolve(strict=True)
            if not path.is_relative_to(run) or digest(path) != sha:
                raise ValueError(f'Recovery source integrity failed: {relative}')


def legacy_pending_record(run, contract):
    """Migrate an old accepted assembly interrupted before the PPA record was saved.

    Requires explicit assembly acceptance and each source hash; does NOT infer
    E2E/PPA success from filenames. The resumed flow always reruns trusted E2E.
    """
    events = json.loads((run/'events.json').read_text())
    starts = [i for i, e in enumerate(events) if e['stage'] == 'round_start']
    if not starts:
        return None
    tail = events[starts[-1]:]
    number = tail[0]['round']
    if (run/f'round_{number:02d}/result.json').exists():
        return None
    accepts = [e for e in tail if e['stage'] == 'assembly_accepted']
    profiles = [e for e in tail if e['stage'] == 'kernel_profile']
    if not accepts or not profiles:
        raise ValueError('Old interrupted run lacks a recoverable accepted assembly/profile')
    accepted = accepts[-1]
    candidates = []
    for path in (run/f'round_{number:02d}').glob('build_*/system_plan.json'):
        raw = json.loads(path.read_text())
        if raw['top'] != accepted['module']:
            continue
        plan = SystemPlan.parse(raw, contract['ports'])
        work = path.parent
        suffix = '.scala' if plan.language == 'chisel' else '.v'
        sources, implementations = {}, {}
        for m in plan.modules:
            source = work/m.name/(m.name+suffix)
            info = json.loads((source.parent/'implementation.json').read_text())
            if digest(source) != info['source_sha256']:
                raise ValueError('Old accepted module source changed')
            sources[str(source.relative_to(run))] = digest(source)
            implementations[m.name] = info
        if implementations[plan.top]['source_sha256'] != accepted['source_sha256']:
            continue
        gates = [json.loads(p.read_text()) for p in sorted((work/plan.top).glob('check_*.json'))]
        passed = [g for g in gates if g.get('passed')]
        if not passed:
            raise ValueError('Accepted assembly has no passing compilation record')
        rtl = [Path(passed[-1]['elaborated_verilog'])] if plan.language == 'chisel' else [run/s for s in sources]
        candidates.append({'round': number, 'status': 'ppa_pending', 'reentry': tail[0]['reentry'],
            'config': profiles[-1]['choice']['config'], 'profile': profiles[-1]['profile'],
            'system_plan': raw, 'sources': sources, 'implementations': implementations,
            'rtl_sources': {str(p.relative_to(run)): digest(p) for p in rtl},
            'migration': 'Legacy accepted assembly; E2E must be freshly verified before PPA'})
    if len(candidates) != 1:
        raise ValueError('Cannot uniquely recover old accepted assembly')
    return candidates[0]


def fork_run(flow, original):
    original = original.resolve(strict=True)
    task = json.loads((original/'task.json').read_text())
    # Execution/recovery budgets may change; the scientific contract may not.
    from dataclasses import asdict
    current = asdict(flow.task)
    for field in ('algorithm', 'constraints', 'seed', 'activity', 'ppa_backend',
                  'quality_validation_seeds', 'quality_validation_samples', 'quality_margin'):
        old = task.get(field, [] if field == 'quality_validation_seeds' else current[field])
        if json.dumps(old, sort_keys=True) != json.dumps(current[field], sort_keys=True):
            raise ValueError(f'Resume changes scientific task field: {field}')
    manifest = json.loads((original/'library_manifest.json').read_text())
    for key, item in manifest['files'].items():
        if key not in flow.library.files or flow.library.files[key]['sha256'] != item['sha256']:
            raise ValueError(f'Resume library differs: {key}')
        if digest(Path(item['snapshot'])) != item['sha256']:
            raise ValueError(f'Original reference snapshot changed: {key}')
    summary = read_summary(original)
    if summary.get('reference_integrity') is False:
        raise ValueError('Cannot resume a reference-integrity failure')
    pending = legacy_pending_record(original, flow.contract)
    records = summary['rounds'] + ([pending] if pending else [])
    if not records:
        raise ValueError('No durable round evidence to resume')
    for record in records:
        check_inventory(original, record)
    def rebase(value):
        if isinstance(value, str): return value.replace(str(original), str(flow.workspace))
        if isinstance(value, list): return [rebase(x) for x in value]
        if isinstance(value, dict): return {rebase(k): rebase(v) for k, v in value.items()}
        return value
    # No hardlinks: later writes cannot mutate the original evidence.
    ignore = shutil.ignore_patterns('obj_dir', '.scala-build', '.bsp', '__pycache__', 'latest')
    for folder in [*sorted(original.glob('round_*')), original/'agent_calls']:
        if folder.is_dir():
            target = flow.workspace/folder.name
            shutil.copytree(folder, target, ignore=ignore, symlinks=True)
            # Rebase structured paths, retaining raw logs/prompts in original archive.
            for path in target.rglob('*.json'):
                if path.is_symlink(): continue
                value = json.loads(path.read_text())
                mapped = rebase(value)
                if mapped != value: save(path, mapped)
    flow.records = rebase(deepcopy(records))
    flow.events = rebase(json.loads((original/'events.json').read_text()))
    for agent in flow.agents.values():
        calls = list((flow.workspace/'agent_calls'/agent.role).glob('*.json'))
        agent.calls = max((int(p.stem) for p in calls if p.stem.isdigit()), default=0)
    survey = original/'kernel_survey.json'
    if survey.exists():
        data = json.loads(survey.read_text())
        save(flow.workspace/'kernel_survey.json', data)
        for profile in data.get('profiles', []):
            flow.profile_cache[json.dumps(profile['config'], sort_keys=True)] = profile
    for record in flow.records:
        record.setdefault('provenance', {'imported_from': str(original), 'round': record['round'],
                                        'historical_measurement': bool(record.get('evaluation'))})
        save(flow.workspace/f'round_{record["round"]:02d}'/'result.json', record)
        if flow.task.reuse_verified_modules and record.get('sources'):
            plan = SystemPlan.parse(record['system_plan'], flow.contract['ports'])
            modules = {m.name: m for m in plan.modules}
            paths = {Path(p).stem: flow.workspace/p for p in record['sources']}
            def closure(name):
                result = set()
                for dep in modules[name].dependencies:
                    result.add(dep); result.update(closure(dep))
                return result
            for module in plan.modules:
                if module.name == plan.top: continue
                deps = closure(module.name)
                refs = flow.library.plan_sources(plan, {module.name, *deps})
                key = json.dumps({'language': plan.language, 'config': record['config'],
                    'module': asdict(module), 'dependencies': {n: digest(paths[n]) for n in deps},
                    'library': {str(p): digest(p) for p in refs}}, sort_keys=True)
                flow.verified_module_cache[key] = {'path': paths[module.name], 'sha256': digest(paths[module.name])}
    save(flow.workspace/'recovery_origin.json', {'original_run': str(original),
        'original_task': task, 'original_summary_status': summary['status'],
        'original_record_sha256': {str(p.relative_to(original)): digest(p)
                                  for p in original.glob('round_*/result.json')},
        'migration_of_pending_round': pending['round'] if pending else None,
        'policy': 'Preserve completed measurements as historical evidence; resume remaining candidate budget'})
    flow.event('resume_import', original_run=str(original), rounds=[r['round'] for r in records])
