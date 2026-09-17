#!/usr/bin/env python3
"""Rebuild a generated design and check additional algorithm seeds without LLM calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fast.fullstack.revalidation import revalidate
from fast.fullstack.contracts import SystemPlan
from fast.fullstack.library import Library, digest, save
from fast.fullstack.tools import RtlTools


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--round',type=int,default=1)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tool-root',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[101,211,307,401,503])
    parser.add_argument('--ppa-backend',choices=['yosys_opensta','hammer_openroad'],
                        help='Optional fresh rebuild PPA backend; does not replace original run measurements')
    parser.add_argument('--timeout',type=int,default=600)
    args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    tools=RtlTools(args.tool_root,args.timeout)
    baseline=revalidate(args.run,args.round,args.catalog,out/'rebuild',tools,ppa_backend=args.ppa_backend)
    if not baseline['passed']:
        save(out/'summary.json',{'passed':False,'baseline':baseline,'llm_calls':0})
        return 1
    record=json.loads((args.run/f'round_{args.round:02d}/result.json').read_text())
    contract=json.loads((args.run/'algorithm_contract.json').read_text())
    plan=SystemPlan.parse(record['system_plan'],contract['ports'])
    references=Library(args.catalog,out/'holdout_reference')
    algorithm=references.algorithm(baseline['task']['algorithm'])
    rtl=out/'rebuild/whole_system.v';sha=digest(rtl)
    results=[]
    for seed in args.seeds:
        if seed==baseline['task']['seed']:
            raise ValueError('Holdout seed must differ from the original generation seed')
        work=out/f'seed_{seed}';work.mkdir()
        checked=tools.verify(plan,[rtl],algorithm.verification(record['config'],seed,plan.top),work)
        results.append({'seed':seed,**checked})
        save(work/'verification.json',results[-1])
    references.check()
    passed=all(r['passed'] for r in results) and digest(rtl)==sha
    save(out/'summary.json',{'passed':passed,'llm_calls':0,'baseline':baseline,'holdout':results,
        'rtl_sha256':sha,'holdout_case_executions':sum(r.get('cases',0) for r in results),
        'scope':'fresh elaboration/E2E/PPA revalidation plus extra reference seeds; boundary vectors may repeat across seeds'})
    print(json.dumps({'passed':passed,'seeds':args.seeds,'llm_calls':0}))
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
