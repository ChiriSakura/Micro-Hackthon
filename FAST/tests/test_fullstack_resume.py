"""Fault injection for recovery; these doubles do not count as physical evidence."""
import json
from pathlib import Path
import runpy
import sys

import pytest

from fast.fullstack.flow import FullStackFlow
from fast.fullstack.library import digest
from fast.fullstack.recovery import read_summary
from test_fullstack_generation import CATALOG, FakeTools, ScriptedLLM, task


def test_interrupted_ppa_is_durable_and_resumed_without_new_generated_design(tmp_path):
    class Interrupt(FakeTools):
        def evaluate(self, plan, sources, verification, profile, task, work):
            saved = json.loads((work.parent/'result.json').read_text())
            assert saved['status'] == 'ppa_pending' and saved['sources'] and saved['verification']['passed']
            raise KeyboardInterrupt('scheduler termination')
    original = tmp_path/'original'
    flow = FullStackFlow(task(max_loops=2), CATALOG, original, ScriptedLLM('compiler'), Interrupt())
    with pytest.raises(KeyboardInterrupt): flow.run()
    hashes = {str(p.relative_to(original)): digest(p) for p in original.rglob('*') if p.is_file()}
    llm, tools = ScriptedLLM('compiler'), FakeTools()
    resumed = FullStackFlow(task(max_loops=2), CATALOG, tmp_path/'resumed', llm, tools, resume_run=original)
    result = resumed.run()
    assert result['completed_design_rounds'] == [1, 2]
    assert tools.events.count('ppa') == 2
    assert llm.roles.count('uarch') == 1  # only new round 2 needs generation
    assert result['rounds'][0]['recovery_e2e']['passed']
    assert hashes == {str(p.relative_to(original)): digest(p) for p in original.rglob('*') if p.is_file()}
    assert len(list((tmp_path/'resumed/agent_calls/compiler').glob('*.json'))) == 2


def test_resume_rejects_mutated_rtl_and_changed_constraint(tmp_path):
    original = tmp_path/'original'
    flow = FullStackFlow(task(max_loops=1), CATALOG, original, ScriptedLLM(), FakeTools())
    flow.run()
    changed = dict(flow.task.constraints, frequency_mhz=301)
    with pytest.raises(ValueError, match='scientific task'):
        FullStackFlow(task(max_loops=2, constraints=changed), CATALOG, tmp_path/'changed',
                      ScriptedLLM(), FakeTools(), resume_run=original)
    source = next(original.glob('round_*/build_*/Leaf/Leaf.v'))
    source.chmod(0o644); source.write_text('mutated')
    with pytest.raises(ValueError, match='source integrity'):
        FullStackFlow(task(max_loops=2), CATALOG, tmp_path/'corrupt',
                      ScriptedLLM(), FakeTools(), resume_run=original)


def test_incomplete_ppa_reaches_critic_and_remaining_budget(tmp_path):
    class PpaFailure(FakeTools):
        def evaluate(self, *args):
            result = super().evaluate(*args)
            if self.events.count('ppa') == 1:
                result.update(complete=False, feasible=False, error='routing timeout')
            return result
    llm = ScriptedLLM('compiler')
    flow = FullStackFlow(task(max_loops=2, continue_after_build_failure=True), CATALOG,
                        tmp_path/'run', llm, PpaFailure())
    result = flow.run()
    assert result['completed_design_rounds'] == [2]
    assert result['pareto_rounds'] == [2]
    assert result['rounds'][0]['status'] == 'ppa_failed'
    contexts = [c for role, c in llm.contexts if role == 'critic']
    assert contexts[0]['current']['evaluation']['complete'] is False
    assert contexts[0]['current']['evaluation']['error'] == 'routing timeout'


def test_missing_summary_keeps_completed_rounds_and_rejects_null_evaluation(tmp_path):
    run = tmp_path/'run'; run.mkdir()
    for number, evaluation in [(1, {'feasible': True, 'energy_nj': 2, 'latency_ns': 70}), (2, None)]:
        folder = run/f'round_{number:02d}'; folder.mkdir()
        (folder/'result.json').write_text(json.dumps({'round': number, 'evaluation': evaluation}))
    summary = read_summary(run)
    assert summary['status'] == 'interrupted_without_summary'
    assert summary['pareto_rounds'] == [1]
    assert len(summary['rounds']) == 2 and not (run/'summary.json').exists()


def test_successful_retry_archives_old_rollback_decision(tmp_path):
    class LastPpaFails(FakeTools):
        def evaluate(self, *args):
            result = super().evaluate(*args)
            if self.events.count('ppa') == 2:
                result.update(complete=False, feasible=False, error='routing failed')
            return result
    original = tmp_path/'original'
    spec = task(max_loops=2, continue_after_build_failure=True)
    before = FullStackFlow(spec, CATALOG, original, ScriptedLLM('compiler'), LastPpaFails()).run()
    assert before['rounds'][-1]['rollback_to_round'] == 1
    llm = ScriptedLLM('compiler')
    after = FullStackFlow(spec, CATALOG, tmp_path/'retry', llm, FakeTools(), resume_run=original).run()
    last = after['rounds'][-1]
    assert last['evaluation']['complete']
    assert 'rollback_to_round' not in last and 'critique_evidence_round' not in last
    assert last['prior_attempt_decisions'][-1]['rollback_to_round'] == 1
    assert last['prior_evaluations'][-1]['error'] == 'routing failed'
    assert 'uarch' not in llm.roles


def test_critic_receives_exact_current_accepted_sources(tmp_path):
    llm = ScriptedLLM()
    workspace = tmp_path/'run'
    result = FullStackFlow(task(max_loops=1), CATALOG, workspace, llm, FakeTools()).run()
    context = next(c for role, c in llm.contexts if role == 'critic')
    assert context['accepted_sources']
    assert set(context['accepted_sources']) == set(result['rounds'][0]['sources'])
    for relative, item in context['accepted_sources'].items():
        assert item['source'] == (workspace/relative).read_text()
        assert item['sha256'] == digest(workspace/relative)


def test_finalizer_without_summary_runs_independent_checks(tmp_path, monkeypatch):
    original = tmp_path/'original'
    flow = FullStackFlow(task(max_loops=1), CATALOG, original, ScriptedLLM(), FakeTools())
    flow.run(); (original/'summary.json').unlink()
    scripts = Path(__file__).parents[1]/'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    ns = runpy.run_path(str(scripts/'finalize_rq1_run.py'))
    from fast.fullstack.library import Library
    real_algorithm = Library.algorithm
    def measured(self, name):
        algorithm = real_algorithm(self, name)
        algorithm.measure = lambda *a, **k: {'quality_loss': .01, 'sparsity': .1}
        return algorithm
    monkeypatch.setattr(Library, 'algorithm', measured)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        output = Path(command[-1]); output.mkdir()
        (output/'summary.json').write_text('{"passed":true}')
        from types import SimpleNamespace
        return SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr('subprocess.run', run)
    monkeypatch.setattr(sys, 'argv', ['finalize', '--run', str(original), '--catalog', str(CATALOG),
        '--output', str(tmp_path/'post'), '--tool-root', str(tmp_path)])
    ns['main']()
    result = json.loads((tmp_path/'post/results.json').read_text())
    assert result['summary_recovered'] and result['qualified_pareto_rounds'] == [1]
    assert len(calls) == 2 and not (original/'summary.json').exists()
