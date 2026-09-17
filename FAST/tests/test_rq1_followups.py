"""Reporting provenance tests; values are artificial and not hardware evidence."""
import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest

from fast.fullstack.report_evidence import load_followups


def fixture(root):
    evaluation = {'complete': True, 'feasible': True, 'energy_nj': 2., 'latency_ns': 70.,
                  'energy_efficiency_queries_per_joule': 5e8, 'design_sha256': 'design'}
    record = {'round': 1, 'status': 'evaluated', 'config': {'n': 7}, 'evaluation': evaluation,
              'system_plan': {'top': 'Top', 'language': 'chisel', 'modules': []}}
    post = {'algorithm': 'rq1_block_nm', 'rounds': [dict(record, independently_qualified=True,
            heldout={'quality_loss': .03, 'sparsity': .125})]}
    entry = {'id': 'nm_assisted', 'label': 'A1', 'algorithm': 'rq1_block_nm',
             'evidence_class': 'assisted_repair', 'report': 'repair.md', 'sha256': {}}
    for key, value in [('record', record), ('post', post), ('verification', {'passed': True})]:
        p = root / (key + '.json'); p.write_text(json.dumps(value))
        entry[key] = p.name; entry['sha256'][key] = hashlib.sha256(p.read_bytes()).hexdigest()
    (root/'followups.json').write_text(json.dumps([entry]))
    return entry, record, post


def test_assisted_qualification_does_not_replace_original_failed_round(tmp_path, monkeypatch):
    _, record, _ = fixture(tmp_path)
    run = tmp_path/'run'; run.mkdir()
    record['evaluation']['feasible'] = False
    (run/'summary.json').write_text(json.dumps({'status': 'budget_exhausted', 'rounds': [record]}))
    (tmp_path/'jobs.json').write_text(json.dumps([{'algorithm': 'rq1_block_nm', 'run': str(run),
        'output': str(tmp_path/'absent'), 'job_id': '1'}]))
    monkeypatch.setattr('subprocess.run', lambda *a, **kw: SimpleNamespace(returncode=0, stdout=''))
    ns = runpy.run_path(str(Path(__file__).parents[1]/'scripts/report_rq1_completion.py'))
    data = ns['build_report'](tmp_path)
    assert len(data['rounds']) == 1 and not data['rounds'][0]['qualified']
    assert len(data['followups']) == 1 and data['followups'][0]['qualified']
    assert data['followups'][0]['display_label'] == 'A1'
    assert '0/4' in (tmp_path/'RQ1_SUMMARY.md').read_text()
    assert '1/4' in (tmp_path/'RQ1_SUMMARY.md').read_text()


def test_followup_rejects_mutated_evidence(tmp_path):
    fixture(tmp_path)
    (tmp_path/'record.json').write_text('{}')
    with pytest.raises(ValueError, match='hash differs'):
        load_followups(tmp_path)


def test_followup_rejects_validation_for_a_different_design(tmp_path):
    entry, _, post = fixture(tmp_path)
    post['rounds'][0]['evaluation']['design_sha256'] = 'different'
    path = tmp_path/'post.json'; path.write_text(json.dumps(post))
    entry['sha256']['post'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path/'followups.json').write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match='validated design'):
        load_followups(tmp_path)


def test_failed_archive_cannot_qualify_followup(tmp_path):
    entry, _, _ = fixture(tmp_path)
    path = tmp_path/'verification.json'; path.write_text(json.dumps({'passed': False}))
    entry['sha256']['verification'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path/'followups.json').write_text(json.dumps([entry]))
    assert load_followups(tmp_path)[0]['qualified'] is False
