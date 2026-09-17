#!/usr/bin/env python3
"""Audit the declared fixed-point row against actual DynaX pruning + PyTorch AV.

Reports LUT error and tie-order differences explicitly; never patches upstream
code, changes golden output to fit hardware, or claims whole-model equivalence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dynax',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--captured-tile',type=Path)
    args=p.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'libraries/algorithms'))
    sys.path.insert(0,str(args.dynax.resolve()))
    from dynax_xm_row import DynaxXMRow
    from models.utils.sparse_attention import gen_sparsity_mask_xm
    import torch
    torch.set_num_threads(2)
    algo=DynaxXMRow();cases=algo.cases(913,256);real=[]
    provenance={}
    if args.captured_tile:
        data=json.loads(args.captured_tile.read_text())
        def q4(x):return max(-8,min(7,round(x/64)))
        def v8(x):return max(-128,min(127,round(x/16)))
        for q in data['q_ticks']:
            real.append(([q4(x) for x in q[:2]],[[q4(x) for x in k[:2]] for k in data['k_ticks'][:8]],
                         [v8(v[0]) for v in data['v_ticks'][:8]]))
        cases+=real
        provenance={'source':data['source'],'sha256':hashlib.sha256(args.captured_tile.read_bytes()).hexdigest(),
                    'projection':'first 8 keys, first 2 Q/K dimensions, first V dimension; requantized Q*.2/Q*.4, not original full attention head'}
    results=[]
    for t0 in (5,6):
        for t1 in (1,2):
            config={'t0_quarters':t0,'t1_quarters':t1};ties=0;tier_diffs=[];errors=[];exact_mask=0
            for idx,case in enumerate(cases):
                q,k,v=case;r=algo.reference(config,case)
                scores=(torch.tensor(q,dtype=torch.float64) @ torch.tensor(k,dtype=torch.float64).T)/16
                # Square attention shape follows the actual DynaX recording API.
                scores=scores.view(1,1,1,8).expand(1,1,8,8).clone()
                bias=torch.zeros((1,1,1,8),dtype=torch.float64)
                additive=gen_sparsity_mask_xm(scores,bias,t0/4,t1/4,n1=2,n2=1,m=4)
                mask=additive[0,0,0]==0
                actual=sum((1<<i) for i in range(8) if mask[i])
                if actual == r['keep_mask']:exact_mask+=1
                # Different equal-score members are legal TopK tie refinements.
                expected=tuple(tuple(sorted(r['scores'][i] for i in range(4*b,4*b+4) if r['keep_mask']>>i&1)) for b in range(2))
                observed=tuple(tuple(sorted(r['scores'][i] for i in range(4*b,4*b+4) if actual>>i&1)) for b in range(2))
                if expected!=observed:tier_diffs.append(idx)
                elif actual!=r['keep_mask']:ties+=1
                selected=torch.tensor([bool(r['keep_mask']>>i&1) for i in range(8)])
                float_scores=scores[0,0,0].clone();float_scores[~selected]=-float('inf')
                # Compare numerical LUT error under the same legal mask; also retain
                # original DynaX outputs so tie refinements cannot be hidden.
                out=float(torch.softmax(float_scores,dim=0) @ torch.tensor(v,dtype=torch.float64))*16
                original_out=float(torch.softmax((scores+additive)[0,0,0],dim=0) @ torch.tensor(v,dtype=torch.float64))*16
                errors.append({'case':idx,'hardware_contract':r['result'],'float_same_mask':out,
                               'original_dynax_float':original_out,'abs_error_ticks':abs(out-r['result'])})
            results.append({'config':config,'cases':len(cases),'exact_mask_matches':exact_mask,
                'legal_tie_differences':ties,'non_tie_selection_mismatches':tier_diffs,
                'max_lut_and_trunc_error_q8_ticks':max(x['abs_error_ticks'] for x in errors),
                'mean_lut_and_trunc_error_q8_ticks':sum(x['abs_error_ticks'] for x in errors)/len(errors),'outputs':errors})
    args.output.mkdir(parents=True,exist_ok=False)
    source=args.dynax/'models/utils/sparse_attention.py'
    report={'selection_semantics_passed':all(not r['non_tie_selection_mismatches'] for r in results),
            'numeric_within_2_q8_ticks':all(r['max_lut_and_trunc_error_q8_ticks']<=2 for r in results),
            'scope':'bounded is_quant=False X:M decode-row; LUT approximation and deterministic tie refinement; no model accuracy claim',
            'upstream_source':str(source),'upstream_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'real_capture_projection':provenance,'real_cases':real,'results':results}
    (args.output/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('results','real_cases')},indent=2))
    return 0 if report['selection_semantics_passed'] and report['numeric_within_2_q8_ticks'] else 1

if __name__=='__main__':raise SystemExit(main())
