"""Executable contract arithmetic/protocol tests, separate from trusted E2E oracle."""
from dataclasses import asdict
import pytest
import json

from fast.fullstack.behavior import evaluate, compile_tests
from fast.fullstack.contracts import Module, Port, SystemPlan
from fast.fullstack.tools import module_testbench


def test_packed_dot_product_and_sparse_reduction_regressions():
    env={'q':0x51,'k':0x85}
    assert evaluate('lane(q,0,4)*lane(k,0,4)+lane(q,1,4)*lane(k,1,4)',env)==45
    packed=evaluate('pack(9,60,70,80,90)',{})
    assert [evaluate(f'lane(s,{i},9)',{'s':packed}) for i in range(4)]==[60,70,80,90]
    weights=[v if v>=64 else 0 for v in (60,398,415,57)]
    assert sum(weights)==813
    assert evaluate('0 if d == 0 else n // d',{'n':15,'d':0})==0
    assert evaluate('d == 0 or n // d < 16',{'n':15,'d':0})==1
    assert evaluate('n < 0 and n // d > 0',{'n':15,'d':0})==0


@pytest.mark.parametrize('expr',["__import__('os')",'a.__class__','[x for x in a]','2**100','1 << 100000000','open(1)','(lambda:1)()'])
def test_expression_language_rejects_host_execution_and_unbounded_work(expr):
    with pytest.raises(ValueError): evaluate(expr,{'a':1})


def pipeline():
    ports=(Port('clock','input',1),Port('reset','input',1),Port('iv','input',1),
           Port('a','input',4),Port('ov','output',1),Port('b','output',5))
    behavior={'latency':3,'reset':'reset','valid_input':'iv','valid_output':'ov',
              'outputs':{'b':'a+1'},'vectors':[{'a':0},{'a':15},{'a':7}]}
    return ports,behavior


def test_pipeline_valid_delay_bubbles_and_reset_are_computed():
    ports,behavior=pipeline()
    tests=compile_tests(ports,behavior)
    first=tests[0]['steps']
    assert [step['expected']['ov'] for step in first]==[0,0,0,1,0,0]
    assert first[3]['expected']['b']==1
    assert all(step['cycles']==1 for case in tests for step in case['steps'])
    # Independently model a 3-register pipeline for the generated continuous stream.
    queue=[None,None,None]
    for step in tests[-1]['steps']:
        values=step['inputs'];expected=step['expected']
        if values['reset']:
            queue=[None,None,None]
            assert expected=={'ov':0,'b':0}
        else:
            queue=[values['a']+1 if values['iv'] else None,*queue[:2]]
            assert expected['ov']==(queue[2] is not None)
            if queue[2] is not None:assert expected['b']==queue[2]
    assert tests==compile_tests(ports,behavior)


def test_generated_tests_cannot_be_overridden_and_round_trip():
    ports,behavior=pipeline()
    leaf={'name':'Pipe','purpose':'increment','ports':[asdict(p) for p in ports],
          'dependencies':[],'implementation':'three registers','design_prompt':'implement','behavior':behavior}
    top={'name':'Top','purpose':'top','ports':[],'dependencies':['Pipe'],'implementation':'connect','design_prompt':'assemble'}
    obj={'top':'Top','rationale':'test','modules':[leaf,top]}
    plan=SystemPlan.parse(obj,[],require_jobs=True)
    assert SystemPlan.parse(json.loads(json.dumps(asdict(plan))),[],require_jobs=True)==plan
    leaf['tests']=[{'name':'forged','steps':[]}]
    with pytest.raises(ValueError,match='cannot override'):SystemPlan.parse(obj,[])


def test_combinational_vectors_use_bounded_pack_and_computed_outputs():
    ports=(Port('q','input',8),Port('k','input',8),Port('s','output',9))
    model={'latency':0,'outputs':{'s':'lane(q,0,4)*lane(k,0,4)+lane(q,1,4)*lane(k,1,4)'},
           'vectors':[{'q':0,'k':0},{'q':255,'k':255},{'q':'pack(4,1,5)','k':'pack(4,5,8)'}]}
    tests=compile_tests(ports,model)
    assert tests[0]['steps'][2]['expected']=={'s':45}
    assert len(tests[0]['steps'])==15
    module=Module('Score','',ports,(),'',tests=tuple(tests),behavior=model)
    tb=module_testbench(module)
    assert "9'd45" in tb['testbench']


def test_signed_reference_helpers_encode_without_truncating_invalid_lanes():
    assert evaluate('spack(4,-8,7)',{}) == 0x78
    assert evaluate('signed(lane(spack(8,-100,127),0,8),8)',{}) == -100
    assert evaluate('abs(signed(0x80,8))',{}) == 128
    with pytest.raises(ValueError,match='Signed packed lane'):
        evaluate('spack(4,-9,0)',{})
    with pytest.raises(ValueError,match='Packed lane'):
        evaluate('pack(4,-1,0)',{})


@pytest.mark.parametrize('n,d,expected', [(-1000,10,-100),(-7,3,-2),(7,-3,-2),(-7,-3,2),(99,0,0)])
def test_signed_division_truncates_toward_zero(n,d,expected):
    assert evaluate('trunc_div(n,d)', {'n':n,'d':d}) == expected


def test_simulator_counterexample_decodes_wide_packed_lanes():
    from fast.fullstack.behavior import explain_module_failure
    inputs = {'scores':evaluate('spack(9,195,85,201,-32,107,-78,-32,114)',{})}
    expected = evaluate('pack(16,45042,47,65535,0,184,0,0,285)',{})
    actual = expected | (15566 << 80)
    behavior = {'outputs':{'weights':'pack(16,45042,47,65535,0,184,0,0,285)'},
                'let':{'s':'signed(lane(scores,5,9),9)'}}
    tests = ({'name':'regression','steps':[{'inputs':inputs,'expected':{'weights':expected}}]},)
    m=Module('Weights','',(Port('scores','input',72),Port('weights','output',128)),(),'',
             behavior=behavior,tests=tests)
    gate={'functional':{'simulation':{'diagnostics':f'module case=0 step=0 output=weights expected={expected} actual={actual}'}}}
    result=explain_module_failure(m,gate)
    assert result['inputs']['scores']['signed_lanes'][5] == -78
    assert result['expected']['low_to_high_lanes'][5] == 0
    assert result['actual']['low_to_high_lanes'][5] == 15566
    assert result['frozen_expected_matches_log']
    assert m.tests == tests  # diagnosis never edits the test contract


def test_versioned_lane_corners_catch_signed_dot_product_overflow_without_changing_archives():
    ports=(Port('q','input',8),Port('k','input',8),Port('s','output',9))
    expr='signed(lane(q,0,4),4)*signed(lane(k,0,4),4)+signed(lane(q,1,4),4)*signed(lane(k,1,4),4)'
    old={'latency':0,'outputs':{'s':expr},'vectors':[{'q':0,'k':0},{'q':1,'k':1},{'q':255,'k':255}]}
    assert len(compile_tests(ports,old)[0]['steps'])==15
    new={**old,'test_generation_version':2}
    steps=compile_tests(ports,new)[0]['steps']
    corner=next(s for s in steps if s['inputs']=={'q':0x88,'k':0x88})
    assert corner['expected']['s']==128
    assert steps[:15]==compile_tests(ports,old)[0]['steps']
    bounded={**new,'input_bounds':{'q':[0,127]},'vectors':[{'q':0,'k':0},{'q':1,'k':1},{'q':127,'k':255}]}
    assert all(s['inputs']['q']<=127 for s in compile_tests(ports,bounded)[0]['steps'])


def test_failure_timing_distinguishes_step_index_from_capture_latency():
    from fast.fullstack.behavior import explain_module_failure
    ports = tuple(Port(n,d,w) for n,d,w in [('clock','input',1),('reset','input',1),
        ('valid_in','input',1),('a','input',8),('valid_out','output',1),('b','output',8)])
    behavior = {'latency':12, 'reset':'reset', 'valid_input':'valid_in', 'valid_output':'valid_out',
                'outputs':{'b':'a'}, 'vectors':[{'a':0},{'a':7},{'a':255}]}
    tests = compile_tests(ports, behavior)
    m = Module('Delay','',ports,(),'',behavior=behavior,tests=tuple(tests))
    def failure(step, expected, actual):
        return explain_module_failure(m, {'functional':{'simulation':{'diagnostics':
            f'module case=1 step={step} output=valid_out expected={expected} actual={actual}'}}})
    early = failure(11,0,1)['timing']
    assert early['sample_edge_in_scenario'] == 12
    assert early['contract_latency_including_capture'] == 12
    capture = early['most_recent_captures'][0]
    assert capture['capture_edge'] == 2
    assert capture['edges_including_capture_to_sample'] == 11  # not 10
    assert capture['expected_output_edge'] == 13
    assert capture['inputs']['a']['hex'] == '0x7'  # not zero-valued idle input
    assert early['captures_due_now'] == []
    due = failure(12,1,0)['timing']['captures_due_now']
    assert len(due) == 1 and due[0]['capture_edge'] == 2
    assert due[0]['computed_math']['outputs']['b']['hex'] == '0x7'
    assert due[0]['computed_math']['matches_frozen_expected']
    assert tests == list(m.tests)


def test_failure_timing_tracks_every_capture_when_valid_spans_multiple_edges():
    from fast.fullstack.behavior import explain_module_failure
    ports = tuple(Port(n,d,w) for n,d,w in [('clock','input',1),('reset','input',1),
        ('valid_in','input',1),('a','input',8),('valid_out','output',1),('b','output',8)])
    behavior = {'latency':3,'reset':'reset','valid_input':'valid_in','valid_output':'valid_out'}
    tests = ({'name':'held_valid','steps':[
        {'inputs':{'reset':1,'valid_in':0,'a':0},'cycles':2,'expected':{'valid_out':0}},
        {'inputs':{'reset':0,'valid_in':1,'a':7},'cycles':2,'expected':{'valid_out':0}},
        {'inputs':{'valid_in':0},'cycles':1,'expected':{'valid_out':1,'b':7}}]},)
    module = Module('Delay','',ports,(),'',behavior=behavior,tests=tests)
    result = explain_module_failure(module,{'functional':{'simulation':{'diagnostics':
        'module case=0 step=2 output=b expected=7 actual=0'}}})
    timing = result['timing']
    assert timing['sample_edge_in_scenario'] == 5
    assert [c['capture_edge'] for c in timing['most_recent_captures']] == [3,4]
    assert [c['capture_edge'] for c in timing['captures_due_now']] == [3]
