import json
import sys

import pytest

from scripts.refine_rediscovery import FeedbackLLM, main
from fast.schemas.models import to_primitive
from test_kernel_search import _measurement


def test_actual_timing_failure_reaches_the_proposer_with_its_design_identity():
    class Recorder:
        def prompt(self, prompt):
            self.prompt_text = prompt
            return 'reply'
    backend = Recorder()
    measured = [{'design_id': 'failed-32x8', 'metrics': {'critical_path_ns': 3.051},
                 'frequency_feasible': False}]
    assert FeedbackLLM(backend, measured).prompt('legal domains') == 'reply'
    assert backend.prompt_text.startswith('legal domains')
    assert json.dumps(measured) in backend.prompt_text


def test_hardware_refinement_cannot_reuse_a_quality_failing_algorithm(tmp_path, monkeypatch):
    source = tmp_path/'source'
    evidence = source/'candidates'/'bad'/'rtl'
    evidence.mkdir(parents=True)
    label = 'xm:16:8:32:1.5:0.05'
    (source/'search.json').write_text(json.dumps({
        'frontier': [{'design_id': 'bad', 'label': label}],
        'measurements': [to_primitive(_measurement(label, .2, .9))],
        'config': {'task': {'epsilon': .05}},
    }))
    (evidence/'validation.json').write_text(json.dumps({
        'design_id': 'bad', 'scope': 'scheduler',
        'results': [{'passed': True, 'frequency_feasible': False,
                     'metrics': {'critical_path_ns': 3.051}}],
    }))
    monkeypatch.setattr(sys, 'argv', ['refine', '--source', str(source),
        '--out', str(tmp_path/'out'), '--dynax-python', 'python', '--method', 'random',
        '--containers', str(tmp_path), '--liberty', str(tmp_path/'test.lib')])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert not (tmp_path/'out'/'refinement.json').exists()
