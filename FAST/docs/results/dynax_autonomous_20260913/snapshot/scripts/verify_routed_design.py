#!/usr/bin/env python3
"""Independent algorithm E2E on the routed gate netlist, with Liberty cell models.

This is zero-delay functional gate simulation, not SDF timing simulation. STA
and extracted parasitics provide the separate timing evidence.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fast.fullstack.contracts import SystemPlan
from fast.fullstack.library import Library,digest,save
from fast.fullstack.tools import RtlTools


def main():
    p=argparse.ArgumentParser(description=__doc__)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--physical',type=Path,help='Standalone revalidation.json')
    source.add_argument('--run',type=Path,help='Autonomous run with inline Hammer evaluation')
    p.add_argument('--round',type=int,default=1)
    p.add_argument('--catalog',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--tool-root',type=Path,required=True)
    args=p.parse_args()
    if args.run:
        run=args.run.resolve()
        record=json.loads((run/f'round_{args.round:02d}/result.json').read_text())
        e=record['evaluation']
        if e.get('ppa_backend')!='hammer_openroad':raise ValueError('Run must contain Hammer evaluation')
        # Locate the measured build by its committed physical result, not the newest directory.
        matches=[]
        for result_path in (run/f'round_{args.round:02d}').glob('*/hammer/result.json'):
            if json.loads(result_path.read_text())==e:matches.append(result_path)
        if len(matches)!=1:raise ValueError('Cannot uniquely identify the recorded physical build')
        physical_record=matches[0]
        physical_root=physical_record.parent.parent
        measured={'original_run':str(run),'original_round':args.round,
                  'task':json.loads((run/'task.json').read_text()),'evaluation':e}
    else:
        physical_record=args.physical.resolve();physical_root=physical_record.parent
        measured=json.loads(physical_record.read_text());e=measured['evaluation']
    if not e.get('complete'):raise ValueError('Requires completed physical measurement')
    work=args.output.resolve();work.mkdir(parents=True,exist_ok=False)
    run=Path(measured['original_run']);record=json.loads((run/f'round_{measured["original_round"]:02d}/result.json').read_text())
    inventory=json.loads((run/'library_manifest.json').read_text())
    library=Library(args.catalog,work);key='algorithm:'+measured['task']['algorithm']
    if library.files[key]['sha256']!=inventory['files'][key]['sha256']:raise ValueError('Algorithm identity differs')
    algorithm=library.algorithm(measured['task']['algorithm']);plan=SystemPlan.parse(record['system_plan'],algorithm.describe()['ports'])
    relative='hammer/par-rundir/routed.v';routed=physical_root/relative
    if digest(routed)!=e['artifacts'][relative]:raise ValueError('Routed netlist integrity failed')
    liberty=args.tool_root/'pdk/hammer45/lib/NangateOpenCellLibrary_typical.lib'
    models=work/'liberty_cells.v';script=work/'cell_models.ys'
    script.write_text(f'read_liberty -ignore_miss_func {liberty}\nwrite_verilog -noattr {models}\n')
    tools=RtlTools(args.tool_root,600)
    built=tools.command(['apptainer','exec',str(args.tool_root/'containers/yosys.sif'),'yosys','-s',str(script)],work,work/'cell_models.log')
    if not built['passed']:raise ValueError('Failed to compile trusted Liberty functions')
    verified=tools.verify(plan,[routed,models],algorithm.verification(record['config'],measured['task']['seed'],plan.top),work)
    library.check()
    result={'passed':verified['passed'],'verification':verified,'physical_measurement':str(physical_record),
            'routed_sha256':digest(routed),'liberty_sha256':digest(liberty),'llm_calls':0,
            'scope':'zero-delay functional gate-level E2E on routed netlist; not SDF timing simulation'}
    save(work/'summary.json',result);print(json.dumps({'passed':result['passed'],'cases':verified.get('cases')}))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
