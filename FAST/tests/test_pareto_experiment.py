from dataclasses import replace
from types import SimpleNamespace

import pytest

from fast.agents.cooptimizer import CoOptimizer, GuidedProposer, RandomProposer
from fast.agents.codesign import CoDesignSpace
from fast.agents.plan_proposers import LLMPlanProposer
from fast.agents.rtl_gate import LocalRtlGate, MODULES
from fast.schemas.models import ArchSpecs
from test_work_conservation import _kernel, _point


def test_overproducing_proposer_cannot_exceed_measurement_budget():
    class TooMany:
        def propose(self, kernel, specs, space, history, count):
            return tuple(replace(_point(), tile_q=i*32) for i in range(1, 20))
    result = CoOptimizer(allow_unverified=True).run(
        _kernel(), sequence_length=512, head_dim=64, budget=3, batch=3,
        proposer=TooMany(), patience=None)
    assert result.evaluated == 3
    assert len(result.history) == 3


def test_duplicate_proposals_do_not_count_as_new_evaluations():
    class Repeats:
        def propose(self, *args):
            return (_point(),) * 8
    result = CoOptimizer(allow_unverified=True).run(
        _kernel(), sequence_length=512, head_dim=64, budget=8, batch=4,
        proposer=Repeats(), patience=None)
    assert result.evaluated == 1
    assert "repeated" in result.stopped_because


def test_no_feedback_prompt_withholds_metrics_but_remembers_designs():
    from fast.agents.cooptimizer import CoDesignResult
    history = (CoDesignResult(_point(), None, None, {}, False),)
    proposer = LLMPlanProposer(None)
    prompt = proposer._prompt(_kernel(), ArchSpecs(), CoDesignSpace(), history, 4)
    assert "feedback withheld" in prompt


def test_failed_elaboration_cannot_reuse_an_old_verilog(tmp_path):
    target = "BlockSched_S4"
    gate = LocalRtlGate(repo=tmp_path, work_root=tmp_path, containers=tmp_path, python="python")
    work = tmp_path/"work"
    old = work/"rtl"/target/"BlockScheduler.v"
    old.parent.mkdir(parents=True)
    old.write_text("module BlockScheduler; endmodule")
    gate._run = lambda *a, **k: "[tool-error] exit=1\ncompile failed"
    assert not gate._elaborate(MODULES[target], work).passed


def test_nonzero_exit_with_a_pass_banner_is_not_a_pass(tmp_path):
    target = "BlockSched_S4"
    workload = tmp_path/"workload.json"
    workload.write_text("{}")
    gate = LocalRtlGate(repo=tmp_path, work_root=tmp_path, containers=tmp_path,
                        python="python", workload=workload)
    (tmp_path/"stimulus.txt").write_text("32 4 1\n")
    binary = tmp_path/"obj_dir"/f"tb_{target}"
    binary.parent.mkdir()
    binary.write_text("old binary")
    outputs = iter(["ok", "ok", "ok", "[tool-error] exit=1\nPASSED"])
    gate._run = lambda *a, **k: next(outputs)
    assert not gate._simulate(MODULES[target], tmp_path).passed
