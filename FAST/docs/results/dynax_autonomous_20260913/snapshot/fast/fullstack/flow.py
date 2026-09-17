"""The main library -> Kernel -> Compiler/UArch -> E2E/PPA -> Critic loop."""
from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy
import math
import itertools
import json
import random
import platform
from pathlib import Path
import time
import threading

from .agents import KernelAgent, CompilerAgent, CriticAgent, validate_critique
from .contracts import SystemPlan, Task, pareto
from .library import Library, digest, save
from .dispatch import DesignDispatcher


class FullStackFlow:
    def __init__(self, task: Task, catalog: Path, workspace: Path, llm, tools,
                 *, critic_enabled: bool = True, initial_run: Path | None = None):
        self.task, self.workspace, self.tools = task, workspace.resolve(), tools
        self.workspace.mkdir(parents=True, exist_ok=False)
        self.library = Library(catalog, self.workspace)
        self.algorithm = self.library.algorithm(task.algorithm)
        self.contract = self.algorithm.describe()
        self.agents = {name: cls(llm, name, self.workspace/'agent_calls') for name, cls in (
            ('kernel', KernelAgent), ('compiler', CompilerAgent), ('critic', CriticAgent))}
        self.llm, self.design_agents = llm, []
        self.event_lock = threading.Lock()
        self.critic_enabled = critic_enabled
        self.initial_run = initial_run.resolve() if initial_run else None
        self.records, self.events = [], []
        self.profile_cache = {}
        code_files = list(Path(__file__).parent.glob('*.py')) + [
            Path(__file__).parents[1]/relative for relative in
            ('agents/llm_backends.py', 'adapters/synthesis.py', 'adapters/timing.py')]
        save(self.workspace/'run_metadata.json', {'python': platform.python_version(),
             'code_sha256': {str(p): digest(p) for p in code_files},
             'llm_backend': type(llm).__name__, 'model': getattr(llm, 'model', None),
             'project': getattr(llm, 'project', None), 'location': getattr(llm, 'location', None),
             'temperature': getattr(llm, 'temperature', None),
             'tool_root': str(getattr(tools, 'tool_root', 'test-double'))})
        save(self.workspace/'task.json', asdict(task))
        save(self.workspace/'algorithm_contract.json', self.contract)

    def initial_design(self, round_dir):
        """Fresh verification/PPA of an immutable shared starting design.

        No measurements are imported as this run's evidence. This enables
        matched Critic/no-Critic experiments starting at the SAME RTL.
        """
        from .tools import check_chisel_source, check_source
        run = self.initial_run
        original_task = Task.parse(json.loads((run/'task.json').read_text()))
        manifest = json.loads((run/'library_manifest.json').read_text())
        key = f'algorithm:{self.task.algorithm}'
        if original_task.algorithm != self.task.algorithm or manifest['files'][key]['sha256'] != self.library.files[key]['sha256']:
            raise ValueError('Initial design trusted algorithm identity differs')
        summary = json.loads((run/'summary.json').read_text())
        if not summary.get('reference_integrity'):
            raise ValueError('Initial run reference integrity failed')
        candidates = [r for r in summary['rounds'] if r.get('evaluation', {}).get('feasible')]
        if not candidates:
            raise ValueError('Initial run has no verified feasible design')
        original = candidates[0]  # deliberately fixed baseline, not cherry-picked per arm
        config = original['config']
        profile = self.measured_profile(config)
        plan = SystemPlan.parse(original['system_plan'], self.contract['ports'])
        self.library.check_linked_identity(plan, manifest)
        work = round_dir/'initial_design'; work.mkdir()
        paths = {}
        for name, sha in original['sources'].items():
            path = (run/name).resolve(strict=True)
            if not path.is_relative_to(run) or digest(path) != sha or path.stem in paths:
                raise ValueError(f'Initial generated source integrity failed: {name}')
            paths[path.stem] = path
        if set(paths) != {m.name for m in plan.modules}:
            raise ValueError('Initial source inventory differs from plan')
        sources, accepted = [], {}
        for module in plan.modules:
            folder = work/module.name; folder.mkdir()
            source = paths[module.name].read_text()
            self.library.check_generated(source, module, plan.language)
            path = folder/paths[module.name].name; path.write_text(source)
            sources.append(path)
            # Compile a dependency closure, without unrelated modules.
            needed = set()
            def visit(name):
                if name in needed: return
                needed.add(name)
                for dep in next(m for m in plan.modules if m.name == name).dependencies: visit(dep)
            visit(module.name)
            gate = self.tools.module(module, [*self.library.plan_sources(plan, needed),
                *[p for p in sources if p.stem in needed]], folder, language=plan.language)
            save(folder/'verification.json', gate)
            if not gate['passed']: raise ValueError(f'Initial module failed fresh verification: {module.name}')
            save(folder/'implementation.json', {'rationale':'Immutable shared experimental baseline; freshly verified',
                                               'original_source':str(paths[module.name]), 'sha256':digest(path)})
            path.chmod(0o444)
        rtl = [Path(gate['elaborated_verilog'])] if plan.language == 'chisel' else sources
        verification = self.tools.verify(plan, rtl, self.algorithm.verification(config, self.task.seed, plan.top), work)
        if not verification['passed']: raise ValueError('Initial design failed independent E2E')
        save(work/'provenance.json', {'run':str(run), 'round':original['round'], 'source_hashes':original['sources'],
                                    'measurements_reused':False})
        save(work/'system_plan.json', asdict(plan))
        return config, profile, plan, sources, rtl, verification, work

    def event(self, stage, **details):
        with self.event_lock:
            self.events.append({'time_unix': time.time(), 'stage': stage, **deepcopy(details)})
            save(self.workspace/'events.json', self.events)

    def context(self, **extra):
        return {'task': asdict(self.task), 'algorithm': self.contract, **extra}

    def measured_profile(self, config):
        self.algorithm.validate_config(config)
        key = json.dumps(config, sort_keys=True)
        if key not in self.profile_cache:
            profile = self.algorithm.profile(config, self.task.seed)
            loss = profile['quality_loss']
            if not isinstance(loss, (int, float)) or not math.isfinite(loss) or loss < 0:
                raise ValueError('Algorithm plugin returned an invalid quality loss')
            self.profile_cache[key] = profile
        return self.profile_cache[key]

    def kernel(self, advice):
        # Survey the declared finite domain using trusted executions BEFORE the LLM
        # chooses. Large domains receive a reproducible budgeted random subset.
        space = self.contract['config_space']
        if not space or any(not isinstance(v, list) or not v for v in space.values()):
            raise ValueError('Algorithm config_space must declare nonempty finite lists')
        keys = list(space)
        cardinality = math.prod(len(space[k]) for k in keys)
        budget = self.task.kernel_profile_budget
        if cardinality <= budget:
            configs = [dict(zip(keys, values)) for values in itertools.product(*(space[k] for k in keys))]
        else:
            rng = random.Random(self.task.seed)
            configs = [dict(zip(keys, values)) for values in
                       (tuple(rng.choice(space[k]) for k in keys) for _ in range(budget))]
        survey, rejected = [], []
        for config in configs:
            try:
                self.algorithm.validate_config(config)
            except ValueError as exc:
                rejected.append({'config': config, 'error': str(exc)})
                continue
            survey.append(self.measured_profile(config))
        save(self.workspace/'kernel_survey.json', {'space_size': cardinality,
             'profile_budget': budget, 'profiles': list(self.profile_cache.values()),
             'invalid_combinations': rejected})
        feedback = []
        for attempt in range(self.task.module_attempts):
            self.event('kernel', attempt=attempt+1)
            try:
                choice = self.agents['kernel'].run(self.context(critic=advice, measured_config_profiles=survey, feedback=feedback))
                profile = self.measured_profile(choice['config'])
                loss = profile['quality_loss']
                if not isinstance(loss, (int, float)) or not math.isfinite(loss) or loss < 0:
                    raise ValueError('Algorithm plugin returned an invalid quality loss')
                self.event('kernel_profile', choice=choice, profile=profile)
                if loss > self.task.constraints['max_quality_loss']:
                    feedback.append({'choice': choice, 'profile': profile, 'error': 'Quality constraint failed'})
                    continue
                return choice['config'], profile
            except (ValueError, KeyError, TypeError) as exc:
                feedback.append({'error': str(exc)})
        raise RuntimeError(f'Kernel budget exhausted: {feedback}')

    def compile_plan(self, profile, config, advice, previous_plan, feedback, work):
        references, reads, pending_plan = {}, [], None
        for turn in range(self.task.template_read_budget+1):
            response_errors, raw, plan, rejected_plan = [], None, None, None
            for retry in range(self.task.module_attempts):
                candidate = None
                try:
                    candidate = self.agents['compiler'].run(self.context(profile=profile, config=config,
                        hardware_catalog=self.library.template_index(), reference_code=references,
                        reference_support_code=self.library.support_code(references),
                        reference_tests=self.library.test_references(references),
                        library_read_completed=bool(reads),
                        critic=advice, previous_plan=asdict(previous_plan) if previous_plan else None,
                        uarch_feedback=feedback, response_errors=response_errors, rejected_plan=rejected_plan,
                        plan_awaiting_reference_review=pending_plan,
                        remaining_reference_reads=self.task.template_read_budget-turn))
                    if 'read_templates' not in candidate:
                        plan = SystemPlan.parse(candidate, self.contract['ports'], require_jobs=True)
                    raw = candidate
                    break
                except (ValueError, KeyError, TypeError) as exc:
                    if candidate is not None:
                        rejected_plan = candidate
                    response_errors.append(str(exc))
                    self.event('compiler_response_retry', attempt=retry+1, error=str(exc))
            if raw is None:
                raise ValueError(f'Compiler response budget exhausted: {response_errors}')
            if 'read_templates' in raw:
                ids = raw['read_templates']
                if not isinstance(ids, list) or any(not isinstance(i, str) for i in ids):
                    raise ValueError('read_templates must be a list of catalog IDs')
            else:
                assigned = list(dict.fromkeys(ref for module in plan.modules for ref in module.reference_ids))
                self.library.templates(assigned)  # fail closed on invented IDs
                ids = [ref for ref in assigned if ref not in references]
                if not ids:
                    return plan
                # Resolve an unread assignment and let Compiler inspect it before finalizing.
                pending_plan=raw
            if turn == self.task.template_read_budget:
                raise ValueError('Compiler reference-read budget exhausted; return a final plan')
            references.update(self.library.templates(ids))
            entry = {'turn': turn+1, 'references': self.library.bindings(ids)}
            reads.append(entry)
            save(work/'compiler_reference_reads.json', reads)
            self.event('compiler_library_read', **entry)
        raise RuntimeError('Compiler did not return a system plan')

    def build(self, profile, config, advice, previous_plan, previous_sources, round_dir):
        feedback, previous_failures = [], {}
        for attempt in range(1, self.task.compiler_attempts+1):
            work = round_dir/f'build_{attempt:02d}'
            work.mkdir()
            plan, sources = None, []
            try:
                # UArch reentry preserves the interface/topology plan on the first attempt.
                # A real implementation failure is allowed to escalate back to Compiler.
                if attempt == 1 and advice and advice['layer'] == 'uarch' and previous_plan:
                    plan = previous_plan
                else:
                    self.event('compiler', build=attempt, round_dir=str(round_dir))
                    plan = self.compile_plan(profile, config, advice, previous_plan, feedback, work)
                if self.task.hdl != 'auto' and plan.language != self.task.hdl:
                    raise ValueError(f'Plan language must be {self.task.hdl}')
                save(work/'system_plan.json', asdict(plan))
                save(work/'reference_bindings.json', {m.name:self.library.bindings(m.reference_ids) for m in plan.modules})
                dispatcher = DesignDispatcher(self, plan, work, profile, config, advice, previous_sources,
                                              previous_failures)
                sources, rtl_sources, verification = dispatcher.run()
                self.library.check()
                return plan, sources, rtl_sources, verification, work
            except (ValueError, KeyError, TypeError) as exc:
                module_feedback = {}
                for path in work.glob('*/failure.json'):
                    detail = json.loads(path.read_text())
                    last = detail.get('feedback', [{}])[-1]
                    module_feedback[path.parent.name] = {
                        'reason': detail.get('reason'), 'full_log': str(path),
                        'compiler_diagnosis': detail.get('diagnosis'),
                        # Source-contract rejects never reach the canonical .scala/.v file.
                        # Retain their actual source so Compiler can diagnose the rejected structure.
                        'failed_source': last.get('source', last.get('rtl')),
                        'last_failure': {k: v for k, v in last.items() if k not in ('source', 'rtl', 'reply')}}
                failure = {'build': attempt, 'plan': asdict(plan) if plan else None,
                           'implemented_sources': {p.name: p.read_text() for p in work.glob('*/*')
                                                   if p.suffix in ('.v', '.scala')},
                           'module_feedback': module_feedback,
                           'error': str(exc)}
                feedback.append(failure)
                save(work/'compiler_feedback.json', failure)
                self.event('compiler_feedback', **failure)
                if plan is not None:
                    previous_plan = plan
                # A restarted worker must see the rejected candidate and actual
                # failure, rather than relearning the same defect from scratch.
                # This is diagnostic context, never an accepted implementation.
                previous_failures.update(module_feedback)
                # A replan may adapt already accepted modules instead of forgetting their fixes.
                # This is source context only: every new candidate still receives fresh checks.
                retained = {p.stem: p.read_text() for p in work.glob('*/*')
                            if p.suffix in ('.v', '.scala') and (p.parent/'implementation.json').is_file()}
                previous_sources = {**previous_sources, **retained}
                if retained:
                    self.event('accepted_source_retained', build=attempt, modules=sorted(retained),
                               measurements_reused=False)
        raise RuntimeError('Compiler/UArch build budget exhausted; see compiler_feedback.json')

    def run(self):
        advice, config, profile, plan, previous_sources = None, None, None, None, {}
        status, error = 'budget_exhausted', None
        try:
            for number in range(1, self.task.max_loops+1):
                record = {'round': number, 'reentry': advice['layer'] if advice else 'kernel',
                          'status': 'running'}
                if number == 1 and self.initial_run:
                    record['reentry'] = 'shared_initial_design'
                self.records.append(record)
                if number > 1 and self.records[-2].get('critique'):
                    self.records[-2]['critique_applied'] = True
                round_dir = self.workspace/f'round_{number:02d}'
                round_dir.mkdir()
                self.event('round_start', round=number, reentry=record['reentry'])
                if number == 1 and self.initial_run:
                    record['reentry'] = 'shared_initial_design'
                    config, profile, plan, sources, rtl_sources, verification, work = self.initial_design(round_dir)
                elif config is None or (advice and advice['layer'] == 'kernel'):
                    config, profile = self.kernel(advice)
                    # Algorithm changes invalidate the whole design and test vectors.
                    plan, previous_sources = None, {}
                    if advice:
                        self.event('kernel_advice_resolved', proposed=advice, selected_config=config, profile=profile)
                        advice={'layer':'kernel', 'reason':'Kernel resolved the proposed algorithm intervention using measurements.',
                                'instructions':'Implement ONLY the Kernel-approved config in context: '+json.dumps(config,sort_keys=True)+
                                               '. Earlier parameter suggestions are superseded.',
                                'evidence':['profile.config']}
                record.update(config=config, profile=profile)
                if not (number == 1 and self.initial_run):
                    plan, sources, rtl_sources, verification, work = self.build(profile, config, advice, plan,
                                                                   previous_sources, round_dir)
                record['system_plan'] = asdict(plan)
                record['implementations'] = {p.stem: json.loads((p.parent/'implementation.json').read_text()) for p in sources}
                record['sources'] = {str(p.relative_to(self.workspace)): digest(p) for p in sources}
                record['rtl_sources'] = {str(p.relative_to(self.workspace)): digest(p) for p in rtl_sources}
                self.event('ppa', round=number)
                evaluation = self.tools.evaluate(plan, rtl_sources, verification, profile, self.task, work)
                self.library.check()
                record['evaluation'] = evaluation
                record['status'] = 'evaluated' if evaluation['complete'] else 'ppa_failed'
                save(round_dir/'result.json', record)
                if not evaluation['complete']:
                    status = 'ppa_failed'
                    break
                previous_sources = {p.stem:p.read_text() for p in sources}
                if self.critic_enabled:
                    self.event('critic', round=number)
                    critic_feedback = []
                    advice = None
                    available = []
                    def collect(value, prefix):
                        if isinstance(value, dict):
                            for key, child in value.items():
                                if key not in ('diagnostics', 'command', 'cell_histogram'):
                                    collect(child, f'{prefix}.{key}')
                        elif value is not None and not isinstance(value, (list, tuple)):
                            available.append(prefix)
                    collect(record['evaluation'], 'evaluation')
                    collect(record['profile'], 'profile')
                    for retry in range(self.task.module_attempts):
                        try:
                            critique = self.agents['critic'].run(self.context(current=record,
                                history=self.records[:-1], pareto_rounds=pareto(self.records),
                                available_evidence=available, validation_feedback=critic_feedback,
                                measured_config_profiles=list(self.profile_cache.values()),
                                remaining_rounds=self.task.max_loops-number))
                            checked_advice = validate_critique(critique, record)
                            if checked_advice['layer']=='kernel':
                                proposed=checked_advice.get('proposed_config')
                                if not isinstance(proposed,dict):
                                    raise ValueError('Kernel intervention requires a complete proposed_config object')
                                proposed_profile=self.measured_profile(proposed)
                                self.event('critic_proposal_profile', config=proposed, profile=proposed_profile)
                                if proposed_profile['quality_loss']>self.task.constraints['max_quality_loss']:
                                    raise ValueError('Proposed kernel config violates measured quality constraint: '+json.dumps(proposed_profile))
                            advice = checked_advice
                            break
                        except (ValueError, KeyError, TypeError) as exc:
                            critic_feedback.append({'error': str(exc)})
                            self.event('critic_format_repair', round=number, attempt=retry+1, error=str(exc))
                    if advice is None:
                        raise ValueError(f'Critic response budget exhausted: {critic_feedback}')
                    record.update(critique=advice, critique_applied=False)
                    if advice['layer'] == 'stop':
                        status = 'critic_stopped'
                        break
                else:
                    # Budget-matched no-Critic arm: Kernel is retained, Compiler independently replans.
                    advice = {'layer': 'compiler', 'instructions': 'Propose another design within the same constraints.'}
                save(round_dir/'result.json', record)
        except Exception as exc:
            status, error = 'failed', f'{type(exc).__name__}: {exc}'
            self.event('failure', error=error)
            if self.records:
                self.records[-1]['status'] = 'failed'
                self.records[-1]['error'] = error
        finally:
            try:
                self.library.check()
                intact = True
            except Exception as exc:
                intact, status, error = False, 'reference_integrity_failed', str(exc)
            if not intact:
                for record in self.records:
                    if 'evaluation' in record:
                        record['evaluation']['feasible'] = False
            for record in self.records:
                save(self.workspace/f'round_{record["round"]:02d}'/'result.json', record)
            summary = {'status': status, 'error': error, 'reference_integrity': intact,
                'critic_enabled': self.critic_enabled, 'rounds': self.records,
                'pareto_rounds': pareto(self.records),
                'agent_calls': {**{name: agent.calls for name, agent in self.agents.items()},
                    **{role: sum(a.calls for a in self.design_agents if a.role == role)
                       for role in ('uarch', 'uarch_assembly', 'compiler_diagnosis')}},
                'orchestration': 'parallel module UArch sessions, dependency barrier, separate assembly UArch',
                'evidence_scope': 'generated complete integration workload; not legacy DynaX or whole-model evidence'}
            save(self.workspace/'summary.json', summary)
        return summary
