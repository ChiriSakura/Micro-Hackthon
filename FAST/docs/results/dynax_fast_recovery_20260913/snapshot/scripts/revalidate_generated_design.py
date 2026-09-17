#!/usr/bin/env python3
"""Recheck one archived generated design without making any LLM calls."""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.contracts import SystemPlan, Task
from fast.fullstack.library import Library, digest, save
from fast.fullstack.tools import RtlTools, check_chisel_source, check_source


def revalidate(run: Path, number: int, catalog: Path, output: Path, tools, *, ppa_backend=None):
    run=run.resolve()
    task=Task.parse(json.loads((run/'task.json').read_text()))
    if ppa_backend is not None:
        task=Task.parse(asdict(replace(task, ppa_backend=ppa_backend)))
    record=json.loads((run/f'round_{number:02d}/result.json').read_text())
    contract=json.loads((run/'algorithm_contract.json').read_text())
    plan=SystemPlan.parse(record['system_plan'],contract['ports'])
    originals=json.loads((run/'library_manifest.json').read_text())
    # Verify all generated sources before invoking any compiler or trusted plugin.
    by_name={}
    for name,sha in record['sources'].items():
        path=(run/name).resolve(strict=True)
        if not path.is_relative_to(run) or digest(path)!=sha:
            raise ValueError(f'Generated source integrity failed: {name}')
        if path.stem in by_name:
            raise ValueError('Duplicate source module name')
        by_name[path.stem]=path
    if set(by_name)!={m.name for m in plan.modules}:
        raise ValueError('Source inventory does not match the system plan')
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    library=Library(catalog,output)
    algorithm_key=f'algorithm:{task.algorithm}'
    if library.files[algorithm_key]['sha256']!=originals['files'][algorithm_key]['sha256']:
        raise ValueError('Trusted algorithm differs from the original run; use the frozen catalog')
    algorithm=library.algorithm(task.algorithm)
    library.check_linked_identity(plan,originals)
    algorithm.validate_config(record['config'])
    sources=[]
    for module in plan.modules:
        code=by_name[module.name].read_text()
        library.check_generated(code,module,plan.language)
        suffix='scala' if plan.language=='chisel' else 'v'
        path=output/f'{module.name}.{suffix}'
        path.write_text(code);sources.append(path)
    gate=tools.module(plan.modules[-1],[*library.plan_sources(plan),*sources],output,language=plan.language)
    if not gate['passed']:
        result={'passed':False,'stage':'elaboration/lint','gate':gate}
    else:
        rtl=[Path(gate['elaborated_verilog'])] if plan.language=='chisel' else sources
        verification=tools.verify(plan,rtl,algorithm.verification(record['config'],task.seed,plan.top),output)
        result={'passed':False,'stage':'e2e','verification':verification}
        if verification['passed']:
            evaluation=tools.evaluate(plan,rtl,verification,algorithm.profile(record['config'],task.seed),task,output)
            result={'passed':evaluation['complete'],'stage':'evaluation','evaluation':evaluation}
    library.check()
    result.update(original_run=str(run),original_round=number,llm_calls=0,
                  task=asdict(task),purpose='artifact revalidation, not another autonomous optimization run')
    save(output/'revalidation.json',result)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--round',type=int,required=True)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tool-root',type=Path,required=True)
    parser.add_argument('--ppa-backend',choices=['yosys_opensta','hammer_openroad'])
    parser.add_argument('--timeout',type=int,default=300)
    args=parser.parse_args(argv)
    result=revalidate(args.run,args.round,args.catalog,args.output,RtlTools(args.tool_root,args.timeout),ppa_backend=args.ppa_backend)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
