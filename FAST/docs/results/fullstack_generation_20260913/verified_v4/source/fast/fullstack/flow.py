"""The main library -> Kernel -> Compiler/UArch -> E2E/PPA -> Critic loop."""
from __future__ import annotations

from dataclasses import asdict
import math
import itertools
import json
import random
import platform
from pathlib import Path
import time

from .agents import KernelAgent, CompilerAgent, UArchAgent, CriticAgent, validate_critique
from .contracts import SystemPlan, Task, pareto
from .library import Library, digest, save
from .tools import check_source, check_chisel_source


class FullStackFlow:
    def __init__(self, task: Task, catalog: Path, workspace: Path, llm, tools,
                 *, critic_enabled: bool = True):
        self.task, self.workspace, self.tools = task, workspace.resolve(), tools
        self.workspace.mkdir(parents=True, exist_ok=False)
        self.library = Library(catalog, self.workspace)
        self.algorithm = self.library.algorithm(task.algorithm)
        self.contract = self.algorithm.describe()
        self.agents = {name: cls(llm, name, self.workspace/'agent_calls') for name, cls in (
            ('kernel', KernelAgent), ('compiler', CompilerAgent), ('uarch', UArchAgent), ('critic', CriticAgent))}
        self.critic_enabled = critic_enabled
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

    def event(self, stage, **details):
        self.events.append({'time_unix': time.time(), 'stage': stage, **details})
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

    def build(self, profile, config, advice, previous_plan, previous_sources, round_dir):
        feedback = []
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
                    raw = self.agents['compiler'].run(self.context(profile=profile, config=config,
                        templates=self.library.templates(), critic=advice,
                        previous_plan=asdict(previous_plan) if previous_plan else None,
                        uarch_feedback=feedback))
                    plan = SystemPlan.parse(raw, self.contract['ports'])
                if self.task.hdl != 'auto' and plan.language != self.task.hdl:
                    raise ValueError(f'Plan language must be {self.task.hdl}')
                save(work/'system_plan.json', asdict(plan))
                sources = []
                for module in plan.modules:
                    module_dir = work/module.name
                    module_dir.mkdir()
                    failures, passed = [], False
                    for repair in range(1, self.task.module_attempts+1):
                        self.event('uarch', module=module.name, attempt=repair, build=attempt)
                        answer = self.agents['uarch'].run(self.context(profile=profile, config=config,
                            system_plan=asdict(plan), module=asdict(module), critic=advice,
                            templates=self.library.templates(),
                            implemented_dependencies={p.stem: p.read_text() for p in sources},
                            previous_implementation=previous_sources.get(module.name), feedback=failures))
                        if answer.get('replan_reason'):
                            raise ValueError(f'UArch requests Compiler replan: {answer["replan_reason"]}')
                        try:
                            source = answer.get('source', answer.get('rtl'))
                            if plan.language == 'chisel':
                                check_chisel_source(source, module)
                            else:
                                check_source(source, module)
                        except (ValueError, KeyError, TypeError) as exc:
                            failures.append({'error': str(exc), 'reply': answer})
                            self.event('module_repair', module=module.name, error=str(exc))
                            continue
                        suffix = 'scala' if plan.language == 'chisel' else 'v'
                        path = module_dir/f'{module.name}.{suffix}'
                        path.write_text(source)
                        check_dir = module_dir/f'check_{repair:02d}'
                        check_dir.mkdir()
                        gate = self.tools.module(module, [*sources, path], check_dir, language=plan.language)
                        save(module_dir/f'check_{repair:02d}.json', gate)
                        # Keep each rejected implementation, not just the eventual file.
                        (module_dir/f'attempt_{repair:02d}.{suffix}.txt').write_text(source)
                        self.event('module_check', module=module.name, passed=gate['passed'])
                        if gate['passed']:
                            sources.append(path)
                            passed = True
                            break
                        failures.append({'rtl': source, 'tool': gate})
                    if not passed:
                        raise ValueError(f'Module {module.name} exhausted repairs: {failures}')
                self.library.check()
                self.event('e2e', build=attempt)
                trusted = self.algorithm.verification(config, self.task.seed, plan.top)
                rtl_sources = [Path(gate['elaborated_verilog'])] if plan.language == 'chisel' else sources
                verification = self.tools.verify(plan, rtl_sources, trusted, work)
                save(work/'verification.json', verification)
                if not verification['passed']:
                    raise ValueError(f'Whole-system verification failed: {verification}')
                self.library.check()
                return plan, sources, rtl_sources, verification, work
            except (ValueError, KeyError, TypeError) as exc:
                failure = {'build': attempt, 'plan': asdict(plan) if plan else None,
                           'implemented_sources': {p.name: p.read_text() for p in sources},
                           'error': str(exc)}
                feedback.append(failure)
                save(work/'compiler_feedback.json', failure)
                self.event('compiler_feedback', **failure)
        raise RuntimeError('Compiler/UArch build budget exhausted; see compiler_feedback.json')

    def run(self):
        advice, config, profile, plan, previous_sources = None, None, None, None, {}
        status, error = 'budget_exhausted', None
        try:
            for number in range(1, self.task.max_loops+1):
                record = {'round': number, 'reentry': advice['layer'] if advice else 'kernel',
                          'status': 'running'}
                self.records.append(record)
                if number > 1 and self.records[-2].get('critique'):
                    self.records[-2]['critique_applied'] = True
                round_dir = self.workspace/f'round_{number:02d}'
                round_dir.mkdir()
                self.event('round_start', round=number, reentry=record['reentry'])
                if config is None or (advice and advice['layer'] == 'kernel'):
                    config, profile = self.kernel(advice)
                    # Algorithm changes invalidate the whole design and test vectors.
                    plan, previous_sources = None, {}
                record.update(config=config, profile=profile)
                plan, sources, rtl_sources, verification, work = self.build(profile, config, advice, plan,
                                                               previous_sources, round_dir)
                record['system_plan'] = asdict(plan)
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
                                remaining_rounds=self.task.max_loops-number))
                            advice = validate_critique(critique, record)
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
                'agent_calls': {name: agent.calls for name, agent in self.agents.items()},
                'evidence_scope': 'generated complete integration workload; not legacy DynaX or whole-model evidence'}
            save(self.workspace/'summary.json', summary)
        return summary
