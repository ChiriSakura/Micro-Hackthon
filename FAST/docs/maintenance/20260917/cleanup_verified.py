"""Clean only this completed RQ1 batch after verifying its published archives."""
from pathlib import Path
import datetime
import json
import os
import shutil
import sys

w = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(w))
from fast.fullstack.artifacts import verify_archive, sha256_file

o = w/'docs/results/rq1_completion_20260917'
r = w/'docs/results/block_nm_timing_repair_20260917'
b = Path('/scratch/gz2522/gz2522/tmp/micro-hackthon')
maintenance = Path(__file__).parent
archives = []
for path in [*sorted(o.glob('*/artifacts.tar.gz')), r/'validation/artifacts.tar.gz']:
    old = json.loads((path.parent/'archive_verification.json').read_text())
    checked = verify_archive(path)
    assert checked['passed'] and checked['archive_sha256'] == old['archive_sha256']
    archives.append({'path': str(path), **{k: checked[k] for k in ('passed','archive_sha256','file_count')}})
    print('Verified', path.parent.name, flush=True)
history = w/'docs/history/rq1_consolidation_20260917'
old = json.loads((history/'archive_verification.json').read_text())
checked = verify_archive(history/'before_consolidation.tar.gz')
assert checked['passed'] and checked['archive_sha256'] == old['archive_sha256']

jobs = json.loads((o/'jobs.json').read_text())
roots = [Path(j[k]) for j in jobs for k in ('run','output')]
paths = json.loads((r/'paths.json').read_text())
roots += [Path(paths['run']), Path(paths['output']), o, r]
cache_names = {'obj_dir','.scala-build','.bsp','__pycache__','.pytest_cache'}
ledger = []

def remove(path, reason):
    count = size = 0
    assert not path.is_symlink()
    for base, dirs, files in os.walk(path):
        for name in files:
            p = Path(base)/name
            if not p.is_symlink():
                count += 1; size += p.stat().st_size
    shutil.rmtree(path)
    ledger.append({'path':str(path), 'reason':reason, 'files':count, 'bytes':size})

for root in dict.fromkeys(roots):
    assert root.is_relative_to(b/'runs') or root.is_relative_to(w/'docs/results')
    # Only terminal run directories / post-processed outputs listed in this batch.
    if (root/'summary.json').exists():
        assert json.loads((root/'summary.json').read_text())['status'] != 'running'
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            path = Path(base)/name
            if name in cache_names and not path.is_symlink():
                remove(path, 'Rebuildable cache in explicitly listed completed RQ1 run/output')
                dirs.remove(name)

# Historical generators are redundant active copies, but their exact bytes are archived.
for path in sorted(o.glob('report_tools*')):
    if not path.is_dir():
        continue
    prefix = 'previous_generators/'+path.name+'/'
    expected = {k[len(prefix):]:v for k,v in checked['manifest']['files'].items() if k.startswith(prefix)}
    assert expected
    actual = {str(p.relative_to(path)):sha256_file(p) for p in path.rglob('*') if p.is_file()}
    assert actual == {k:v['sha256'] for k,v in expected.items()}
    remove(path, 'Superseded reporting generator; exact files preserved in before_consolidation.tar.gz')

result = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope':'Completed RQ1 and Block N:M repair only; no library, generated design, raw log or unrelated project deletion.',
    'verified_archives':archives, 'historical_generators_archive':str(history/'before_consolidation.tar.gz'),
    'removed':ledger, 'files_removed':sum(x['files'] for x in ledger),
    'bytes_removed':sum(x['bytes'] for x in ledger)}
(maintenance/'cleanup_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'files_removed':result['files_removed'],'bytes_removed':result['bytes_removed']}),flush=True)
