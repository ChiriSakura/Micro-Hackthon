"""Independent numeric and workload checks for the frozen RQ1 experiment."""
import importlib.util
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('rq1', Path(__file__).parents[1] / 'libraries/algorithms/rq1_sparse_rows.py')
rq1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rq1)
CLASSES = [rq1.DynaxXM, rq1.BlockNM, rq1.GlobalTopK, rq1.SangerThreshold]
CONFIGS = [{'n1': 7, 'n2': 6, 't0_quarters': 4, 't1_quarters': 0}, {'n': 7}, {'k': 14}, {'threshold_256': 3}]


def test_identical_workloads_and_distinct_holdout():
    workloads = [cls().cases(rq1.CALIBRATION_SEED, 32) for cls in CLASSES]
    assert all(w == workloads[0] for w in workloads)
    holdout = rq1.DynaxXM().cases(rq1.HOLDOUT_SEED, 32)[4:]
    assert not set(map(repr, workloads[0][4:])) & set(map(repr, holdout))


def test_mechanisms_are_distinct():
    s = list(range(16)); e = [rq1.EXP[15-x] for x in s]
    nm = rq1.BlockNM().select({'n': 7}, s, e)
    top = rq1.GlobalTopK().select({'k': 14}, s, e)
    assert set(nm) == set(range(16)) - {0, 8}
    assert set(top) == set(range(2, 16))
    threshold = rq1.SangerThreshold()
    # Equality is dropped; this tests the strict probability threshold itself.
    assert threshold.select({'threshold_256': 8}, [0] * 16, [1] * 15 + [17]) == [15]


@pytest.mark.parametrize('cls,config', zip(CLASSES, CONFIGS))
def test_reference_dense_rmse_and_packing(cls, config):
    a = cls(); cases = a.cases(19, 17); err = norm = 0
    for case in cases:
        q, keys, v = case
        score = [(q[0]*k[0]+q[1]*k[1])/16 for k in keys]
        ex = [math.exp(s-max(score)) for s in score]
        dense = 16 * sum(w*x for w, x in zip(ex, v)) / sum(ex)
        r = a.reference(config, case)
        assert -2048 <= r['result'] <= 2032
        err += (r['result'] - dense)**2; norm += dense**2
    measured = a.measure(config, 19, 17)
    assert measured['quality_loss'] == pytest.approx(math.sqrt(err/norm))
    verification = a.verification(config, 17, 'TestTop')
    assert verification['expected_cases'] == 100
    assert 'input [127:0] ik' in verification['testbench']
    assert 'wire [15:0] keep_mask' in verification['testbench']
    for case, vector in zip(a.cases(17 ^ 0x5A17, 96), verification['vectors']):
        assert [(vector['k'] >> (4*i)) & 15 for i in range(32)] == [x & 15 for k in case[1] for x in k]


@pytest.mark.parametrize('cls,config', zip(CLASSES, CONFIGS))
def test_quality_calibration_is_frozen_and_non_dense(cls, config):
    a = cls(); first = a.profile(config, 17); second = a.profile(config, 29)
    assert first == second
    assert first['quality_loss'] <= .05
    assert first['sparsity'] > 0
    assert first['fully_dense_query_fraction'] < 1
    with pytest.raises(ValueError):
        a.validate_config({**config, 'not_a_parameter': 1})


def test_fixedpoint_negative_division_and_ties():
    assert rq1.trunc(-17, 3) == -5
    assert rq1.trunc(17, 0) == 0
    a = rq1.BlockNM()
    r = a.reference({'n': 7}, ([0,0], [[0,0]]*16, [-128]*16))
    assert r['result'] == -2048
    assert r['keep_mask'] == 0x7f7f
