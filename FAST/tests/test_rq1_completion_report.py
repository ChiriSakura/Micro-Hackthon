"""Report provenance checks; all measurements here are explicit test doubles."""
import json
import csv
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('same_design', [False, True])
@pytest.mark.parametrize('new_validation_failed', [False, True])
@pytest.mark.parametrize('awaiting_resume', [False, True])
def test_baseline_qualification_requires_matching_design_and_physical_artifacts(tmp_path, monkeypatch, same_design, new_validation_failed, awaiting_resume):
    run = tmp_path/'run'; run.mkdir()
    output = tmp_path/'post'
    if new_validation_failed:
        output.mkdir()
        (output/'results.json').write_text(json.dumps({'rounds': [{'round': 1, 'independently_qualified': False}]}))
    evaluation = {'complete': True, 'feasible': True, 'energy_nj': 2, 'latency_ns': 70,
        'energy_efficiency_queries_per_joule': 5e8, 'design_sha256': 'current',
        'artifacts': {'hammer/par-rundir/routed.v': 'current_netlist'}}
    record = {'round': 1, 'config': {'n': 7}, 'status': 'evaluated', 'evaluation': evaluation,
              'system_plan': {'top': 'Top', 'language': 'chisel', 'modules': []}}
    (run/'summary.json').write_text(json.dumps({'status': 'running', 'rounds': [record]}))
    (tmp_path/'jobs.json').write_text(json.dumps([{'algorithm': 'rq1_dynax_xm', 'run': str(tmp_path/'queued' if awaiting_resume else run), 'previous_run': str(run),
        'output': str(output), 'job_id': '44'}]))
    baseline = tmp_path/'dynax_baseline'; baseline.mkdir()
    old = dict(evaluation)
    if not same_design:
        old['artifacts'] = {'hammer/par-rundir/routed.v': 'different_netlist'}
    (baseline/'results.json').write_text(json.dumps({'rounds': [{'round': 1, 'config': {'n': 7},
        'evaluation': old, 'independently_qualified': True,
        'heldout': {'quality_loss': .02, 'sparsity': .1}}]}))
    monkeypatch.setattr('subprocess.run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='44|PENDING|00:00:00\n' if awaiting_resume else '44|TIMEOUT|06:00:00\n'))
    ns = runpy.run_path(str(Path(__file__).parents[1]/'scripts/report_rq1_completion.py'))
    result = ns['build_report'](tmp_path)
    assert result['rounds'][0]['qualified'] is (same_design and not new_validation_failed)
    assert result['rounds'][0]['qualification_status'] == ('failed' if new_validation_failed else 'passed' if same_design else 'pending')
    assert result['runs'][0]['status'] == ('resume_not_started' if awaiting_resume else 'interrupted_with_checkpoint')
    assert result['runs'][0]['evidence_run'] == str(run)
    assert result['runs'][0]['persisted_status'] == 'running'
    # CSV and the main report must preserve/reject the same historical evidence.
    script = Path(__file__).parents[1]/'scripts/report_rq1.py'
    monkeypatch.setattr(sys, 'argv', [str(script), '--experiment', str(tmp_path)])
    runpy.run_path(str(script), run_name='__main__')
    csv_row = next(csv.DictReader((tmp_path/'metrics.csv').open()))
    assert (csv_row['independently_qualified'] == 'True') is (same_design and not new_validation_failed)
