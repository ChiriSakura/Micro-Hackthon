import json
from pathlib import Path

import pytest

from fast.fullstack.behavior import explain_behavior
from fast.fullstack.contracts import Module, Port, Task
from fast.fullstack.library import Library

ROOT = Path(__file__).parents[1]


def test_upstream_files_are_byte_identical_and_not_falsely_native(tmp_path):
    import hashlib
    records = json.loads((ROOT / 'libraries/third_party/manifest.json').read_text())
    for record in records.values():
        for relative, data in record['files'].items():
            path = ROOT / record['local_directory'] / relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == data['sha256']
    library = Library(ROOT / 'libraries/rq1_extended_catalog.json', tmp_path)
    index = {x['id']: x for x in library.template_index()}
    assert index['spatten_official_topk']['language'] == 'spinalhdl'
    assert index['spatten_official_topk']['native_library_symbols'] == {}
    assert not index['spatten_official_topk']['native_linkable']
    assert index['pipelined_divider']['native_linkable']
    for name in ('spatten_official_topk', 'flexcim_nm_distribution', 'sanger_official_mask'):
        with pytest.raises(ValueError, match='reference-only'):
            library.linked_sources([name])
    assert library.test_references(['sanger_official_pack'])['sanger_official_pack']
    library.check()


def test_large_packed_arithmetic_is_visible_to_diagnosis():
    module = Module('Scores', '', (Port('x', 'input', 8), Port('scores', 'output', 144)), (), '',
                    behavior={'latency': 0, 'outputs': {'scores': 'pack(9,' + ','.join(['x'] * 16) + ')'},
                              'vectors': [{'x': 2}, {'x': 0}, {'x': 255}]})
    example = explain_behavior(module)[0]['outputs']['scores']
    value = sum(2 << (9*i) for i in range(16))
    assert example['port_bit_pattern'] == value
    assert example['hex'] == hex(value)
    assert example['unsigned_lanes_lsb_first'] == [2]*16


def test_minimum_rounds_rejects_early_stop_and_defaults_unchanged(tmp_path):
    from test_fullstack_generation import FakeTools, ScriptedLLM, task, CATALOG
    from fast.fullstack.flow import FullStackFlow
    from fast.agents.llm_backends import Reply
    class EarlyStop(ScriptedLLM):
        def prompt(self, prompt):
            reply = super().prompt(prompt)
            if self.roles[-1] == 'critic':
                data = json.loads(reply.result)
                # Propose stop first, then honor the mandatory-round feedback.
                if 'This experiment requires' not in prompt:
                    data['layer'] = 'stop'
                else:
                    data['layer'] = 'compiler'
                return Reply(json.dumps(data))
            return reply
    assert task().min_loops == 1
    with pytest.raises(ValueError, match='min_loops'):
        task(min_loops=3, max_loops=2)
    flow = FullStackFlow(task(min_loops=2, max_loops=2), CATALOG, tmp_path / 'run', EarlyStop(), FakeTools())
    result = flow.run()
    assert result['error'] is None
    assert len(result['rounds']) == 2
    assert result['agent_calls']['critic'] == 3
