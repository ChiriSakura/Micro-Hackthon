"""Bounded hardware re-entry after independent scheduler validation rejects a front.

Reuse the measured algorithm's quality evidence, show actual STA failures to the
LLM, then independently validate its NEW hardware proposals. Never patch a queue
depth or a clock by hand. This verifies a subsystem, not full-attention PPA.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
import time
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fast.experiments.critic_ablation import (RecordingLLM, LocalRandomCritic, atomic_json,
    without_independent_feedback, copy_cached_workload)
from fast.adapters.dynax import _dataset_flag
from fast.agents.codesign import CoDesignPoint, CoDesignSpace, estimate, violations
from fast.agents.cooptimizer import CoDesignResult, RandomProposer
from fast.agents.rediscovery_critic import CriticGuidedProposer, build_search_critic, read_validation_evidence
from fast.agents.plan_proposers import LLMPlanProposer
from fast.agents.templates import TemplateRegistry
from fast.schemas.conversions import kernel_result_from_measurement
from fast.schemas.contract import parse_algorithm
from fast.schemas.models import ArchSpecs, Budget, ExperimentSpec, digest_json, kernel_measurement_from_dict


class FeedbackLLM:
    def __init__(self, delegate, feedback):
        self.delegate, self.feedback = delegate, feedback

    def prompt(self, prompt):
        return self.delegate.prompt(prompt + "\nIndependent validation overrides the model's "
            "frequency predictions. Review the following latest observed outcomes. "
            "Propose new legal hardware parameters; preserve the measured algorithm and "
            "quality contract. Avoid repeating failed or already evaluated designs. "
            "Only independent validation can accept a repair.\n" + json.dumps(self.feedback))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--dynax-python', required=True)
    p.add_argument('--gcp-project')
    p.add_argument('--method', choices=['llm', 'random'], default='llm')
    p.add_argument('--gcp-location', default='us-central1')
    p.add_argument('--llm-model', default='gemini-2.5-pro')
    p.add_argument('--containers', type=Path, required=True)
    p.add_argument('--liberty', type=Path, required=True)
    p.add_argument('--budget', type=int, default=4)
    p.add_argument('--critic', choices=['auto', 'rule', 'llm', 'off'], default='auto')
    p.add_argument("--seed", type=int)
    p.add_argument("--max-loops", type=int, default=5)
    p.add_argument("--ablation", choices=["none", "shadow", "no_independent", "local_random"], default="none")
    p.add_argument("--workload-cache", type=Path)
    args = p.parse_args()
    started = time.monotonic()
    if not 0 < args.max_loops <= 5:
        p.error("max-loops must be between 1 and 5")
    if not 0 < args.budget <= 8:
        p.error('bounded re-entry permits 1 to 8 new hardware evaluations')
    critic_mode = ('llm' if args.method == 'llm' else 'rule') if args.critic == 'auto' else args.critic
    if (args.method == 'llm' or critic_mode == 'llm') and not args.gcp_project:
        p.error('LLM re-entry requires --gcp-project')
    parent_raw = (args.source/'search.json').read_bytes()
    source = json.loads(parent_raw)
    failures = []
    for path in sorted((args.source/'candidates').glob('*/rtl/validation.json')):
        data = json.loads(path.read_text())
        if data.get('design_id') != path.parent.parent.name:
            continue
        for result in data['results']:
            if not result['passed'] or not result['frequency_feasible']:
                failures.append({'design_id': data['design_id'], 'scope': data['scope'],
                    'metrics': result['metrics'], 'function_passed': result['passed'],
                    'frequency_feasible': result['frequency_feasible'],
                    'log_uri': str(path)})
    if not failures:
        p.error('no independently rejected candidate to refine')
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/'parent_search.json').write_bytes(parent_raw)
    failed_ids = {f['design_id'] for f in failures}
    parent = next(d for d in source['frontier'] if d['design_id'] in failed_ids)
    label = parent['label']
    measurement = kernel_measurement_from_dict(next(m for m in source['measurements'] if m['label'] == label))
    task, config = source['config']['task'], source['config']
    if not measurement.within or not math.isfinite(measurement.quality_loss) or measurement.quality_loss > task['epsilon']:
        p.error('parent algorithm does not have passing quality evidence')
    kernel = kernel_result_from_measurement(None, measurement)
    contract = parse_algorithm(label)
    specs = ArchSpecs(**config['constraints'])
    space = CoDesignSpace(**{k: tuple(v) for k, v in config['hardware_space'].items()})
    history = tuple(CoDesignResult(CoDesignPoint(**d['point']), None, None, d['metrics'],
        d['feasible'] and d['design_id'] not in failed_ids) for d in source['designs'] if d['label'] == label)
    model_history = tuple(CoDesignResult(CoDesignPoint(**d['point']), None, None, d['metrics'],
        d['feasible'], tuple(d.get('analytical_violations', ()))) for d in source['designs'] if d['label'] == label)
    seed = args.seed if args.seed is not None else 1000+source['search_seed']
    random = RandomProposer(seed)
    api = {}
    llm = None
    if args.method == 'llm' or critic_mode == 'llm':
        from fast.agents.llm_backends import VertexDirect
        llm = VertexDirect(model=args.llm_model, project=args.gcp_project,
                          location=args.gcp_location, temperature=.2, timeout_seconds=180,
                          system_message='Repair a hardware configuration using independent tool failures.')
    if args.method == 'llm':
        api['proposer'] = RecordingLLM(llm, 'proposer', args.out)
        proposer = LLMPlanProposer(FeedbackLLM(api['proposer'], failures), model_name=args.llm_model,
                                  fallback=random, calibration_hints=False)
    else:
        proposer = random
    if critic_mode == 'llm':
        api['critic'] = RecordingLLM(llm, 'critic', args.out)
    critic = (LocalRandomCritic(seed) if args.ablation == 'local_random' else
        build_search_critic(critic_mode, llm=api.get('critic'), model_name=args.llm_model, specs=specs))
    spec = ExperimentSpec(experiment_id='dynax-critic-repair', candidate_id=parent['design_id'],
        model=task['model'], dataset=task['dataset'], sequence_length=task['sequence_length'],
        sparsity_x=contract.kept_low, sparsity_m=contract.block_m,
        epsilon=task['epsilon'], seed=task['data_seed'],
        budget=Budget(max_candidates=args.budget, max_evaluations=args.budget))
    reviews = []
    parent_observations = [f for f in failures if f['design_id'] == parent['design_id']]
    guided = CriticGuidedProposer(proposer, critic, spec, reviews,
                                  validation=parent_observations, parent_point=parent['point'],
        context_filter=(lambda c: without_independent_feedback(c, model_history)) if args.ablation == 'no_independent' else None,
        apply_interventions=args.ablation != 'shadow')
    current_parent = parent
    current_verified = False
    result = {'parent_search_sha256': hashlib.sha256(parent_raw).hexdigest(),
              'algorithm': label, 'quality_loss': measurement.quality_loss,
              'independent_feedback': failures, 'budget': args.budget,
              'method': args.method, 'critic_mode': critic_mode, 'ablation': args.ablation,
              'seed': seed, 'max_loops': args.max_loops, 'critic_reviews': reviews,
              'parent_point': parent['point'], 'state': 'running', 'best_verified_design_id': None,
              'llm_seed_supported': False, 'continue_after_success': True,
              'llm_successful_batches': getattr(proposer, 'llm_batches', 0),
              'fallback_batches': getattr(proposer, 'fallback_batches', 0),
              'calls': getattr(proposer, 'calls', []), 'rejections': getattr(proposer, 'rejected', []), 'candidates': [],
              'evidence_scope': 'scheduler functional/STA repair; not full-attention energy/PPA'}
    def save():
        result.update(critic_calls=getattr(critic, 'search_calls', []),
                      llm_successful_batches=getattr(proposer, 'llm_batches', 0),
                      fallback_batches=getattr(proposer, 'fallback_batches', 0),
                      calls=getattr(proposer, 'calls', []), rejections=getattr(proposer, 'rejected', []))
        result.update(wall_seconds=time.monotonic()-started, api_calls={k:v.calls for k,v in api.items()})
        atomic_json(args.out/'refinement.json', result)
    save()
    for iteration in range(min(args.budget, args.max_loops)):
        loop_started = time.monotonic()
        result["active_loop"] = iteration+1
        save()
        print(f"Critic repair iteration {iteration+1}/{args.budget}", flush=True)
        points = guided.propose(kernel, specs, space, history, 1)
        if not points:
            result['stopped_because'] = 'no new legal proposal'
            break
        proposal_seconds = time.monotonic()-loop_started
        point = points[0]
        applied_review = guided.pending[0] if guided.pending else None
        metrics = estimate(point, kernel, task['sequence_length'], head_dim=task['head_dim'],
                           block_m=contract.block_m, kept_per_block=contract.sizing_kept)
        problems = violations(point, kernel, specs, TemplateRegistry(), head_dim=task['head_dim'],
                              block_m=contract.block_m, kept_per_block=contract.sizing_kept)
        design = {'design_id': digest_json({'parent': parent['design_id'], 'point': asdict(point)}),
                  'label': label, 'algorithm': asdict(contract), 'point': asdict(point),
                  'task': task, 'quality_loss': measurement.quality_loss, 'metrics': metrics,
                  'analytical_violations': problems, 'module_verified': False,
                  'parent_design_id': current_parent['design_id'], 'iteration': iteration,
                  'proposal_seconds': proposal_seconds,
                  'critic_review_id': applied_review['review_id'] if applied_review else None}
        history += (CoDesignResult(point, None, None, metrics, not problems, tuple(problems)),)
        model_history += (history[-1],)
        guided.observe(history)
        result['candidates'].append(design)
        # Persist the analysis and executed model evaluation before expensive
        # capture/RTL tools; a timeout must not erase the Critic's audit trail.
        save()
        if problems:
            design.update(wall_seconds=time.monotonic()-loop_started, state="analytical_rejection")
            save()
            continue
        directory = args.out/design['design_id']
        directory.mkdir()
        (directory/'design.json').write_text(json.dumps(design, indent=2))
        capture = [args.dynax_python, str(ROOT.parent/'DynaX/capture_row_workload.py'),
            '--model', task['model'], '--dataset', _dataset_flag(task['dataset']),
            '--layer', str(task['capture_layer']), '--head', str(task['capture_head']),
            '--seq-len', str(task['sequence_length']), '--seed', str(task['data_seed']),
            '--methods', label, '--rows', str(point.num_rows), '--block', str(contract.block_m),
            '--device', 'cpu', '--max-tiles', str(task['sequence_length']**2),
            '--out', str(directory/'workload.json')]
        validate = [sys.executable, str(ROOT/'scripts/validate_pareto_scheduler.py'),
            '--design', str(directory/'design.json'), '--workload', str(directory/'workload.json'),
            '--tile-offset', '0', '--tile-count', '0', '--out', str(directory/'rtl'),
            '--frequency-mhz', str(specs.target_mhz), '--containers', str(args.containers),
            '--liberty', str(args.liberty)]
        design['stages'] = []
        for name, command in [('capture', capture), ('validate', validate)]:
            stage_started = time.monotonic()
            stage = {'stage': name, 'state': 'running', 'command': command}
            design['stages'].append(stage)
            save()
            try:
                if name == 'capture' and args.workload_cache:
                    stage['trace_reuse'] = copy_cached_workload(args.workload_cache, design, directory/'workload.json')
                    stage['command'] = None
                    code = 0
                else:
                    with (directory/f'{name}.log').open('w') as log:
                        done = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=900)
                    code = done.returncode
            except Exception as exc:
                code = -1
                stage['error'] = f'{type(exc).__name__}: {exc}'
            stage.update(exit_code=code, state='finished', wall_seconds=time.monotonic()-stage_started)
            save()
            if code:
                break
        verified, observations = read_validation_evidence(
            directory/'rtl/validation.json', design['design_id'], specs.target_mhz)
        design['module_verified'] = verified and len(design['stages']) == 2 and all(s['exit_code'] == 0 for s in design['stages'])
        design['independent_observations'] = observations
        manifest_path = directory/'rtl/validation.json'
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            design['independent_results'] = manifest['results']
            design['validation_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if design['module_verified']:
            latency = sum(r['latency_s'] for r in design['independent_results'])
            power = [r['metrics'].get('estimated_power_mw') for r in design['independent_results']]
            design['scheduler_latency_s'] = latency
            design['scheduler_uniform_activity_energy_j'] = (sum(r['latency_s']*p*.001
                for r,p in zip(design['independent_results'],power)) if all(p is not None for p in power) else None)
            incumbent = next((d for d in result['candidates'] if d['design_id'] == result['best_verified_design_id']), None)
            if incumbent is None or latency < incumbent['scheduler_latency_s']:
                result['best_verified_design_id'] = design['design_id']
        design.update(wall_seconds=time.monotonic()-loop_started, state='finished')
        # Rejected independent observations override feasibility for subsequent
        # proposals; retain the original model metrics with their L1 scope.
        if not design['module_verified']:
            history = history[:-1] + (CoDesignResult(point, None, None, metrics, False,
                ('independent scheduler validation rejected this point',)),)
        if applied_review:
            applied_review['outcome'].update(
                independent_module_verified=design['module_verified'],
                independent_observations=observations,
                independent_constraint_recovered=bool(design['module_verified'] and not current_verified
                    and any(v.get('frequency_feasible') is False or v.get('function_passed') is False
                            for v in guided.validation)),
                independent_improvement=None,
                independent_energy_improvement=None,
                independent_scope='scheduler only; constraint recovery is not a whole-task Pareto gain')
        guided.validation = observations
        if isinstance(getattr(proposer, 'llm', None), FeedbackLLM):
            proposer.llm.feedback = observations
        guided.parent_point = asdict(point)
        current_parent, current_verified = design, design['module_verified']
        save()
        print(f"refinement {design['design_id'][:12]}: module_verified={design['module_verified']}", flush=True)
    result['state'] = 'finished'
    result['loops_completed'] = len(result['candidates'])
    result['evaluated'] = len(result['candidates'])
    result['budget_complete'] = result['evaluated'] == args.budget
    result.setdefault('stopped_because', 'budget exhausted')
    save()
    return 0 if any(d['module_verified'] for d in result['candidates']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
