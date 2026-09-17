from dataclasses import asdict
import json
from types import SimpleNamespace
import pytest
from fast.experiments.critic_ablation import RecordingLLM, LocalRandomCritic, without_independent_feedback
from fast.agents.rediscovery_critic import CriticGuidedProposer, review_search
from fast.agents.cooptimizer import RandomProposer, CoDesignResult
from fast.agents.critic import CriticAgent
from fast.schemas.models import ArchSpecs
from test_rediscovery_critic import context, space, point
from test_kernel_search import _spec
from test_work_conservation import _kernel


def test_shadow_cannot_change_seeded_proposals_or_delegate_feedback():
    histories = [(), ()]
    agents = [CriticGuidedProposer(RandomProposer(4), c, _spec(), [],
        parent_point=asdict(point()), validation=[{'frequency_feasible': False}], apply_interventions=False)
        for c in [None, CriticAgent()]]
    for _ in range(5):
        children = [a.propose(_kernel(), ArchSpecs(data_widths=(16,)), space(), h, 1)[0]
                    for a,h in zip(agents,histories)]
        assert children[0] == children[1]
        histories = [h+(CoDesignResult(p,None,None,{},False),) for h,p in zip(histories,children)]
        assert all(a.delegate.critic_feedback == '' for a in agents)
    assert len(agents[1].events) == 5


def test_blinding_removes_independent_results_and_derived_rejection():
    ctx = context(); ctx['validation'] = [{'metrics': {'slack_ns': -.3}}]
    pure = CoDesignResult(point(), None, None, ctx['history'][0]['metrics'], True)
    blinded = without_independent_feedback(ctx, [pure])
    assert not blinded['validation']
    assert blinded['history'][0]['feasible'] and not blinded['history'][0]['violations']
    assert ctx['validation'] and not ctx['history'][0]['feasible']


def test_local_random_is_legal_single_field_without_model_lookahead():
    ctx = context()
    events = []
    result = review_search(LocalRandomCritic(3), ctx, events)
    assert result['fallback_reason'] is None
    mutation, = result['critique']['mutations']
    assert mutation['value'] in ctx['domains'][mutation['field']]
    assert mutation['value'] != ctx['parent_point'][mutation['field']]


def test_recording_persists_raw_prompt_response_and_failures(tmp_path):
    class Backend:
        def prompt(self, prompt):
            assert json.loads((tmp_path/'api_test_000.json').read_text())['state'] == 'running'
            return SimpleNamespace(result='raw reply', success=True, stderr='')
    recorder = RecordingLLM(Backend(), 'test', tmp_path)
    recorder.prompt('exact input')
    record = json.loads((tmp_path/'api_test_000.json').read_text())
    assert record['prompt'] == 'exact input' and record['response'] == 'raw reply'
    assert record['state'] == 'finished' and record['wall_seconds'] >= 0
    class Broken:
        def prompt(self, prompt):
            raise RuntimeError('test failure')
    with pytest.raises(RuntimeError):
        RecordingLLM(Broken(), 'broken', tmp_path).prompt('input')
    assert json.loads((tmp_path/'api_broken_000.json').read_text())['success'] is False


def test_trace_cache_rejects_tampering_and_task_mismatch(tmp_path):
    import hashlib
    from fast.experiments.critic_ablation import copy_cached_workload, workload_key
    design = dict(task=dict(model='m',dataset='d',sequence_length=32,head_dim=64,data_seed=1,
        capture_layer=0,capture_head=0,dtype='float32'),label='xm:16:8:32:0.75:0.05',
        point={'num_rows':16},algorithm={'block_m':32})
    payload = dict(source=dict(model='m',seq_len=32,seed=1,layer=0,head=0,token_sha256='token'),
        tile=dict(rows=16,block=32),methods={design['label']:{'complete_task':True}})
    source = tmp_path/'trace.json'
    source.write_text(json.dumps(payload))
    index = {workload_key(design):dict(file=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest())}
    (tmp_path/'index.json').write_text(json.dumps(index))
    audit=copy_cached_workload(tmp_path,design,tmp_path/'copied.json')
    assert audit['hardware_result_reused'] is False
    assert (tmp_path/'copied.json').read_bytes()==source.read_bytes()
    source.write_text('{}')
    with pytest.raises(ValueError,match='hash changed'):
        copy_cached_workload(tmp_path,design,tmp_path/'bad.json')
    source.write_text(json.dumps(payload))
    wrong=dict(design,task=dict(design['task'],model='other'))
    index[workload_key(wrong)] = index[workload_key(design)]
    (tmp_path/'index.json').write_text(json.dumps(index))
    with pytest.raises(ValueError,match='identity/coverage'):
        copy_cached_workload(tmp_path,wrong,tmp_path/'wrong.json')


def test_proxy_hypervolume_handles_dominance_duplicates_and_outside_reference():
    from scripts.analyze_critic_ablation import hypervolume
    assert hypervolume([(1,3),(2,2),(2,2),(3,3),(8,1)],(5,5)) == 11
    assert hypervolume([],(5,5)) == 0
