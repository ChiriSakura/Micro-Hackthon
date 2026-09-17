"""Repair control-plane fault injection; fake measurements are not PPA evidence."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from fast.fullstack.flow import FullStackFlow
from fast.fullstack.library import digest
from test_fullstack_generation import CATALOG, FakeTools, ScriptedLLM, task


def repair_case(tmp_path, monkeypatch, tools):
    original = tmp_path / 'original'
    FullStackFlow(task(max_loops=1), CATALOG, original, ScriptedLLM(), FakeTools()).run()
    inventory = {str(p.relative_to(original)): digest(p) for p in original.rglob('*') if p.is_file()}
    script = Path(__file__).resolve().parents[1] / 'scripts/repair_generated_assembly.py'
    spec = importlib.util.spec_from_file_location('assisted_repair', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    llm = ScriptedLLM()
    monkeypatch.setattr(module, 'VertexDirect', lambda **kwargs: llm)
    monkeypatch.setattr(module, 'RtlTools', lambda *args: tools)
    diagnosis = tmp_path / 'diagnosis.txt'
    diagnosis.write_text('External diagnosis for the repair test')
    output = tmp_path / 'repair'
    monkeypatch.setattr(sys, 'argv', [str(script), '--run', str(original),
        '--build', 'round_01/build_01', '--previous-top', str(original/'round_01/build_01/Complete/Complete.v'),
        '--diagnosis', str(diagnosis), '--catalog', str(CATALOG), '--output', str(output),
        '--tool-root', str(tmp_path), '--project', 'test'])
    return module, output, original, inventory, llm


def test_repair_saves_accepted_design_before_interrupted_ppa(tmp_path, monkeypatch):
    class Interrupt(FakeTools):
        def evaluate(self, plan, sources, verification, profile, task, work):
            saved = json.loads((work.parent/'result.json').read_text())
            assert saved['status'] == 'ppa_pending'
            assert saved['verification']['passed'] and saved['sources'] and saved['rtl_sources']
            raise KeyboardInterrupt('scheduler interruption')

    module, output, original, before, _ = repair_case(tmp_path, monkeypatch, Interrupt())
    with pytest.raises(KeyboardInterrupt):
        module.main()
    assert json.loads((output/'summary.json').read_text())['rounds'][0]['status'] == 'ppa_pending'
    assert before == {str(p.relative_to(original)): digest(p) for p in original.rglob('*') if p.is_file()}


def test_repair_passes_fresh_measurements_and_source_to_critic(tmp_path, monkeypatch):
    module, output, _, _, llm = repair_case(tmp_path, monkeypatch, FakeTools())
    assert module.main() == 0
    summary = json.loads((output/'summary.json').read_text())
    assert summary['pareto_rounds'] == [1] and summary['critic_enabled']
    assert summary['rounds'][0]['critique_applied'] is False
    assert 'external-diagnosis-assisted' in summary['evidence_scope']
    context = next(ctx for role, ctx in llm.contexts if role == 'critic')
    assert context['current']['evaluation']['complete']
    assert context['accepted_sources']
    assert 'kernel' not in llm.roles and 'compiler' not in llm.roles
