"""Reference propagation and matched-baseline integrity, not hardware evidence."""
import json
from pathlib import Path

import pytest

from fast.fullstack.library import Library
from fast.fullstack.flow import FullStackFlow
from fast.fullstack.contracts import pareto
from test_fullstack_generation import CATALOG, FakeTools, ScriptedLLM, task


def test_golden_references_frozen_and_bound_to_selected_module(tmp_path):
    library = Library(CATALOG, tmp_path)
    refs = library.test_references(['pipelined_divider'])
    assert set(refs) == {'pipelined_divider'}
    assert 'out_valid' in refs['pipelined_divider'][0]['code']
    assert refs['pipelined_divider'][0]['sha256']
    assert library.test_references(['register_stage']) == {'register_stage': []}
    copy = Path(library.files['test:pipelined_divider:0']['snapshot'])
    copy.chmod(0o644); copy.write_text('changed golden')
    with pytest.raises(RuntimeError, match='changed'):
        library.check()


def test_efficiency_pareto_excludes_invalid_and_retains_tradeoffs():
    def point(i, latency, energy, feasible=True):
        return {'round':i, 'evaluation':{'feasible':feasible,'latency_ns':latency,'energy_nj':energy}}
    assert pareto([point(1,100,10),point(2,50,20),point(3,150,15),point(4,1,0),
                   point(5,1,float('nan')),point(6,1,1,False)]) == [1,2]


def test_shared_initial_design_rebuilt_without_initial_agent_calls(tmp_path):
    base = FullStackFlow(task(max_loops=1), CATALOG, tmp_path/'base', ScriptedLLM(), FakeTools()).run()
    assert base['pareto_rounds']
    llm, tools = ScriptedLLM(layer='compiler'), FakeTools()
    result = FullStackFlow(task(max_loops=2), CATALOG, tmp_path/'next', llm, tools,
                           initial_run=tmp_path/'base').run()
    assert result['error'] is None
    assert result['rounds'][0]['reentry'] == 'shared_initial_design'
    assert llm.roles[0] == 'critic'
    assert llm.roles.count('kernel') == 0
    assert tools.events.count('ppa') == 2
    record = base['rounds'][0]
    source = tmp_path/'base'/next(iter(record['sources']))
    source.chmod(0o644); source.write_text('tampered')
    bad = FullStackFlow(task(max_loops=1), CATALOG, tmp_path/'bad', ScriptedLLM(), FakeTools(),
                        initial_run=tmp_path/'base').run()
    assert bad['status'] == 'failed'
    assert 'integrity failed' in bad['error']
    assert bad['agent_calls']['critic'] == 0


def test_infeasible_critic_kernel_proposal_never_reaches_compiler(tmp_path):
    from fast.agents.llm_backends import Reply
    class BadKernelAdvice(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='critic':
                d=json.loads(reply.result)
                d.update(layer='kernel',proposed_config={'threshold':128},instructions='Implement threshold 128')
                return Reply(json.dumps(d))
            return reply
    llm=BadKernelAdvice()
    result=FullStackFlow(task(max_loops=2,module_attempts=2),CATALOG,tmp_path/'bad_advice',llm,FakeTools()).run()
    assert result['status']=='failed' and 'quality constraint' in result['error']
    assert len(result['rounds'])==1
    assert llm.roles.count('compiler')==1
    assert llm.roles.count('critic')==2
    retry=[c for role,c in llm.contexts if role=='critic'][-1]
    assert any(p['config']=={'threshold':128} and p['quality_loss']>.15 for p in retry['measured_config_profiles'])


def test_kernel_resolution_replaces_stale_parameter_instructions(tmp_path):
    from fast.agents.llm_backends import Reply
    class Advice(ScriptedLLM):
        def prompt(self,prompt):
            reply=super().prompt(prompt)
            if self.roles[-1]=='critic':
                d=json.loads(reply.result)
                d.update(layer='kernel',proposed_config={'threshold':0},instructions='Use threshold zero')
                return Reply(json.dumps(d))
            return reply
    llm=Advice()
    result=FullStackFlow(task(max_loops=2),CATALOG,tmp_path/'resolve',llm,FakeTools()).run()
    assert result['error'] is None
    ctx=[c for role,c in llm.contexts if role=='compiler'][-1]
    assert ctx['config']=={'threshold':64}  # Kernel double intentionally chooses a different legal configuration.
    assert 'Use threshold zero' not in ctx['critic']['instructions']
    assert 'Kernel-approved' in ctx['critic']['instructions']


def test_native_library_closure_is_frozen_deduplicated_and_explicit(tmp_path):
    from fast.fullstack.contracts import Module
    from fast.fullstack.tools import check_chisel_source
    library = Library(CATALOG, tmp_path)
    ids = ['attention_tile_system_reference', 'attention_tile_reference']
    sources = library.linked_sources(ids)
    assert len(sources) == 17
    assert len(set(sources)) == 17
    symbols = library.linked_symbols(ids)
    assert 'predict_unit.FixedPointDivPipelined' in symbols['classes']
    assert 'AttentionTileSystem' in symbols['classes']
    module = Module('Adapter', '', (), (), '', reference_ids=('pipelined_divider',),
                    linked_reference_ids=('pipelined_divider',))
    source = '''import chisel3._
import predict_unit.FixedPointDivPipelined
class Adapter extends RawModule {
 val core = Module(new FixedPointDivPipelined())
}'''
    with pytest.raises(ValueError):
        check_chisel_source(source, module)
    library.check_generated(source, module, 'chisel')
    with pytest.raises(ValueError, match='children'):
        library.check_generated(source.replace('new FixedPointDivPipelined()', 'new UnknownCore()'), module, 'chisel')
    support = Path(library.files['support:attention_tile_system_reference:0']['snapshot'])
    support.chmod(0o644); support.write_text('changed dependency')
    with pytest.raises(RuntimeError, match='changed'):
        library.check()


def test_native_links_must_be_assigned_chisel_references():
    from fast.fullstack.contracts import SystemPlan
    obj = {'top':'Top', 'language':'chisel', 'rationale':'test', 'modules':[
        {'name':'Top', 'purpose':'', 'ports':[], 'dependencies':[], 'implementation':'',
         'reference_ids':[], 'linked_reference_ids':['pipelined_divider']}]}
    with pytest.raises(ValueError, match='assigned'):
        SystemPlan.parse(obj, [])
    obj['modules'][0]['reference_ids'] = ['pipelined_divider']
    assert SystemPlan.parse(obj, []).modules[0].linked_reference_ids == ('pipelined_divider',)
    obj['language'] = 'verilog'
    with pytest.raises(ValueError, match='Chisel'):
        SystemPlan.parse(obj, [])


def test_revalidation_rejects_changed_linked_implementation(tmp_path):
    from copy import deepcopy
    from fast.fullstack.contracts import Module, SystemPlan
    library = Library(CATALOG, tmp_path)
    module = Module('Top', '', (), (), '', reference_ids=('pipelined_divider',),
                    linked_reference_ids=('pipelined_divider',))
    plan = SystemPlan('Top', (module,), '', 'chisel')
    manifest = json.loads((tmp_path/'library_manifest.json').read_text())
    library.check_linked_identity(plan, manifest)
    changed = deepcopy(manifest)
    changed['files']['template:pipelined_divider']['sha256'] = 'changed'
    with pytest.raises(ValueError, match='integrity'):
        library.check_linked_identity(plan, changed)

    # A valid but different original implementation must also be rejected.
    from fast.fullstack.library import digest
    other = tmp_path/'other.scala'; other.write_text('different implementation')
    changed['files']['template:pipelined_divider'].update(snapshot=str(other),sha256=digest(other))
    with pytest.raises(ValueError, match='identity differs'):
        library.check_linked_identity(plan, changed)


def test_native_reference_identity_survives_relocation_and_still_rejects_tampering(tmp_path):
    from fast.fullstack.contracts import Module, SystemPlan

    original = tmp_path / 'original'
    Library(CATALOG, original)
    manifest = json.loads((original / 'library_manifest.json').read_text())
    module = Module('Top', '', (), (), '', reference_ids=('pipelined_divider',),
                    linked_reference_ids=('pipelined_divider',))
    plan = SystemPlan('Top', (module,), '', 'chisel')
    relocated = tmp_path / 'relocated'
    original.rename(relocated)
    current = Library(CATALOG, tmp_path / 'current')
    current.check_linked_identity(plan, manifest, snapshot_root=relocated)
    snapshot = relocated / 'references' / Path(manifest['files']['template:pipelined_divider']['snapshot']).name
    snapshot.chmod(0o644)
    snapshot.write_text('tampered native IP')
    with pytest.raises(ValueError, match='integrity'):
        current.check_linked_identity(plan, manifest, snapshot_root=relocated)
