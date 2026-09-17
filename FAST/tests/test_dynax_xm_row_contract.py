"""Bit-contract checks; actual upstream audit is a separate recorded experiment."""
from pathlib import Path
import importlib.util

spec=importlib.util.spec_from_file_location('dynax_row_contract',Path(__file__).resolve().parents[1]/'libraries/algorithms/dynax_xm_row.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_tie_refinement_and_signed_extremes():
    a=m.DynaxXMRow();c={'t0_quarters':5,'t1_quarters':1}
    zero,extreme,*_=a.cases(17,0)
    r=a.reference(c,zero)
    assert r['keep_mask']==0x11 and r['result']==-32
    r=a.reference(c,extreme)
    assert r['keep_mask']==3 and r['result']==-2048
    assert m.trunc(-17,3)==-5


def test_contract_checks_mask_and_numeric_output_and_lut_bounds():
    a=m.DynaxXMRow();c={'t0_quarters':6,'t1_quarters':2}
    for case in a.cases(101,1000):
        r=a.reference(c,case)
        assert -112<=min(r['scores'])<=max(r['scores'])<=128
        assert max(r['scores'])-min(r['scores'])<=240
        assert 1<=r['keep_mask'].bit_count()<=4
        assert -2048<=r['result']<=2032
    t=a.verification(c,17,'Complete')
    assert t['expected_cases']==100
    assert 'keep_mask !== mask' in t['testbench'] and 'result !== want' in t['testbench']
    assert len(m.EXP)==256 and m.EXP[0]==65535
