"""Archive portable evidence; compiled intermediates stay in the original study."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--study',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    summary=json.loads((args.out/'summary.json').read_text())
    assert summary['all_complete'] and not summary['audit_errors']
    raw=args.out/'raw';raw.mkdir(exist_ok=False)
    excluded={'scala-build','.scala-build','obj_dir','__pycache__','.bsp','analysis'}
    for directory,dirs,names in os.walk(args.study):
        dirs[:]=[d for d in dirs if d not in excluded]
        for name in names:
            source=Path(directory)/name
            if source.suffix in {'.json','.log','.tcl','.txt','.slurm','.out','.err','.md'}:
                target=raw/source.relative_to(args.study)
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    manifest=json.loads((args.study/'source_manifest.json').read_text())
    snapshot=Path(manifest['snapshot'])
    source_dir=args.out/'source';source_dir.mkdir(exist_ok=False)
    for name,expected in manifest['files'].items():
        source=snapshot/name
        assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
        target=source_dir/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    analysis_source=args.out/'analysis_source';analysis_source.mkdir()
    for name in ('analyze_critic_ablation.py','report_critic_ablation.py','archive_critic_ablation.py'):
        shutil.copyfile(Path(__file__).parent/name,analysis_source/name)
    runtime=snapshot/'FAST/hardware/tool_commands.log'
    shutil.copyfile(runtime,raw/'hardware_tool_commands.log')
    # Include generated RTL and mapped netlists without enormous compiler objects.
    with tarfile.open(args.out/'rtl_netlists.tar.gz','w:gz') as tar:
        for directory,dirs,names in os.walk(args.study):
            dirs[:]=[d for d in dirs if d not in excluded]
            for name in names:
                if name.endswith(('.v','.fir')):
                    source=Path(directory)/name;tar.add(source,arcname=str(source.relative_to(args.study)))
    info=dict(original_study=str(args.study),source_snapshot=str(snapshot),
        retained='All JSON, logs, Tcl, stimulus text, job scripts, source snapshot; generated RTL/netlists in rtl_netlists.tar.gz.',
        omitted_from_portable_copy='Compiled objects, Scala classes/cache and simulation executables; originals remain in original_study.',
        artifacts={str(f.relative_to(args.out)):hashlib.sha256(f.read_bytes()).hexdigest()
                   for f in sorted(args.out.rglob('*')) if f.is_file() and f.name!='artifact_manifest.json'})
    (args.out/'artifact_manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print('Archived',len(info['artifacts']),'files')

if __name__=='__main__':main()
