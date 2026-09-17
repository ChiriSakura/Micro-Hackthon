"""Critic must change actual proposals, obey gates, and observe their outcomes."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from fast.agents.codesign import CoDesignPoint, CoDesignSpace, estimate
from fast.agents.cooptimizer import CoDesignResult
from fast.agents.critic import CriticAgent
from fast.agents.llm_critic import LLMCriticAgent
from fast.agents.rediscovery import DynaXRediscovery, RandomKernelProposer
from fast.agents.rediscovery_critic import (
    CriticGuidedProposer, read_validation_evidence, review_search, search_context,
)
from fast.schemas.models import ArchSpecs, KernelSearchSpace, to_primitive
from test_kernel_search import FakeAdapter, ScriptedLLM, _measurement, _spec
from test_work_conservation import _kernel


def point(**changes):
    return CoDesignPoint(**dict(dict(tile_q=32, tile_k=32, tile_d=64, parallelism=8,
        double_buffer=False, num_rows=16, pe_per_row=8, reg_width=16, data_width=16,
        sram_bytes=131072, queue_depth=0, divider_stages=4, bank_count=8), **changes))


def space():
    return CoDesignSpace(tile_q=(32,), tile_k=(32,), tile_d=(64,), parallelism=(8,),
        double_buffer=(False,), num_rows=(16, 32), pe_per_row=(8,), reg_width=(16,),
        sram_bytes=(131072,), queue_depth=(0, 2, 4), divider_stages=(4, 8), bank_count=(8, 16, 32))


class Proposer:
    def propose(self, kernel, specs, domain, history, count):
        seen = [h.point for h in history]
        return tuple(p for b in (8, 16, 32) if (p := point(bank_count=b)) not in seen)[:count]


def run_search(critic):
    return DynaXRediscovery(FakeAdapter(), RandomKernelProposer(0), lambda _: Proposer(),
        critic=critic).run(_spec(1), kernel_space=KernelSearchSpace(block_ms=(32,),
        xm_high=(16,), xm_low=(4,), threshold_pairs=((1.0, .1),), max_sequence_length=512),
        hardware_space=space(), specs=ArchSpecs(data_widths=(16,)), head_dim=64,
        kernel_batch=1, hardware_budget=3, hardware_batch=1)


def test_critic_changes_a_real_search_point_and_recovers_model_feasibility_at_equal_budget():
    on, off = run_search(CriticAgent()), run_search(None)
    assert len(on['designs']) == len(off['designs']) == 3
    assert on['kernel_budget_complete'] and off['kernel_budget_complete']
    assert not any(d['feasible'] for d in off['designs'])
    assert any(d['feasible'] for d in on['designs'])
    applied = [r for r in on['critic_reviews'] if r['outcome']['state'] == 'evaluated']
    assert applied and applied[0]['outcome']['after']['divider_stages'] == 8
    assert applied[0]['outcome']['model_frontier_extended']
    assert applied[0]['outcome']['independent_improvement'] is None
    assert any(d['critic_review_id'] == applied[0]['review_id'] for d in on['designs'])
    assert not off['critic_reviews']


def context():
    p = point()
    metrics = estimate(p, _kernel(), 512, head_dim=64, block_m=32, kept_per_block=16)
    return search_context(_spec(), _kernel(), ArchSpecs(data_widths=(16,)), space(),
        (CoDesignResult(p, None, None, metrics, False, ('clock below 350 MHz',)),))


def payload(**changes):
    return dict(dict(attribution='compiler', decision='continue', summary='pipeline hypothesis',
        evidence=['history.0.metrics.max_frequency_mhz'], mutations=[dict(layer='compiler',
        field='divider_stages', operation='set', value=8, expected_effect='test clock recovery', risk='area')]), **changes)


def test_llm_critic_uses_actual_domains_and_records_a_successful_analysis():
    llm = ScriptedLLM(json.dumps(payload()))
    critic = LLMCriticAgent(llm)
    events = []
    review = review_search(critic, context(), events)
    assert review['critique']['mutations'][0]['value'] == 8
    assert review['llm_call']['successful'] and review['fallback_reason'] is None
    assert 'CONTEXT:' in llm.prompts[0]
    assert 'execution array critical path   2.230' not in llm.prompts[0]


def test_hardware_root_cause_can_dispatch_a_compiler_parameter_change():
    critic = LLMCriticAgent(ScriptedLLM(json.dumps(payload(attribution='uarch'))))
    review = review_search(critic, context(), [])
    assert review['fallback_reason'] is None
    assert review['critique']['attribution'] == 'uarch'
    assert review['critique']['mutations'][0]['layer'] == 'compiler'


@pytest.mark.parametrize('bad', [
    payload(attribution='The scheduler failed timing'),
    payload(evidence=['invented.clock']),
    payload(mutations=[dict(layer='compiler', field='divider_stages', operation='set', value=999,
                           expected_effect='faster', risk='')]),
    payload(mutations=[dict(layer='compiler', field='target_mhz', operation='set', value=50,
                           expected_effect='relax gate', risk='')]),
    payload(mutations=[dict(layer='compiler', field='divider_stages', operation='set', value=4,
                           expected_effect='repeat', risk='')]),
])
def test_invalid_llm_action_is_rejected_and_falls_back_visibly(bad):
    critic = LLMCriticAgent(ScriptedLLM(json.dumps(bad)))
    review = review_search(critic, context(), [])
    assert review['fallback_reason']
    assert not review['llm_call']['successful']
    assert review['critique']['mutations'][0]['value'] == 8


def test_no_gain_is_recorded_as_no_gain_instead_of_success():
    ctx = context()
    parent = point(divider_stages=8)
    old = CoDesignResult(parent, None, None, dict(ctx['history'][0]['metrics'], seconds=1, energy_j=1), True)
    class SetQueue:
        def review_search(self, context):
            return LLMCriticAgent(ScriptedLLM(json.dumps(payload(mutations=[dict(
                layer='compiler', field='queue_depth', operation='set', value=2,
                expected_effect='test utilisation', risk='timing')])))).review_search(context)
    events = []
    guided = CriticGuidedProposer(Proposer(), SetQueue(), _spec(), events)
    child, = guided.propose(_kernel(), ArchSpecs(data_widths=(16,)), space(), (old,), 1)
    guided.observe((old, CoDesignResult(child, None, None, dict(old.metrics, seconds=2, energy_j=2), True)))
    assert events[0]['outcome']['state'] == 'evaluated'
    assert events[0]['outcome']['model_frontier_extended'] is False


def test_kernel_intervention_is_measured_and_cannot_bypass_quality_budget():
    labels = ('xm:8:4:32:1:0.1', 'xm:16:4:32:1:0.1')
    domain = KernelSearchSpace(block_ms=(32,), xm_high=(8, 16), xm_low=(4,),
                              threshold_pairs=((1.0, .1),), max_sequence_length=512)
    labels = domain.labels()
    class Kernel:
        name = 'first-only'
        def propose(self, spec, space, history, count):
            from fast.schemas.models import KernelCandidate
            return (KernelCandidate(labels[0], self.name),)
    adapter = FakeAdapter({labels[0]: (.2, .9), labels[1]: (.01, .7)})
    result = DynaXRediscovery(adapter, Kernel(), lambda _: Proposer()).run(
        _spec(2), kernel_space=domain, hardware_space=space(), specs=ArchSpecs(), head_dim=64,
        kernel_batch=1, hardware_budget=1, hardware_batch=1)
    assert adapter.batches == [(labels[0],), (labels[1],)]
    assert result['rounds'][0]['hardware_evaluated'] == 0
    assert result['measurements'][1]['proposed_by'] == 'critic'
    assert any(r['outcome'].get('quality_passed') is True for r in result['critic_reviews'])


@pytest.mark.parametrize('overrides', [
    {'design_id': 'different'}, {'sources_unchanged': False},
    {'complete_captured_task': False}, {'fixed_frequency_mhz': 100}, {'results': []},
])
def test_independent_gate_does_not_accept_stale_or_incomplete_evidence(tmp_path, overrides):
    data = dict(design_id='design', sources_unchanged=True, complete_captured_task=True,
        fixed_frequency_mhz=350, scope='scheduler', results=[dict(passed=True,
        frequency_feasible=True, metrics={'slack_ns': .1})])
    path = tmp_path/'validation.json'
    path.write_text(json.dumps({**data, **overrides}))
    accepted, observations = read_validation_evidence(path, 'design', 350)
    assert not accepted and observations


def test_repair_analyzes_each_new_independent_failure_before_next_proposal(tmp_path, monkeypatch):
    from scripts import refine_rediscovery
    p = point(queue_depth=4, divider_stages=8)
    kernel = _measurement('xm:16:4:32:1:0.1', .01, .8)
    metrics = estimate(p, _kernel(), 512, head_dim=64, block_m=32, kept_per_block=16)
    source = tmp_path/'source'
    evidence = source/'candidates'/'parent'/'rtl'
    evidence.mkdir(parents=True)
    config = dict(task=dict(model='test', dataset='wikitext-2-raw-v1', sequence_length=512,
        head_dim=64, epsilon=.05, data_seed=1, capture_layer=0, capture_head=0),
        hardware_space=asdict(space()), constraints=asdict(ArchSpecs(data_widths=(16,))))
    parent = dict(design_id='parent', label=kernel.label, point=asdict(p), metrics=metrics, feasible=True)
    (source/'search.json').write_text(json.dumps(dict(frontier=[parent], designs=[parent],
        measurements=[to_primitive(kernel)], config=config, search_seed=0)))
    (evidence/'validation.json').write_text(json.dumps(dict(design_id='parent', scope='scheduler',
        results=[dict(passed=True, frequency_feasible=False, metrics={'slack_ns': -.3})])))
    def run(command, **kwargs):
        if str(command[1]).endswith('validate_pareto_scheduler.py'):
            directory = Path(command[command.index('--out')+1]); directory.mkdir()
            design = json.loads(Path(command[command.index('--design')+1]).read_text())
            passed = design['point']['queue_depth'] == 0
            (directory/'validation.json').write_text(json.dumps(dict(
                design_id=design['design_id'], scope='scheduler', sources_unchanged=True,
                complete_captured_task=True, fixed_frequency_mhz=350,
                results=[dict(passed=True, frequency_feasible=passed, latency_s=1e-6 if passed else None,
                              metrics={'slack_ns': .1 if passed else -.1, 'cycles': 350})])))
            return SimpleNamespace(returncode=0 if passed else 1)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(refine_rediscovery.subprocess, 'run', run)
    monkeypatch.setattr(sys, 'argv', ['refine', '--source', str(source), '--out', str(tmp_path/'out'),
        '--dynax-python', 'python', '--method', 'random', '--critic', 'rule', '--budget', '2',
        '--containers', str(tmp_path), '--liberty', str(tmp_path/'lib')])
    assert refine_rediscovery.main() == 0
    result = json.loads((tmp_path/'out/refinement.json').read_text())
    assert [c['point']['queue_depth'] for c in result['candidates']] == [2, 0]
    assert result['budget_complete'] and len(result['critic_reviews']) == 2
    second = result['critic_reviews'][1]
    assert second['context']['validation'][0]['metrics']['slack_ns'] == -.1
    assert second['outcome']['independent_constraint_recovered']
    assert second['outcome']['independent_energy_improvement'] is None
