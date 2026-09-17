"""Control-plane tests use explicit doubles; they are not RTL/PPA evidence."""
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from fast.agents.llm_backends import Reply
from fast.fullstack.agents import validate_critique
from fast.fullstack.contracts import Module, Port, SystemPlan, Task, pareto
from fast.fullstack.flow import FullStackFlow
from fast.fullstack.library import Library
from fast.fullstack.tools import check_source

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'libraries/catalog.json'


def task(**changes):
    obj = json.loads((ROOT/'configs/fullstack/threshold_attention.json').read_text())
    obj.update(changes)
    return Task.parse(obj)


def plan(ports):
    return {'top': 'Complete', 'rationale': 'test plan', 'modules': [
        {'name': 'Complete', 'purpose': 'top', 'ports': ports,
         'dependencies': ['Leaf'], 'implementation': 'instantiate leaf'},
        {'name': 'Leaf', 'purpose': 'test child', 'ports': [
            {'name':'a','direction':'input','width':4},
            {'name':'b','direction':'output','width':4}],
         'dependencies': [], 'implementation': 'pass through'}]}


def source(module):
    ports = ', '.join(f'{p["direction"]} '+(f'[{p["width"]-1}:0] ' if p['width']>1 else '')+p['name']
                      for p in module['ports'])
    body = 'Leaf leaf(.a(q[3:0]),.b(result)); assign done=start;' if module['name']=='Complete' else 'assign b=a;'
    return f'module {module["name"]}({ports}); {body} endmodule'


class ScriptedLLM:
    def __init__(self, layer='uarch', malformed=False):
        self.roles = []
        self.contexts = []
        self.layer, self.malformed = layer, malformed

    def prompt(self, prompt):
        role = prompt.split('FAST ', 1)[1].split(' Agent',1)[0]
        ctx = json.loads(prompt.split('CONTEXT:\n')[1])
        self.roles.append(role)
        self.contexts.append((role, ctx))
        if role=='kernel':
            answer = {'config': {'threshold': 64}, 'rationale': 'test'}
        elif role=='compiler':
            answer = plan(ctx['algorithm']['ports'])
        elif role=='uarch':
            answer = {'rtl': source(ctx['module']), 'rationale': 'test'}
            if self.malformed:
                answer = {'rtl': 'module Wrong(); endmodule'}
        else:
            answer = {'layer': self.layer, 'reason': 'test measured latency',
                      'instructions':'pipeline datapath', 'evidence':['evaluation.latency_ns']}
        return Reply(json.dumps(answer))


class FakeTools:
    def __init__(self, module_failures=0, e2e_failures=0, ppa_complete=True):
        self.events=[]
        self.module_failures, self.e2e_failures, self.ppa_complete = module_failures, e2e_failures, ppa_complete

    def module(self, module, sources, work, language="verilog"):
        self.events.append('module')
        fail = self.module_failures>0
        self.module_failures-=1
        return {'passed':not fail,'diagnostics':'injected lint diagnostic' if fail else ''}

    def verify(self, plan, sources, trusted, work):
        self.events.append('e2e')
        fail = self.e2e_failures>0
        self.e2e_failures-=1
        return {'passed':not fail,'mean_cycles':7,'expected_cases':trusted['expected_cases']}

    def evaluate(self, plan, sources, verification, profile, task, work):
        assert verification['passed']
        self.events.append('ppa')
        return {'complete':self.ppa_complete,'feasible':self.ppa_complete,
                'energy_nj':2.,'latency_ns':70., 'area_um2':100., 'quality_loss':profile['quality_loss']}


def run(tmp_path, llm=None, tools=None, **changes):
    llm, tools = llm or ScriptedLLM(), tools or FakeTools()
    flow = FullStackFlow(task(**changes), CATALOG, tmp_path/'run', llm, tools)
    return flow, flow.run(), llm, tools


def test_dynamic_graph_orders_dependencies_and_rejects_disconnected_cycles(tmp_path):
    library=Library(CATALOG, tmp_path)
    ports=library.algorithm('threshold_attention').describe()['ports']
    obj=plan(ports)
    assert [m.name for m in SystemPlan.parse(obj, ports).modules]==['Leaf','Complete']
    obj['modules'][1]['dependencies']=['Complete']
    with pytest.raises(ValueError,match='Cyclic'):
        SystemPlan.parse(obj,ports)
    obj=plan(ports)
    obj['modules'][0]['dependencies']=[]
    with pytest.raises(ValueError,match='disconnected'):
        SystemPlan.parse(obj,ports)


def test_library_snapshot_and_unknown_algorithm(tmp_path):
    library=Library(CATALOG,tmp_path)
    library.check()
    with pytest.raises(ValueError,match='No fallback'):
        library.algorithm('dynax_missing_contract')
    copy=Path(next(iter(library.files.values()))['snapshot'])
    copy.chmod(0o644)
    copy.write_text('changed')
    with pytest.raises(RuntimeError,match='changed'):
        library.check()


def test_reference_detects_external_library_edit(tmp_path):
    source_file=tmp_path/'plugin.py'
    source_file.write_text('old')
    manifest=tmp_path/'catalog.json'
    manifest.write_text(json.dumps({'version':1,'algorithms':{},'hardware_templates':{'x':'plugin.py'}}))
    work=tmp_path/'work'; work.mkdir()
    library=Library(manifest,work)
    source_file.write_text('new')
    with pytest.raises(RuntimeError,match='changed'):
        library.check()


def test_trusted_profile_and_verification_are_independent(tmp_path):
    alg=Library(CATALOG,tmp_path).algorithm('threshold_attention')
    profile=alg.profile({'threshold':0},17)
    assert profile['quality_loss']==0
    verification=alg.verification({'threshold':64},17,'Complete')
    assert verification['expected_cases']==100
    assert 'FAST_PASS' in verification['testbench']
    assert alg.reference({'threshold':64},([0,0],[[15,15]]*4,[15]*4))==0
    assert alg.reference({'threshold':64},([15,15],[[15,15]]*4,[15]*4))==15


@pytest.mark.parametrize('bad', ['`include "library.v"', 'initial $finish;', 'initial begin end', '$readmemh("golden",x);'])
def test_source_rejects_simulation_and_reference_access(bad):
    module=Module('Leaf','', (Port('a','input',4),Port('b','output',4)), (), '')
    with pytest.raises(ValueError):
        check_source('module Leaf(input [3:0] a, output [3:0] b); '+bad+' endmodule',module)


def test_source_contract_and_declared_topology():
    module=Module('Leaf','', (Port('a','input',4),Port('b','output',4)), (), '')
    check_source('module Leaf(input [3:0] a, output [3:0] b); assign b=a; endmodule',module)
    with pytest.raises(ValueError,match='Ports'):
        check_source('module Leaf(input [2:0] a, output [3:0] b); assign b=a; endmodule',module)
    with pytest.raises(ValueError,match='children'):
        check_source('module Leaf(input [3:0] a, output [3:0] b); Hidden h(.a(a),.b(b)); endmodule',module)


def test_critic_after_e2e_and_ppa_reenters_uarch(tmp_path):
    flow,result,llm,tools=run(tmp_path)
    assert result['status']=='budget_exhausted'
    assert result['reference_integrity']
    assert llm.roles==['kernel','compiler','uarch','uarch','critic','uarch','uarch','critic']
    stages=[e['stage'] for e in flow.events]
    assert stages.index('e2e') < stages.index('ppa') < stages.index('critic')
    assert result['rounds'][0]['critique_applied'] is True
    assert result['rounds'][1]['critique_applied'] is False
    assert result['pareto_rounds']==[1,2]
    assert (tmp_path/'run/agent_calls/uarch/0001.json').exists()


def test_failed_module_repaired_inside_uarch_without_critic(tmp_path):
    _,result,llm,_=run(tmp_path,tools=FakeTools(module_failures=1),max_loops=1)
    assert result['pareto_rounds']==[1]
    assert llm.roles[:5]==['kernel','compiler','uarch','uarch','uarch']
    repair_ctx=[ctx for role,ctx in llm.contexts if role=='uarch'][1]
    assert 'injected lint diagnostic' in str(repair_ctx['feedback'])


def test_e2e_failure_returns_to_compiler_before_critic(tmp_path):
    _,result,llm,_=run(tmp_path,tools=FakeTools(e2e_failures=1),max_loops=1)
    assert result['pareto_rounds']==[1]
    assert llm.roles.count('compiler')==2
    assert llm.roles[-1]=='critic'
    ctx=[ctx for role,ctx in llm.contexts if role=='compiler'][1]
    assert 'Whole-system verification failed' in str(ctx['uarch_feedback'])
    assert 'Complete.v' in ctx['uarch_feedback'][0]['implemented_sources']


def test_never_calls_critic_or_ppa_for_unbuilt_system(tmp_path):
    _,result,llm,tools=run(tmp_path,llm=ScriptedLLM(malformed=True),max_loops=1)
    assert result['status']=='failed'
    assert result['pareto_rounds']==[]
    assert 'critic' not in llm.roles and 'ppa' not in tools.events


def test_never_calls_critic_for_missing_ppa(tmp_path):
    _,result,llm,_=run(tmp_path,tools=FakeTools(ppa_complete=False),max_loops=1)
    assert result['status']=='ppa_failed'
    assert 'critic' not in llm.roles


def test_kernel_reentry_discards_previous_design(tmp_path):
    _,result,llm,_=run(tmp_path,llm=ScriptedLLM(layer='kernel'))
    assert result['agent_calls']['kernel']==2
    contexts=[ctx for role,ctx in llm.contexts if role=='compiler']
    assert contexts[1]['previous_plan'] is None
    assert all(ctx['previous_implementation'] is None for role,ctx in llm.contexts if role=='uarch')


def test_invalid_evidence_and_budget_are_rejected():
    with pytest.raises(ValueError,match='Unknown'):
        validate_critique({'layer':'uarch','reason':'x','instructions':'x','evidence':['evaluation.imaginary']}, {'evaluation':{}})
    for limit in (0,6):
        with pytest.raises(ValueError):
            task(max_loops=limit)
    records=[{'round':i,'evaluation':dict(feasible=ok,energy_nj=e,latency_ns=l)}
             for i,ok,e,l in [(1,True,2,4),(2,True,3,5),(3,True,1,6),(4,False,.1,.1)]]
    assert pareto(records)==[1,3]


def test_valid_non_ansi_and_parameterized_children():
    module=Module('Leaf','', (Port('a','input',4),Port('b','output',4)), (), '')
    check_source('module Leaf(a,b); input [3:0] a; output [3:0] b; assign b=a; endmodule',module)
    parent=Module('Parent','',module.ports,('Leaf',),'')
    check_source('module Parent(input [3:0] a, output [3:0] b); Leaf #(.T(4)) leaf(.a(a),.b(b)); endmodule',parent)


def test_chisel_source_contract_and_external_code_rejection():
    from fast.fullstack.tools import check_chisel_source
    leaf=Module('Leaf','', (Port('a','input',4),Port('b','output',4)), (), '')
    good='import chisel3._\nclass Leaf extends RawModule { val a=IO(Input(UInt(4.W))); val b=IO(Output(UInt(4.W))); b:=a }'
    check_chisel_source(good,leaf)
    for bad in [good.replace('RawModule','Module'), good+'\nobject Main extends App {}',
                good+'\n//> using dep "bad:dependency:1"', good.replace('b:=a','java.nio.file.Files.delete(null)')]:
        with pytest.raises(ValueError):
            check_chisel_source(bad,leaf)


def test_chisel_port_check_on_emitted_verilog():
    from fast.fullstack.tools import check_verilog_ports
    module=Module('Leaf','', (Port('a','input',4),Port('b','output',4)), (), '')
    check_verilog_ports('module Leaf(\n input [3:0] a,\n output [3:0] b\n); assign b=a; endmodule',module)
    with pytest.raises(ValueError,match='Ports'):
        check_verilog_ports('module Leaf(input [3:0] io_a, output [3:0] io_b); endmodule',module)


def test_chisel_generation_uses_emitted_top_for_verification_and_ppa(tmp_path):
    class ChiselLLM(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            role,ctx=self.contexts[-1]
            if role=='compiler':
                obj=json.loads(reply.result);obj['language']='chisel'
                return Reply(json.dumps(obj))
            if role=='uarch':
                m=ctx['module']
                children=';'.join(f'val child{i}=Module(new {name})' for i,name in enumerate(m['dependencies']))
                return Reply(json.dumps({'source':f'import chisel3._\nclass {m["name"]} extends RawModule {{ {children} }}'}))
            return reply
    class ChiselTools(FakeTools):
        def module(self,module,sources,work,language='verilog'):
            assert language=='chisel' and all(p.suffix=='.scala' for p in sources)
            emitted=work/(module.name+'.v');emitted.write_text(source(asdict(module)))
            return {'passed':True,'elaborated_verilog':str(emitted)}
        def verify(self,plan,sources,trusted,work):
            assert len(sources)==1 and sources[0].name==plan.top+'.v'
            return super().verify(plan,sources,trusted,work)
        def evaluate(self,plan,sources,*args):
            assert len(sources)==1 and sources[0].suffix=='.v'
            return super().evaluate(plan,sources,*args)
    _,result,llm,_=run(tmp_path,llm=ChiselLLM(),tools=ChiselTools(),hdl='chisel',max_loops=1)
    assert result['pareto_rounds']==[1]
    assert all(name.endswith('.scala') for name in result['rounds'][0]['sources'])
    assert all(name.endswith('.v') for name in result['rounds'][0]['rtl_sources'])


def test_explicit_language_constraint_is_enforced(tmp_path):
    _,result,llm,tools=run(tmp_path,hdl='chisel',max_loops=1)
    assert result['status']=='failed'
    assert 'uarch' not in llm.roles


def test_critic_schema_error_retried_without_another_design(tmp_path):
    class BadThenValid(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='critic' and self.roles.count('critic')==1:
                obj=json.loads(reply.result);obj['evidence']=['evaluation.invented']
                return Reply(json.dumps(obj))
            return reply
    flow,result,llm,tools=run(tmp_path,llm=BadThenValid(),max_loops=1)
    assert result['pareto_rounds']==[1]
    assert llm.roles.count('critic')==2
    assert tools.events.count('ppa')==1
    context=[ctx for role,ctx in llm.contexts if role=='critic'][-1]
    assert context['validation_feedback']
    assert 'evaluation.latency_ns' in context['available_evidence']


def test_kernel_survey_skips_illegal_parameter_combinations(tmp_path):
    flow=FullStackFlow(task(max_loops=1),CATALOG,tmp_path/'run',ScriptedLLM(),FakeTools())
    flow.contract['config_space']['threshold']=[-1,0,64]
    result=flow.run()
    survey=json.loads((tmp_path/'run/kernel_survey.json').read_text())
    assert survey['invalid_combinations'][0]['config']=={'threshold':-1}
    assert len(survey['profiles'])==2
    assert result['pareto_rounds']==[1]


@pytest.mark.parametrize('power,slack,credible,complete,feasible', [
    (.001,1.,True,True,True), (.001,-1.,True,True,False),
    (.001,1.,False,True,False), (None,1.,True,False,False),
    (float('nan'),1.,True,False,False)])
def test_physical_acceptance_requires_complete_real_metrics(tmp_path,monkeypatch,power,slack,credible,complete,feasible):
    import fast.fullstack.tools as module
    from fast.adapters.synthesis import SynthesisResult
    from fast.adapters.timing import TimingResult
    class Synthesis:
        def __init__(self,*args,**kwargs): pass
        def synthesize(self,*args,**kwargs):
            return SynthesisResult(True,'Complete','nangate45',100.,10)
    class Timing:
        def __init__(self,*args,**kwargs): pass
        def analyse(self,*args,**kwargs):
            return TimingResult(True,'Complete','nangate45',10.,slack_ns=slack,
                                timing_credible=credible,total_power_w=power)
    monkeypatch.setattr(module,'YosysSynthesisAdapter',Synthesis)
    monkeypatch.setattr(module,'OpenStaTimingAdapter',Timing)
    source_file=tmp_path/'input.v';source_file.write_text('module Complete(); endmodule')
    result=module.RtlTools(tmp_path).evaluate(SystemPlan('Complete',(),''),[source_file],
        {'passed':True,'mean_cycles':7},{'quality_loss':0},task(),tmp_path)
    assert result['complete'] is complete and result['feasible'] is feasible
    if complete:
        assert result['energy_nj']==pytest.approx(.07)
        assert result['latency_ns']==70


def test_uarch_can_request_compiler_architecture_revision(tmp_path):
    class RequestsReplan(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='uarch' and self.roles.count('uarch')==1:
                return Reply(json.dumps({'replan_reason':'The child handshake cannot represent backpressure; revise interfaces.'}))
            return reply
    _,result,llm,_=run(tmp_path,llm=RequestsReplan(),max_loops=1)
    contexts=[ctx for role,ctx in llm.contexts if role=='compiler']
    assert len(contexts)==2
    assert 'backpressure' in str(contexts[1]['uarch_feedback'])
    assert result['pareto_rounds']==[1]


def test_critic_off_replans_without_claiming_critic_intervention(tmp_path):
    llm=ScriptedLLM()
    flow=FullStackFlow(task(),CATALOG,tmp_path/'run',llm,FakeTools(),critic_enabled=False)
    result=flow.run()
    assert result['agent_calls']['critic']==0
    assert result['agent_calls']['compiler']==2
    assert len(result['rounds'])==2
    assert all('critique' not in r for r in result['rounds'])


def test_uarch_api_failure_retries_current_module_without_replanning(tmp_path):
    class FailsOnce(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='uarch' and self.roles.count('uarch')==1:
                return Reply('',success=False,stderr='transient timeout')
            return reply
    _,result,llm,_=run(tmp_path,llm=FailsOnce(),max_loops=1)
    assert result['pareto_rounds']==[1]
    assert llm.roles.count('compiler')==1
    contexts=[ctx for role,ctx in llm.contexts if role=='uarch']
    assert contexts[0]['module']['name']==contexts[1]['module']['name']
    assert 'transient timeout' in str(contexts[1]['feedback'])


def test_artifact_revalidation_rejects_changed_generated_sources(tmp_path):
    from scripts.revalidate_generated_design import revalidate
    _,result,_,_=run(tmp_path,max_loops=1)
    artifact=next(iter(result['rounds'][0]['sources']))
    (tmp_path/'run'/artifact).write_text('tampered')
    with pytest.raises(ValueError,match='integrity'):
        revalidate(tmp_path/'run',1,CATALOG,tmp_path/'recheck',FakeTools())
    assert not (tmp_path/'recheck').exists()


def test_artifact_revalidation_uses_tools_without_llm(tmp_path):
    from scripts.revalidate_generated_design import revalidate
    run(tmp_path,max_loops=1)
    result=revalidate(tmp_path/'run',1,CATALOG,tmp_path/'recheck',FakeTools())
    assert result['passed'] and result['llm_calls']==0


@pytest.mark.parametrize('explicit_request',[True,False])
def test_compiler_retrieves_and_assigns_module_specific_reference_code(tmp_path,explicit_request):
    class RetrievalLLM(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='compiler':
                if explicit_request and self.roles.count('compiler')==1:
                    return Reply(json.dumps({'read_templates':['register_stage','chisel_carry_and_clock']}))
                obj=json.loads(reply.result)
                obj['modules'][0]['reference_ids']=['register_stage']
                obj['modules'][1]['reference_ids']=['chisel_carry_and_clock']
                return Reply(json.dumps(obj))
            return reply
    flow,result,llm,_=run(tmp_path,llm=RetrievalLLM(),max_loops=1)
    assert result['pareto_rounds']==[1]
    compiler_contexts=[ctx for role,ctx in llm.contexts if role=='compiler']
    assert len(compiler_contexts)==2
    assert compiler_contexts[0]['reference_code']=={}
    assert len(compiler_contexts[0]['hardware_catalog'])>=3
    assert set(compiler_contexts[1]['reference_code'])=={'register_stage','chisel_carry_and_clock'}
    uarch_contexts=[ctx for role,ctx in llm.contexts if role=='uarch']
    assert set(uarch_contexts[0]['reference_code'])=={'chisel_carry_and_clock'}
    assert set(uarch_contexts[1]['reference_code'])=={'register_stage'}
    assert all('templates' not in ctx for ctx in uarch_contexts)
    assert uarch_contexts[0]['reference_provenance'][0]['sha256']
    assert 'compiler_library_read' in [e['stage'] for e in flow.events]
    bindings=json.loads((tmp_path/'run/round_01/build_01/reference_bindings.json').read_text())
    assert bindings['Leaf'][0]['id']=='chisel_carry_and_clock'


def test_unknown_compiler_reference_is_rejected_before_uarch(tmp_path):
    class BadReference(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='compiler':
                obj=json.loads(reply.result);obj['modules'][0]['reference_ids']=['../../escape']
                return Reply(json.dumps(obj))
            return reply
    _,result,llm,_=run(tmp_path,llm=BadReference(),max_loops=1)
    assert result['status']=='failed'
    assert 'uarch' not in llm.roles


def test_chisel_allows_bundle_helpers_but_not_redefined_child_modules():
    from fast.fullstack.tools import check_chisel_source
    module=Module('Divider','',(),(),'')
    source='''import chisel3._
class Divider extends RawModule {
 private class DivState extends Bundle { val valid = Bool(); val quotient = UInt(16.W) }
 val state = Wire(new DivState)
 state.valid := false.B
 state.quotient := 0.U
}
'''
    check_chisel_source(source,module)
    with pytest.raises(ValueError,match='requested hardware'):
        check_chisel_source(source+'\nclass Extra extends RawModule {}',module)


def test_compiler_response_retry_retains_retrieved_reference_code(tmp_path):
    class RetryCompiler(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='compiler':
                n=self.roles.count('compiler')
                if n==1:return Reply(json.dumps({'read_templates':['register_stage']}))
                if n==2:return Reply('{}\n{}')
                obj=json.loads(reply.result);obj['modules'][0]['reference_ids']=['register_stage']
                return Reply(json.dumps(obj))
            return reply
    _,result,llm,_=run(tmp_path,llm=RetryCompiler(),max_loops=1)
    assert result['pareto_rounds']==[1]
    contexts=[ctx for role,ctx in llm.contexts if role=='compiler']
    assert len(contexts)==3 and contexts[-1]['response_errors']
    assert set(contexts[-1]['reference_code'])=={'register_stage'}
    assert len(list((tmp_path/'run/round_01').glob('build_*')))==1
