import json

from fast.agents.codesign import CoDesignSpace
from fast.agents.rediscovery import DynaXRediscovery
from fast.agents.plan_proposers import LLMPlanProposer
from fast.schemas.contract import parse_algorithm
from fast.schemas.models import ArchSpecs, KernelCandidate, KernelSearchSpace
from test_kernel_search import FakeAdapter, _spec
from test_work_conservation import _point, _kernel


def test_expanded_labels_preserve_all_algorithm_parameters():
    space = KernelSearchSpace(block_ms=(32, 64), xm_high=(16,), xm_low=(4,),
        threshold_pairs=((.75, .05), (1.5, .2)), max_sequence_length=512)
    assert len(space.labels()) == 4
    contracts = [parse_algorithm(label) for label in space.labels()]
    assert {c.block_m for c in contracts} == {32, 64}
    assert {(c.threshold_0, c.threshold_1) for c in contracts} == {(.75, .05), (1.5, .2)}
    assert all(c.sizing_kept == 16 for c in contracts)


def test_invalid_threshold_contract_does_not_silently_fall_back():
    for label in ['xm:16:4:32:nan:0.1', 'xm:4:16:32:1:0.1']:
        assert parse_algorithm(label).sizing_kept is None


def test_joint_search_reenters_kernel_with_real_hardware_feedback():
    class Kernel:
        name = 'scripted'
        seen_feedback = []
        def propose(self, spec, space, history, count):
            self.seen_feedback.append(json.loads(self.hardware_feedback))
            return (KernelCandidate(space.labels()[len(history)], self.name),)
    class Hardware:
        def propose(self, *args):
            return (_point(parallelism=8),)
    kernel = Kernel()
    result = DynaXRediscovery(FakeAdapter(), kernel, lambda index: Hardware()).run(
        _spec(budget=2), kernel_space=KernelSearchSpace(block_ms=(32, 64),
            xm_high=(16,), xm_low=(4,), threshold_pairs=((1.5, .2),), max_sequence_length=512),
        hardware_space=CoDesignSpace(), specs=ArchSpecs(target_mhz=50), head_dim=64,
        kernel_batch=1, hardware_budget=1, hardware_batch=1)
    assert result['kernel_budget_complete']
    assert len(result['designs']) == 2
    assert not kernel.seen_feedback[0]['previous_hardware_evaluations']
    assert kernel.seen_feedback[1]['previous_hardware_evaluations'][0]['hardware_evaluated'] == 1
    assert {d['hardware']['topk_m'] for d in result['designs']} == {32, 64}


def test_blind_hardware_prompt_contains_no_pre_ranked_calibration_answers():
    p = LLMPlanProposer(None, calibration_hints=False)
    prompt = p._prompt(_kernel(), ArchSpecs(), CoDesignSpace(), (), 4)
    assert 'No default design' in prompt
    assert 'depth  area um^2' not in prompt
    assert '3.05' not in prompt
    assert 'queue_depth' in prompt


def test_sram_domain_is_shared_by_random_and_llm_proposers():
    from dataclasses import replace
    from fast.agents.cooptimizer import RandomProposer
    space = replace(CoDesignSpace(), sram_bytes=(131072,))
    points = RandomProposer(3).propose(_kernel(), ArchSpecs(), space, (), 8)
    assert {p.sram_bytes for p in points} == {131072}
    llm = LLMPlanProposer(None, calibration_hints=False)
    prompt = llm._prompt(_kernel(), ArchSpecs(), space, (), 2)
    assert 'sram_bytes       [131072]' in prompt
