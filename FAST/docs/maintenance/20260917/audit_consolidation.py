"""Read-only evidence checks; writes the current consolidation acceptance record."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tarfile
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from fast.fullstack.report_evidence import load_followups

OUT = ROOT / 'docs/results/rq1_completion_20260917'
MAINT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    checks = {}

    def check(name, passed):
        checks[name] = bool(passed)
        if not passed:
            raise AssertionError(name)

    data = read(OUT / 'RQ1_SUMMARY.json')
    rows, followups = data['rounds'], data['followups']
    with tarfile.open(ROOT / 'docs/history/rq1_consolidation_20260917/before_consolidation.tar.gz') as archive:
        original = json.load(archive.extractfile('previous_reports/RQ1_SUMMARY.json'))
    check('original_twenty_candidates_unchanged', len(rows) == 20 and rows == original['rounds'])
    check('assisted_followup_pinned_and_separate', len(followups) == 1 and followups == load_followups(OUT))
    check('original_qualified_algorithms_three', len({r['algorithm'] for r in rows if r['qualified']}) == 3)
    check('cumulative_qualified_algorithms_four', len({r['algorithm'] for r in rows + followups if r['qualified']}) == 4)
    for row in rows + followups:
        if row['qualified']:
            check(f"constraints_{row.get('evidence_id', row['algorithm'] + '_R' + str(row['round']))}",
                  row['complete'] and row['feasible'] and row['frequency_mhz'] > 250
                  and row['heldout_rmse'] <= .05 and row['area_um2'] <= 200000
                  and row['slack_ns'] >= 0 and row['hold_slack_ns'] >= 0
                  and row['route_drc_violations'] == 0)
    with (OUT / 'metrics.csv').open() as stream:
        exported = list(csv.DictReader(stream))
    check('csv_twenty_one_unique_evidence_ids', len(exported) == len({r['evidence_id'] for r in exported}) == 21)
    canonical = {(r['algorithm'], r['round'], 'original_trajectory'): r for r in rows}
    canonical.update({(r['algorithm'], r['round'], r['evidence_class']): r for r in followups})
    for row in exported:
        expected = canonical[(row['algorithm'], int(row['round']), row['evidence_class'])]
        check(f"csv_{row['evidence_id']}",
              (row['independently_qualified'] == 'True') == expected['qualified']
              and json.loads(row['config']) == expected['config']
              and all((not row[k] and expected.get(k) is None)
                      or (bool(row[k]) and expected.get(k) is not None and float(row[k]) == expected[k])
                      for k in ('heldout_rmse', 'area_um2', 'power_mw', 'latency_ns', 'energy_nj',
                                'frequency_mhz', 'slack_ns', 'hold_slack_ns', 'route_drc_violations')))
    designs = read(OUT / 'designs/index.json')
    check('four_readable_design_exports', len(designs) == 4)
    for design in designs:
        directory = OUT / 'designs' / design['name']
        manifest = read(directory / 'manifest.json')
        check(f"design_record_{design['name']}", sha(directory / 'accepted_record.json') == manifest['record_sha256'])
        check(f"design_sources_{design['name']}", all(
            sha(directory / entry['exported']) == sha(Path(entry['original'])) == entry['sha256']
            for entry in manifest['files']))
    trace = read(OUT / 'cross_layer_trace.json')
    for algorithm in trace['transitions']:
        for row in algorithm['rounds']:
            record = Path(row['source_record'])
            check(f"original_record_{algorithm['algorithm']}_R{row['round']}", sha(record) == row['record_sha256_at_audit'])
            check(f"original_sources_{algorithm['algorithm']}_R{row['round']}", all(
                sha(record.parent.parent / entry['path']) == entry['sha256'] for entry in row['sources']))
    workload = read(OUT / 'common_workload_audit.json')
    check('all_twenty_one_share_qkv_workload', len(workload['rounds']) == 20 and
          {r['workload_sha256'] for r in workload['rounds']} == {followups[0]['workload_sha256']})
    cleanup = read(MAINT / 'cleanup_manifest.json')
    for entry in cleanup['verified_archives']:
        check('archive_' + str(Path(entry['path']).relative_to(ROOT)),
              entry['passed'] and sha(Path(entry['path'])) == entry['archive_sha256'])
    code = read(MAINT / 'current_code_verification.json')
    check('current_code_archive', code['passed'] and sha(MAINT / 'current_code.tar.gz') == code['archive_sha256'])
    check('current_code_matches_snapshot', all(sha(ROOT / path) == entry['sha256']
          for path, entry in code['manifest']['files'].items()))
    suite = ET.parse(OUT / 'consolidated_report_tests.xml').getroot().find('testsuite')
    check('fourteen_reporting_tests_passed', suite.get('tests') == '14'
          and suite.get('failures') == suite.get('errors') == suite.get('skipped') == '0')
    filenames = ['RQ1_SUMMARY.md', 'RQ1_SUMMARY.json', 'RESULTS.md', 'DESIGNS.md',
                 'metrics.csv', 'metrics.json', 'followups.json', 'README.md', 'PROTOCOL.md',
                 'common_workload_audit.json', 'cross_layer_trace.json',
                 'latency_energy_efficiency.pdf', 'latency_energy_efficiency.svg',
                 'latency_energy_efficiency.png']
    result = {
        'utc': datetime.now(timezone.utc).isoformat(), 'passed': True, 'checks': checks,
        'original_candidates': 20, 'assisted_followups': 1,
        'qualified_algorithms_original': 3, 'qualified_algorithms_including_assisted': 4,
        'qualification_scope': 'Development continuation with a separately labeled externally diagnosed repair; not a four-of-four autonomous success rate.',
        'report_artifact_sha256': {name: sha(OUT / name) for name in filenames},
        'cleanup': {'files': sum(r['files'] for r in cleanup['removed']),
                    'bytes': sum(r['bytes'] for r in cleanup['removed'])},
        'code_snapshot_sha256': code['archive_sha256'],
    }
    (OUT / 'final_acceptance_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'checks': len(checks), 'cleanup': result['cleanup']}))


if __name__ == '__main__':
    main()
