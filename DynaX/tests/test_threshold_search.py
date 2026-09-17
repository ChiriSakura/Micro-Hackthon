"""Candidate thresholds must change the ORIGINAL DynaX mask, not just metadata."""
import pytest
import torch

from run_eval_matrix import method_config, config_digest
from models.utils.sparse_attention import gen_sparsity_mask_xm


def test_three_probability_mass_branches_are_candidate_controlled():
    scores = torch.zeros(1, 1, 64, 64)
    mask = torch.zeros_like(scores)
    counts, configs = [], []
    for label in ["xm:16:4:32:0.75:0.05", "xm:16:4:32:1.5:0.05", "xm:16:4:32:1.5:1.2"]:
        c = method_config(label, {})
        configs.append(c)
        sparse = gen_sparsity_mask_xm(scores, mask, c['threshold_0'], c['threshold_1'],
                                      n1=c['xm_n1'], n2=c['xm_n2'], m=c['xm_m'])
        counts.append(int((sparse[..., -1, :] == 0).sum()))
    assert counts == [32, 8, 0]
    assert len({config_digest(c) for c in configs}) == 3


def test_explicit_thresholds_override_global_defaults_and_remain_isolated():
    overrides = {"threshold_0": 99, "threshold_1": 9}
    a = method_config("xm:16:4:32:0.75:0.05", overrides)
    b = method_config("xm:16:4:64:1.5:0.2", overrides)
    assert (a['xm_m'], a['threshold_0'], a['threshold_1']) == (32, .75, .05)
    assert (b['xm_m'], b['threshold_0'], b['threshold_1']) == (64, 1.5, .2)
    assert overrides == {"threshold_0": 99, "threshold_1": 9}


@pytest.mark.parametrize('label', ['xm:4:16:32:1:0.1', 'xm:16:4:32:nan:0.1',
                                  'xm:16:4:32:1:2', 'xm:16:4:32:1'])
def test_invalid_explicit_parameters_fail_before_execution(label):
    with pytest.raises(ValueError):
        method_config(label, {})


def test_profile_uses_candidate_block_width_instead_of_legacy_64():
    from models.utils.sparsity_stats import SparsityRecorder
    kept = torch.zeros(1, 1, 64, 64, dtype=torch.bool)
    kept[..., :16] = True
    recorder = SparsityRecorder()
    mask = torch.zeros_like(kept, dtype=torch.float32)
    recorder.record('m32', kept, mask, causal_kept_ratio=.5, block_size=32)
    recorder.record('m64', kept, mask, causal_kept_ratio=.5, block_size=64)
    stats = recorder.summary()
    assert stats['m32']['mean_block_occupancy'] == .5
    assert stats['m64']['mean_block_occupancy'] == 1
    assert '16' in stats['m32']['mean_tile_load_imbalance']
