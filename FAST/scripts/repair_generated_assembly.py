#!/usr/bin/env python3
"""Explicitly assisted assembly repair; never counted as an autonomous run.

Rebuild immutable accepted children from a failed build, give an assembly UArch
the supplied diagnosis, and independently verify the resulting system and PPA.
"""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.agents.llm_backends import VertexDirect
from fast.fullstack.contracts import SystemPlan, Task, pareto
from fast.fullstack.dispatch import DesignDispatcher, check_accepted
from fast.fullstack.flow import FullStackFlow
from fast.fullstack.library import digest, save
from fast.fullstack.tools import RtlTools


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--build', required=True, help='Run-relative failed build directory')
    p.add_argument('--previous-top', type=Path, required=True, help='Immutable prior attempt file')
    p.add_argument('--diagnosis', type=Path, required=True)
    p.add_argument('--catalog', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--tool-root', type=Path, required=True)
    p.add_argument('--project', required=True)
    p.add_argument('--tool-timeout', type=int, default=7200)
    p.add_argument('--critic', choices=('on', 'off'), default='on',
                   help='Analyze the measured repair; recommendations do not add design candidates')
    args = p.parse_args()
    original = args.run.resolve(); old = (original / args.build).resolve()
    if not old.is_relative_to(original):
        raise ValueError('Build must be inside the original run')
    task = Task.parse(json.loads((original / 'task.json').read_text()))
    task = replace(task, max_loops=1, min_loops=1,
        prompt=task.prompt + '\nThis is a separately recorded, externally diagnosed assembly repair. '
        'The previous accepted implementation and system plan are supplied intentionally. '
        'Preserve the algorithm contract, configuration and accepted child interfaces.')
    llm = VertexDirect(model='gemini-2.5-pro', project=args.project,
                       location='us-central1', timeout_seconds=600, max_output_tokens=48000)
    tools = RtlTools(args.tool_root, args.tool_timeout)
    flow = FullStackFlow(task, args.catalog, args.output, llm, tools, critic_enabled=args.critic == 'on')
    manifest = json.loads((original / 'library_manifest.json').read_text())
    if {k: v['sha256'] for k, v in flow.library.files.items()} != {
            k: v['sha256'] for k, v in manifest['files'].items()}:
        raise ValueError('Use the complete frozen library from the failed run')
    plan = SystemPlan.parse(json.loads((old / 'system_plan.json').read_text()), flow.contract['ports'])
    context = json.loads((old / plan.top / 'job.json').read_text())
    config = context['config']; profile = flow.measured_profile(config)
    diagnosis = args.diagnosis.read_text()
    provenance = {'scope': 'external-diagnosis-assisted assembly repair, not autonomous generation',
                  'original_run': str(original), 'original_build': args.build,
                  'diagnosis': diagnosis, 'diagnosis_sha256': digest(args.diagnosis),
                  'previous_top_sha256': digest(args.previous_top), 'measurements_reused': False}
    save(flow.workspace / 'repair_provenance.json', provenance)
    round_dir = flow.workspace / 'round_01'; round_dir.mkdir()
    work = round_dir / 'build_01'; work.mkdir()
    save(work / 'system_plan.json', asdict(plan))
    advice = {'layer': 'uarch', 'instructions': diagnosis,
              'origin': 'external diagnosis, not the original Critic'}
    dispatcher = DesignDispatcher(flow, plan, work, profile, config, advice,
                                  {plan.top: args.previous_top.read_text()})
    record = {'round': 1, 'reentry': 'assisted_assembly_repair', 'config': config,
              'profile': profile, 'system_plan': asdict(plan), 'status': 'running'}
    flow.records = [record]

    def persist(status='running', error=None):
        summary = flow.persist(status, error)
        summary['evidence_scope'] = provenance['scope']
        save(flow.workspace / 'summary.json', summary)
        return summary

    persist()
    status, error = 'failed', None
    try:
        accepted = {}
        for module in plan.modules:
            if module.name == plan.top:
                continue
            suffix = 'scala' if plan.language == 'chisel' else 'v'
            src = old / module.name / f'{module.name}.{suffix}'
            implementation = json.loads((src.parent / 'implementation.json').read_text())
            if digest(src) != implementation['source_sha256']:
                raise ValueError('Accepted child source identity changed: ' + module.name)
            flow.library.check_generated(src.read_text(), module, plan.language)
            dst = work / module.name / src.name; dst.write_bytes(src.read_bytes()); dst.chmod(0o444)
            check = dst.parent / 'fresh_check'; check.mkdir()
            deps = [accepted[n]['path'] for n in dispatcher.closure(module.name)]
            linked = flow.library.plan_sources(plan, [*dispatcher.closure(module.name), module.name])
            gate = tools.module(module, [*linked, *deps, dst], check, language=plan.language)
            save(dst.parent / 'implementation.json', {**implementation,
                 'scope': 'imported accepted child, freshly rebuilt and checked', 'original_source': str(src)})
            if not gate['passed']:
                raise ValueError('Fresh child verification failed: ' + module.name)
            accepted[module.name] = {'path': dst, 'sha256': digest(dst), 'gate': gate}
            flow.event('repair_child_reverified', module=module.name, source_sha256=digest(dst))
        check_accepted(accepted)
        top = dispatcher.implement(plan.top, accepted, assembly=True)
        check_accepted(accepted)
        sources = [a['path'] for a in accepted.values()] + [top['path']]
        record.update(sources={str(s.relative_to(flow.workspace)): digest(s) for s in sources},
                      rtl_sources={str(s.relative_to(flow.workspace)): digest(s) for s in top['rtl_sources']},
                      implementations={s.stem: json.loads((s.parent / 'implementation.json').read_text()) for s in sources},
                      work=str(work.relative_to(flow.workspace)), verification=top['verification'],
                      status='ppa_pending')
        persist()
        record['evaluation'] = tools.evaluate(plan, top['rtl_sources'], top['verification'], profile, task, work)
        status = ('assisted_repair_complete' if record['evaluation'].get('feasible') else
                  'assisted_repair_infeasible' if record['evaluation']['complete'] else 'ppa_failed')
        record['status'] = 'evaluated' if record['evaluation']['complete'] else 'ppa_failed'
        persist()
        if flow.critic_enabled:
            flow.event('critic', round=1, repair=True)
            record['critique'] = flow.request_critique(record, 1)
            record['critique_applied'] = False
            persist()
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
        record['error'] = error
        if (record.get('evaluation') or {}).get('complete'):
            status = 'repair_measured_with_followup_error'
        elif record.get('sources'):
            status = 'interrupted_with_checkpoint'
        else:
            record['status'] = 'failed'
    flow.library.check()
    summary = persist(status, error)
    print(json.dumps({k: v for k, v in summary.items() if k != 'rounds'}))
    return 0 if summary['pareto_rounds'] and status == 'assisted_repair_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
