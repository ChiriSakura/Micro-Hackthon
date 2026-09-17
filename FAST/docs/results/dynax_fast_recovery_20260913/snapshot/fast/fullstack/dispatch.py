"""Dependency-aware parallel module sessions followed by one assembly session."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import asdict
from pathlib import Path
import re

from .agents import UArchAgent, AssemblyUArchAgent, CompilerDiagnosisAgent
from .library import digest, save
from .tools import check_source, check_chisel_source
from .behavior import explain_behavior, explain_module_failure


def check_accepted(accepted):
    for name, artifact in accepted.items():
        if digest(artifact['path']) != artifact['sha256']:
            raise ValueError(f'Accepted module {name} changed; verification is invalid')


class DesignDispatcher:
    def __init__(self, flow, plan, work, profile, config, advice, previous_sources, previous_failures=None):
        self.flow, self.plan, self.work = flow, plan, work
        self.profile, self.config, self.advice = profile, config, advice
        self.previous_sources = previous_sources
        self.modules = {m.name: m for m in plan.modules}
        self.jobs = {}
        llm = flow.llm.fork() if hasattr(flow.llm, 'fork') else flow.llm
        self.diagnostician = CompilerDiagnosisAgent(llm, 'compiler_diagnosis',
            flow.workspace/'agent_calls'/work.relative_to(flow.workspace))
        flow.design_agents.append(self.diagnostician)
        plan_context = asdict(plan)
        for item in plan_context['modules']:
            item.pop('tests', None)  # each worker receives its own tests below, not all other vectors
        # Prepare ALL isolated prompts/reference bindings before launching any worker.
        for module in plan.modules:
            directory = work/module.name
            directory.mkdir()
            context = flow.context(profile=profile, config=config, system_plan=plan_context,
                module=asdict(module), compiler_prompt=module.design_prompt, critic=advice,
                reference_code=flow.library.templates(module.reference_ids),
                reference_support_code=flow.library.support_code(module.reference_ids),
                linked_library_symbols=flow.library.linked_symbols(module.linked_reference_ids),
                reference_tests=flow.library.test_references(module.reference_ids),
                reference_provenance=flow.library.bindings(module.reference_ids),
                computed_behavior_examples=explain_behavior(module),
                previous_failed_attempt=(previous_failures or {}).get(module.name),
                previous_implementation=previous_sources.get(module.name))
            save(directory/'job.json', context)
            role = 'uarch_assembly' if module.name == plan.top else 'uarch'
            cls = AssemblyUArchAgent if module.name == plan.top else UArchAgent
            llm = flow.llm.fork() if hasattr(flow.llm, 'fork') else flow.llm
            agent = cls(llm, role, flow.workspace/'agent_calls'/work.relative_to(flow.workspace)/module.name)
            flow.design_agents.append(agent)
            self.jobs[module.name] = (agent, context, directory)

    def closure(self, name):
        names = set()
        def visit(child):
            if child in names:
                return
            names.add(child)
            for dep in self.modules[child].dependencies:
                visit(dep)
        for dep in self.modules[name].dependencies:
            visit(dep)
        return [m.name for m in self.plan.modules if m.name in names]

    def implement(self, name, accepted, *, assembly=False):
        module = self.modules[name]
        agent, context, directory = self.jobs[name]
        # Assembly receives the complete accepted collection. Ordinary workers see only real dependencies.
        dep_names = list(accepted) if assembly else self.closure(name)
        deps = {n: accepted[n] for n in dep_names}
        dep_sources = [item['path'] for item in deps.values()]
        library_sources = self.flow.library.plan_sources(self.plan, {name, *self.closure(name)})
        save(directory/'linked_library_sources.json', {str(p): digest(p) for p in library_sources})
        failures, previous_assertion, diagnosis = [], None, None
        suffix = 'scala' if self.plan.language == 'chisel' else 'v'
        path = directory/f'{name}.{suffix}'
        budget = self.flow.task.assembly_attempts if assembly else self.flow.task.module_attempts
        for attempt in range(1, budget+1):
            check_accepted(deps)
            self.flow.event('assembly_attempt' if assembly else 'uarch', module=name, attempt=attempt,
                            job=str(directory.relative_to(self.flow.workspace)))
            if failures and (assembly or len(failures) >= 2):
                # Repeated local failures also need planner review. Diagnosis
                # consumes no extra implementation attempts and cannot edit tests.
                diagnostic_context = {**context, 'failed_attempt': failures[-1],
                    'implemented_dependencies': {n: a['path'].read_text() for n, a in deps.items()},
                    'previous_diagnosis': diagnosis}
                diagnostic_text = str(failures[-1].get('system_verification', {}))
                match = re.search(r'case[ =](\d+)', diagnostic_text)
                if assembly and match:
                    trusted = self.flow.algorithm.verification(self.config, self.flow.task.seed, self.plan.top)
                    if int(match[1]) < len(trusted.get('vectors', [])):
                        diagnostic_context['independent_failing_vector'] = trusted['vectors'][int(match[1])]
                try:
                    diagnosis = self.diagnostician.run(diagnostic_context)
                    save(directory/f'diagnosis_{attempt:02d}.json', diagnosis)
                    self.flow.event('compiler_diagnosis', module=name, attempt=attempt, diagnosis=diagnosis)
                except (ValueError, KeyError, TypeError) as exc:
                    diagnosis = None
                    self.flow.event('compiler_diagnosis_failed', module=name, attempt=attempt, error=str(exc))
                if diagnosis and diagnosis['action'] == 'replan':
                    save(directory/'failure.json', {'module': name, 'feedback': failures, 'diagnosis': diagnosis})
                    raise ValueError(f'{name}: Compiler diagnosis requests replan: {diagnosis["reason"]}')
            try:
                answer = agent.run({**context, 'feedback': failures,
                    'compiler_diagnosis': diagnosis,
                    'implemented_dependencies': {n: a['path'].read_text() for n, a in deps.items()},
                    'accepted_modules': {n: {'sha256': a['sha256'], 'gate': a['gate']} for n, a in deps.items()}})
            except (ValueError, KeyError, TypeError) as exc:
                failures.append({'stage': 'llm_response', 'error': str(exc)})
                continue
            if answer.get('replan_reason'):
                failure = {'stage': 'uarch_replan_request', 'replan_reason': answer['replan_reason']}
                failures.append(failure)
                try:
                    diagnosis = self.diagnostician.run({**context, **failure,
                        'failed_attempt': failure,
                        'implemented_dependencies': {n: a['path'].read_text() for n, a in deps.items()}})
                    save(directory/f'replan_review_{attempt:02d}.json', diagnosis)
                    self.flow.event('compiler_replan_review', module=name, attempt=attempt, diagnosis=diagnosis)
                except (ValueError, KeyError, TypeError) as exc:
                    diagnosis = None
                    self.flow.event('compiler_replan_review_failed', module=name, error=str(exc))
                if diagnosis and diagnosis['action'] == 'repair':
                    failure['compiler_diagnosis'] = diagnosis
                    continue
                save(directory/'failure.json', {'module': name, 'feedback': failures, 'diagnosis': diagnosis})
                raise ValueError(f'{name} requests Compiler replan: {answer["replan_reason"]}')
            source = answer.get('source', answer.get('rtl'))
            if isinstance(source, str):
                (directory/f'attempt_{attempt:02d}.{suffix}.txt').write_text(source)
            try:
                self.flow.library.check_generated(source, module, self.plan.language)
            except (ValueError, KeyError, TypeError) as exc:
                failures.append({'stage': 'source_contract', 'error': str(exc), 'reply': answer, 'source': source})
                save(directory/f'check_{attempt:02d}.json', {'passed': False, **failures[-1]})
                continue
            path.write_text(source)
            check_dir = directory/f'check_{attempt:02d}'
            check_dir.mkdir()
            gate = self.flow.tools.module(module, [*library_sources, *dep_sources, path], check_dir, language=self.plan.language)
            save(directory/f'check_{attempt:02d}.json', gate)
            self.flow.event('assembly_check' if assembly else 'module_check', module=name, passed=gate['passed'])
            check_accepted(deps)
            verification, rtl_sources = None, None
            if gate['passed'] and assembly:
                rtl_sources = [Path(gate['elaborated_verilog'])] if self.plan.language == 'chisel' else [*dep_sources, path]
                self.flow.event('e2e', module=name, attempt=attempt)
                trusted = self.flow.algorithm.verification(self.config, self.flow.task.seed, self.plan.top)
                verification = self.flow.tools.verify(self.plan, rtl_sources, trusted, check_dir)
                save(check_dir/'verification.json', verification)
                check_accepted(deps)
            if gate['passed'] and (not assembly or verification['passed']):
                artifact = {'path': path, 'sha256': digest(path), 'gate': gate,
                            'verification': verification, 'rtl_sources': rtl_sources}
                save(directory/'implementation.json', {'module': name, 'role': agent.role,
                    'language': self.plan.language, 'source_sha256': artifact['sha256'],
                    'linked_reference_ids': list(module.linked_reference_ids),
                    'linked_library_sha256': {str(p): digest(p) for p in library_sources},
                    'reference_ids': list(module.reference_ids), 'rationale': answer.get('rationale', ''),
                    'critic_request': self.advice,
                    'scope': 'Agent explanation; module planner-vector checks and independent E2E are separate evidence'})
                path.chmod(0o444)
                self.flow.event('assembly_accepted' if assembly else 'module_accepted', module=name,
                                source_sha256=artifact['sha256'])
                return artifact
            failure = {'source': source, 'tool': gate, 'numeric_failure': explain_module_failure(module, gate)}
            if verification is not None:
                failure['system_verification'] = verification
            failures.append(failure)
            if not assembly:
                diagnostic = gate.get('functional', {}).get('simulation', {}).get('diagnostics', '')
                match = re.search(r'module case=\d+ step=\d+ output=\w+ expected=\d+ actual=\d+', diagnostic)
                assertion = match.group() if match else None
                if assertion and assertion == previous_assertion:
                    save(directory/'failure.json', {'module': name, 'feedback': failures,
                        'reason': 'Repeated identical functional mismatch; Compiler must review plan and frozen tests'})
                    raise ValueError(f'{name}: repeated functional mismatch ({assertion}). '
                        'Compiler must review the module math, pipeline protocol and frozen test expectations. '
                        'This is not proof that the implementation or the test is correct. '
                        f'Full feedback: {directory/"failure.json"}')
                previous_assertion = assertion
        save(directory/'failure.json', {'module': name, 'feedback': failures})
        raise ValueError(f'{name} exhausted {"assembly" if assembly else "module"} repairs; '
                         f'full feedback: {directory/"failure.json"}')

    def run(self):
        accepted, active = {}, {}
        pending = [m.name for m in self.plan.modules if m.name != self.plan.top]
        self.flow.event('module_dispatch', modules=pending, workers=self.flow.task.module_workers)
        with ThreadPoolExecutor(max_workers=self.flow.task.module_workers, thread_name_prefix='fast-uarch') as pool:
            while pending or active:
                ready = [n for n in pending if all(d in accepted for d in self.modules[n].dependencies)]
                for name in ready[:max(0, self.flow.task.module_workers-len(active))]:
                    pending.remove(name)
                    active[pool.submit(self.implement, name, dict(accepted))] = name
                if not active:
                    raise ValueError('No runnable module in the dependency graph')
                completed, _ = wait(active, return_when=FIRST_COMPLETED)
                errors = []
                for future in completed:
                    name = active.pop(future)
                    try:
                        accepted[name] = future.result()
                    except Exception as exc:
                        errors.append(f'{name}: {type(exc).__name__}: {exc}')
                        self.flow.event('module_failed', module=name, error=str(exc))
                if errors:
                    # Drain already-running work before replanning; never overlap plans or assemble a partial set.
                    for future in active:
                        future.cancel()
                    # Observe every launched result and record additional failures during drain.
                    for future, name in active.items():
                        if future.cancelled():
                            self.flow.event('module_cancelled', module=name)
                            continue
                        try:
                            accepted[name] = future.result()
                        except Exception as exc:
                            errors.append(f'{name}: {type(exc).__name__}: {exc}')
                            self.flow.event('module_failed', module=name, error=str(exc))
                    raise ValueError('Module dispatch failed: ' + '; '.join(errors))
        # Stable dependency order independent of completion order.
        accepted = {m.name: accepted[m.name] for m in self.plan.modules if m.name != self.plan.top}
        check_accepted(accepted)
        save(self.work/'accepted_modules.json', {n: {'path': str(a['path']), 'sha256': a['sha256'],
             'gate': a['gate']} for n, a in accepted.items()})
        self.flow.event('assembly_start', accepted_modules=list(accepted))
        top = self.implement(self.plan.top, accepted, assembly=True)
        check_accepted(accepted)
        sources = [a['path'] for a in accepted.values()] + [top['path']]
        save(self.work/'verification.json', top['verification'])
        return sources, top['rtl_sources'], top['verification']
