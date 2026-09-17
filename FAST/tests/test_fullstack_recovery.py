"""Recovery/reuse and selection-validation control-plane tests, not hardware evidence."""
import json

import pytest

from fast.fullstack.flow import FullStackFlow, DesignBuildError
from fast.fullstack.contracts import Task
from fast.agents.llm_backends import Reply
from test_fullstack_generation import CATALOG, FakeTools, ScriptedLLM, task, run


class FailSecondRound(FakeTools):
    def module(self, module, sources, work, language='verilog'):
        result = super().module(module, sources, work, language)
        if 'round_02' in work.parts:
            return {'passed': False, 'diagnostics': 'injected candidate compile failure'}
        return result


def test_failed_candidate_restores_measured_baseline_and_continues(tmp_path):
    flow, result, llm, tools = run(tmp_path, llm=ScriptedLLM('compiler'), tools=FailSecondRound(),
        max_loops=3, min_loops=3, compiler_attempts=1, module_attempts=1,
        continue_after_build_failure=True)
    assert result['status'] == 'budget_exhausted_with_failures'
    assert result['completed_design_rounds'] == [1, 3]
    assert result['failed_rounds'] == [2]
    failed = result['rounds'][1]
    assert failed['rollback_to_round'] == failed['critique_evidence_round'] == 1
    assert 'evaluation' not in failed
    assert tools.events.count('ppa') == 2
    recovery = [c for role, c in llm.contexts if role == 'critic' and c.get('failed_candidate')]
    assert len(recovery) == 1 and recovery[0]['current']['round'] == 1
    assert recovery[0]['failed_candidate']['round'] == 2
    assert recovery[0]['failed_candidate']['build_failures'][0]['error']
    assert any(e['stage'] == 'rollback' for e in flow.events)


def test_last_failed_candidate_does_not_erase_existing_pareto(tmp_path):
    _, result, _, _ = run(tmp_path, llm=ScriptedLLM('compiler'), tools=FailSecondRound(),
        max_loops=2, compiler_attempts=1, module_attempts=1, continue_after_build_failure=True)
    assert result['status'] == 'budget_exhausted_with_failures'
    assert result['pareto_rounds'] == [1]
    assert result['failed_rounds'] == [2]


def test_unchanged_verified_module_is_copied_but_reverified(tmp_path):
    flow, result, llm, tools = run(tmp_path, llm=ScriptedLLM('compiler'), max_loops=2,
                                 reuse_verified_modules=True)
    assert result['status'] == 'budget_exhausted'
    assert llm.roles.count('uarch') == 1
    assert llm.roles.count('uarch_assembly') == 2
    assert tools.events.count('module') == 4
    assert tools.events.count('e2e') == tools.events.count('ppa') == 2
    info = result['rounds'][1]['implementations']['Leaf']
    assert 'round_01' in info['reused_from'] and info['measurements_reused'] is False
    assert any(e['stage'] == 'module_revalidation' for e in flow.events)


def test_uarch_intervention_without_targets_is_not_silently_cached(tmp_path):
    _, result, llm, _ = run(tmp_path, llm=ScriptedLLM('uarch'), max_loops=2, reuse_verified_modules=True)
    assert llm.roles.count('uarch') == 2
    assert result['rounds'][1]['implementations']['Leaf']['reused_from'] is None


def test_changed_module_contract_invalidates_reuse(tmp_path):
    class ChangedPlan(ScriptedLLM):
        def prompt(self, prompt):
            reply = super().prompt(prompt)
            context = self.contexts[-1][1]
            if self.roles[-1] == 'compiler' and context.get('previous_plan'):
                value = json.loads(reply.result)
                value['modules'][1]['design_prompt'] += ' revised implementation target'
                return Reply(json.dumps(value))
            return reply
    _, result, llm, _ = run(tmp_path, llm=ChangedPlan('compiler'), max_loops=2, reuse_verified_modules=True)
    assert llm.roles.count('uarch') == 2
    assert result['rounds'][1]['implementations']['Leaf']['reused_from'] is None


def test_selection_validation_and_margin_are_enforced_without_test_data(tmp_path, monkeypatch):
    flow = FullStackFlow(task(quality_validation_seeds=[101, 211], quality_margin=.01),
                         CATALOG, tmp_path/'run', ScriptedLLM(), FakeTools())
    bound = flow.task.constraints['max_quality_loss']
    monkeypatch.setattr(flow.algorithm, 'profile', lambda c, s: {'quality_loss': bound-.02})
    seeds = []
    def measure(config, seed, count, boundaries):
        seeds.append(seed)
        assert count == 4096 and not boundaries
        return {'quality_loss': bound-.005, 'seed': seed}
    monkeypatch.setattr(flow.algorithm, 'measure', measure, raising=False)
    profile = flow.measured_profile({'threshold':64})
    assert profile['quality_loss'] == bound-.02  # original calibration measurement preserved
    assert profile['selection_quality_loss'] == bound-.005
    assert not flow.quality_acceptable(profile)
    flow.measured_profile({'threshold':64})
    assert seeds == [101, 211]  # no final-test data accessed, cached result


def test_reference_corruption_is_not_recovered_as_candidate_failure(tmp_path, monkeypatch):
    flow = FullStackFlow(task(max_loops=3, continue_after_build_failure=True),
                         CATALOG, tmp_path/'run', ScriptedLLM(), FakeTools())
    def corrupt(*args, **kwargs):
        from pathlib import Path
        source = Path(next(iter(flow.library.files.values()))['snapshot'])
        source.chmod(0o644); source.write_text('corrupted')
        raise DesignBuildError('candidate also failed')
    monkeypatch.setattr(flow, 'build', corrupt)
    result = flow.run()
    assert result['status'] == 'reference_integrity_failed'
    assert result['reference_integrity'] is False and len(result['rounds']) == 1


@pytest.mark.parametrize('kwargs', [dict(quality_validation_seeds=[1,1]),
    dict(quality_validation_samples=0),dict(quality_margin=-.01),dict(reuse_verified_modules=1)])
def test_invalid_recovery_configuration_rejected(kwargs):
    with pytest.raises(ValueError): task(**kwargs)
