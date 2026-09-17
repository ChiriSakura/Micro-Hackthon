"""One-time cleanup, only after independently checksummed evidence archives exist."""
from pathlib import Path
import json,os,shutil,sys
sys.path.insert(0,'/home/gz2522/Micro-Hackthon/FAST')
from fast.fullstack.artifacts import sha256_file
w=Path('/home/gz2522/Micro-Hackthon/FAST');b=Path('/scratch/gz2522/gz2522/tmp/micro-hackthon');ledger=[]
def remove(path,reason,archive):
 if not path.exists() and not path.is_symlink():return
 count=size=0
 if path.is_dir() and not path.is_symlink():
  for root,ds,fs in os.walk(path):
   for f in fs:
    p=Path(root)/f
    if not p.is_symlink():count+=1;size+=p.stat().st_size
  shutil.rmtree(path)
 else:
  if not path.is_symlink():count=1;size=path.stat().st_size
  path.unlink()
 ledger.append({'path':str(path),'reason':reason,'regular_files':count,'logical_bytes':size,'archive':str(archive)})
for name in ['dynax_autonomous_20260913','dynax_fast_recovery_20260913']:
 d=w/'docs/results'/name;record=json.loads((d/'archive_verification.json').read_text());archive=d/'artifacts.tar.gz'
 assert sha256_file(archive)==record['archive_sha256']
 inputs=record['manifest']['inputs']
 for excluded in record['manifest']['excluded']:
  labels=[k for k in inputs if excluded['path']==k or excluded['path'].startswith(k+'/')];label=max(labels,key=len)
  root=Path(inputs[label]);relative=Path(excluded['path']).relative_to(label);path=root/relative
  assert root.is_relative_to(b) and path.is_relative_to(root)
  remove(path,excluded['reason'],archive)
archive=w/'docs/history/dynax_development_20260913.tar.gz';record=json.loads((w/'docs/history/dynax_development_20260913.verify.json').read_text());assert sha256_file(archive)==record['archive_sha256']
# Preserve runtime/tool infrastructure and successful snapshots. Only these archived development roots retire.
for label,source in record['manifest']['inputs'].items():
 if label.startswith(('v4/','v5/','v6/','v7/','v8_invalid/')):
  path=Path(source);assert path.is_relative_to(b)
  remove(path,'retired development version; all non-cache evidence archived',archive)
archive=w/'docs/history/obsolete_results_20260913.tar.gz';record=json.loads((w/'docs/history/obsolete_results_20260913.verify.json').read_text());assert sha256_file(archive)==record['archive_sha256']
for source in record['manifest']['inputs'].values():remove(Path(source),'obsolete metrics/derived plot; preserved with invalidation context',archive)
for root in [w/'fast',w/'scripts',w/'tests']:
 for p in list(root.rglob('__pycache__')):
  remove(p,'rebuildable Python cache',None)
output=b/'archives/maintenance_20260913/cleanup_manifest.json'
output.write_text(json.dumps({'entries':ledger,'removed_files':sum(x['regular_files'] for x in ledger),'logical_bytes_removed':sum(x['logical_bytes'] for x in ledger)},indent=2)+'\n')
print(output);print('files',sum(x['regular_files'] for x in ledger),'bytes',sum(x['logical_bytes'] for x in ledger))
