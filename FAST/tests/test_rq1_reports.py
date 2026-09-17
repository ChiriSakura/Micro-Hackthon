import json
from pathlib import Path
import runpy


def test_report_excludes_timing_failures_from_improvement(tmp_path, monkeypatch):
    run = tmp_path / 'run'; run.mkdir()
    out = tmp_path / 'post'; out.mkdir()
    records = []
    for index, (latency, efficiency, feasible) in enumerate([(100, 1e9, True), (90, 1.5e9, True), (10, 10e9, False)], 1):
        records.append({'round': index, 'status': 'evaluated', 'config': {'n1': 7, 'n2': 7, 't1_quarters': 0},
                        'evaluation': {'latency_ns': latency, 'energy_efficiency_queries_per_joule': efficiency, 'feasible': feasible}})
    (run / 'summary.json').write_text(json.dumps({'status': 'budget_exhausted', 'rounds': records, 'pareto_rounds': [2]}))
    (run / 'events.json').write_text(json.dumps([
        {'stage': 'compiler_library_read', 'references': [{'id': 'example_reference'}]}]))
    build = run / 'round_01/build_01'; build.mkdir(parents=True)
    (build / 'system_plan.json').write_text(json.dumps({'modules': [
        {'reference_ids': ['example_reference'], 'linked_reference_ids': []}]}))
    (tmp_path / 'jobs.json').write_text(json.dumps([{'algorithm': 'rq1_dynax_xm', 'job_id': 'test', 'run': str(run), 'output': str(out)}]))
    script = Path(__file__).parents[1] / 'scripts/report_rq1.py'
    monkeypatch.setattr('sys.argv', [str(script), '--experiment', str(tmp_path)])
    runpy.run_path(str(script), run_name='__main__')
    report = (tmp_path / 'RESULTS.md').read_text()
    assert '最高能效 R2' in report and '最低延迟 R2' in report
    assert '1.500×' in report
    data = json.loads((tmp_path / 'metrics.json').read_text())
    assert len(data['rounds']) == 3  # failed measurements are retained
    assert data['rounds'][0]['area_um2'] is None
    assert data['rounds'][0]['xm_collapses_to_fixed_nm'] is True
    assert data['runs'][0]['references_read'] == ['example_reference']
    assert data['runs'][0]['references_assigned'] == ['example_reference']
    assert data['runs'][0]['references_link_requested'] == []
    assert '1 个算法运行' in report
    assert '退化为固定 N:M' in (tmp_path / 'DESIGNS.md').read_text()


def test_empty_report_has_no_invented_measurements(tmp_path, monkeypatch):
    (tmp_path / 'jobs.json').write_text('[]')
    script = Path(__file__).parents[1] / 'scripts/report_rq1.py'
    monkeypatch.setattr('sys.argv', [str(script), '--experiment', str(tmp_path)])
    runpy.run_path(str(script), run_name='__main__')
    assert json.loads((tmp_path / 'metrics.json').read_text())['rounds'] == []
    assert not (tmp_path / 'metrics.csv').exists()
