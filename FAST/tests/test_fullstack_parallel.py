"""Concurrency/failure barriers use doubles; functional renderer runs in real-tool smoke separately."""
from dataclasses import asdict
import json
import threading
from pathlib import Path

import pytest

from fast.agents.llm_backends import Reply, VertexDirect
from fast.fullstack.contracts import SystemPlan, Module, Port
from fast.fullstack.tools import module_testbench
from test_fullstack_generation import ScriptedLLM, FakeTools, run, plan, task


class ParallelLLM(ScriptedLLM):
    def prompt(self, prompt):
        role = prompt.split('FAST ',1)[1].split(' Agent',1)[0]
        ctx = json.loads(prompt.split('CONTEXT:\n')[1])
        # These writes are used only after threads finish; never infer a response from shared last-role state.
        self.roles.append(role)
        self.contexts.append((role, ctx))
        if role == 'kernel':
            answer = {'config': {'threshold':64}, 'rationale':'test'}
        elif role == 'compiler':
            answer = plan(ctx['algorithm']['ports'])
            leaf = answer['modules'][1]
            leaf['name'] = 'Alpha'
            beta = {**leaf, 'name':'Beta', 'design_prompt':'independent Beta assignment'}
            chain = {**leaf, 'name':'Chain', 'dependencies':['Alpha'], 'design_prompt':'compose Alpha'}
            answer['modules'][0]['dependencies'] = ['Chain','Beta']
            answer['modules'].extend([beta,chain])
        elif role in ('uarch','uarch_assembly'):
            m = ctx['module']
            ports = ','.join(f'{p["direction"]} [{p["width"]-1}:0] {p["name"]}' for p in m['ports'])
            body = 'assign b=a;'
            if m['name'] == 'Chain':
                body = 'Alpha child(.a(a),.b(b));'
            if m['name'] == 'Complete':
                body = 'wire [3:0] unused; Chain c(.a(q[3:0]),.b(result)); Beta b(.a(q[7:4]),.b(unused)); assign done=start;'
            answer = {'source':f'module {m["name"]}({ports}); {body} endmodule'}
        else:
            answer = {'layer':'stop','reason':'done','instructions':'stop','evidence':['evaluation.latency_ns']}
        return Reply(json.dumps(answer))


class OverlapTools(FakeTools):
    def __init__(self):
        super().__init__()
        self.barrier = threading.Barrier(2)
        self.passed = set()
        self.lock = threading.Lock()
    def module(self, module, sources, work, language='verilog'):
        if module.name in ('Alpha','Beta'):
            self.barrier.wait(timeout=5)  # Sequential implementation fails deterministically here.
        with self.lock:
            if module.name == 'Chain':
                assert 'Alpha' in self.passed
                assert {p.stem for p in sources} == {'Alpha','Chain'}
            if module.name == 'Complete':
                assert self.passed == {'Alpha','Beta','Chain'}
            self.passed.add(module.name)
        return {'passed':True}


def test_parallel_overlap_dependencies_and_separate_assembly(tmp_path):
    flow, result, llm, _ = run(tmp_path,llm=ParallelLLM(),tools=OverlapTools(),max_loops=1,module_workers=3)
    assert result['pareto_rounds'] == [1], result['error']
    contexts = {c['module']['name']:c for role,c in llm.contexts if role in ('uarch','uarch_assembly')}
    assert contexts['Alpha']['implemented_dependencies'] == {}
    assert contexts['Beta']['compiler_prompt'] == 'independent Beta assignment'
    assert set(contexts['Chain']['implemented_dependencies']) == {'Alpha'}
    assert set(contexts['Complete']['accepted_modules']) == {'Alpha','Beta','Chain'}
    events = flow.events
    dispatch = next(e for e in events if e['stage']=='module_dispatch')
    assert set(dispatch['modules']) == {'Alpha','Beta','Chain'}
    assembly = next(i for i,e in enumerate(events) if e['stage']=='assembly_start')
    assert sum(e['stage']=='module_accepted' for e in events[:assembly]) == 3
    assert result['agent_calls']['uarch'] == 3
    assert result['agent_calls']['uarch_assembly'] == 1
    audits = list((tmp_path/'run/agent_calls').glob('round_*/build_*/*/*/*.json'))
    assert len(audits) == 4
    assert len({p.parent.parent.name for p in audits}) == 4


def test_failed_worker_prevents_assembly_ppa_and_critic(tmp_path):
    class Fail(OverlapTools):
        def module(self,module,sources,work,language='verilog'):
            super().module(module,sources,work,language)
            return {'passed':module.name!='Beta','diagnostics':'bad beta'}
    _, result, llm, tools = run(tmp_path,llm=ParallelLLM(),tools=Fail(),max_loops=1,
                                compiler_attempts=1,module_attempts=1,module_workers=3)
    assert result['status'] == 'failed'
    assert 'uarch_assembly' not in llm.roles
    assert 'critic' not in llm.roles and 'ppa' not in tools.events


def test_assembly_cannot_mutate_accepted_children(tmp_path):
    class Mutates(FakeTools):
        def verify(self,plan,sources,trusted,work):
            child = next(p for p in sources if p.stem=='Leaf')
            child.chmod(0o644)
            child.write_text(child.read_text()+'\n// unauthorized child edit')
            return super().verify(plan,sources,trusted,work)
    _, result, llm, tools = run(tmp_path,tools=Mutates(),max_loops=1,compiler_attempts=1)
    assert result['status']=='failed'
    assert 'critic' not in llm.roles and 'ppa' not in tools.events
    assert 'changed' in (tmp_path/'run/round_01/build_01/compiler_feedback.json').read_text()


def test_assembly_exhaustion_replans_with_full_feedback(tmp_path):
    _, result, llm, _ = run(tmp_path,tools=FakeTools(e2e_failures=2),max_loops=1,assembly_attempts=2)
    assert result['pareto_rounds']==[1]
    assert llm.roles.count('compiler')==2
    compiler=[c for r,c in llm.contexts if r=='compiler'][-1]
    assert 'system_verification' in str(compiler['uarch_feedback'])
    assert 'Complete.v' in compiler['uarch_feedback'][0]['implemented_sources']


def test_planner_jobs_require_frozen_functional_tests():
    obj=plan([])
    obj['modules'][1].pop('tests')
    with pytest.raises(ValueError,match='functional test'):
        SystemPlan.parse(obj,[],require_jobs=True)
    # Historical archives can still be parsed and independently revalidated.
    SystemPlan.parse(obj,[])
    obj=plan([])
    obj['modules'][1]['tests'][0]['steps'][0]['expected']['b']=16
    with pytest.raises(ValueError,match='Invalid test'):
        SystemPlan.parse(obj,[],require_jobs=True)
    for change in ({'module_workers':0},{'assembly_attempts':6}):
        with pytest.raises(ValueError):
            task(**change)


def test_module_testbench_has_bounded_clock_and_planner_expectations():
    m=Module('Leaf','', (Port('clock','input',1),Port('a','input',4),Port('b','output',4)),(),'',
             tests=({'name':'x','steps':[{'inputs':{'a':15},'cycles':2,'expected':{'b':15}}]},))
    tb=module_testbench(m)
    assert 'repeat (2)' in tb['testbench']
    assert "b !== 4'd15" in tb['testbench']
    assert tb['expected_cases']==1
    assert 'not performance evidence' in tb['coverage']


def test_vertex_forks_do_not_share_lazy_client():
    llm=VertexDirect(project='test-project',temperature=.1)
    llm._client=object()
    worker=llm.fork()
    assert worker is not llm and worker._client is None
    assert worker.project==llm.project and worker.temperature==.1


def test_compiler_repairs_invalid_job_without_losing_references(tmp_path):
    class InvalidThenValid(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='compiler':
                count=self.roles.count('compiler')
                if count==1:
                    return Reply(json.dumps({'read_templates':['register_stage']}))
                obj=json.loads(reply.result)
                obj['modules'][1]['reference_ids']=['register_stage']
                if count==2:
                    obj['modules'][1]['tests'][0]['steps'][0]['inputs']['a']=16
                return Reply(json.dumps(obj))
            return reply
    _,result,llm,_=run(tmp_path,llm=InvalidThenValid(),max_loops=1)
    assert result['pareto_rounds']==[1]
    contexts=[c for r,c in llm.contexts if r=='compiler']
    assert len(contexts)==3
    assert 'register_stage' in contexts[-1]['reference_code']
    assert 'Leaf test contract' in str(contexts[-1]['response_errors'])
    assert contexts[-1]['rejected_plan']['modules'][1]['tests'][0]['steps'][0]['inputs']['a']==16
    assert len(list((tmp_path/'run/round_01').glob('build_*')))==1


def test_repeated_functional_mismatch_escalates_to_planner(tmp_path):
    class Stuck(FakeTools):
        def module(self,module,sources,work,language='verilog'):
            return {'passed':False,'functional':{'simulation':{'diagnostics':
                f'{work}: module case=0 step=2 output=b expected=0 actual=1'}}}
    _, result, llm, _=run(tmp_path,tools=Stuck(),max_loops=1,compiler_attempts=1,module_attempts=3)
    assert result['status']=='failed'
    assert result['agent_calls']['uarch']==2
    feedback=json.loads((tmp_path/'run/round_01/build_01/compiler_feedback.json').read_text())
    assert 'Compiler must review' in feedback['error']
    assert 'uarch_assembly' not in llm.roles
