"""Select among previously LLM-proposed algorithms without tuning on holdout.

Calibration = windows 0..15. Holdout = windows 16..31. Selection prefers the
smallest high branch budget, then calibration loss. A heldout failure is kept
as failure; it never causes selection of another candidate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path


def split_quality(records, boundary=16):
    dense = next(r for r in records if r['method'] == 'dense')
    losses = dense['per_window_loss']
    if dense['status'] != 'passed' or len(losses) != 2 * boundary:
        raise ValueError('need exactly two complete, equal calibration/holdout partitions')
    result = []
    for r in records:
        if r['method'] == 'dense': continue
        if r['status'] != 'passed' or len(r['per_window_loss']) != len(losses):
            raise ValueError('candidate evaluation is incomplete')
        entry = {'label':r['method']}
        for key, lo, hi in [('calibration',0,boundary),('heldout',boundary,2*boundary)]:
            b = math.exp(sum(losses[lo:hi]) / boundary)
            c = math.exp(sum(r['per_window_loss'][lo:hi]) / boundary)
            entry[key] = {'windows':[lo,hi], 'dense_ppl':b, 'candidate_ppl':c,
                          'relative_ppl_loss':c/b-1}
        result.append(entry)
    return result


def select(rows, epsilon=.05):
    eligible = [r for r in rows if r['calibration']['relative_ppl_loss'] <= epsilon]
    if not eligible: return None
    return min(eligible, key=lambda r:(int(r['label'].split(':')[1]),
                                       r['calibration']['relative_ppl_loss'],r['label']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--quality',type=Path,required=True)
    p.add_argument('--hardware',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    q=json.loads(args.quality.read_text()); rows=split_quality(q['results']); selected=select(rows)
    report={'selection_rule':'minimum N1, then calibration loss among calibration-passing original LLM proposals',
            'epsilon':.05,'candidates':rows,'selected':selected,
            'quality_sha256':hashlib.sha256(args.quality.read_bytes()).hexdigest(),
            'heldout_used_for_selection':False,
            'quality_passed':selected is not None and selected['heldout']['relative_ppl_loss']<=.05,
            'attribution':'post-search automated confirmation and hardware reuse; not a new autonomous LLM proposal'}
    (args.out/'selection.json').write_text(json.dumps(report,indent=2))
    if selected is None: return 1
    design=json.loads(args.hardware.read_text())
    design.pop('provenance',None)
    label=selected['label']; _,n1,n2,m,t0,t1=label.split(':')
    design['label']=label
    design['algorithm']=dict(label=label,family='xm',block_m=int(m),kept_high=int(n1),kept_low=int(n2),threshold_0=float(t0),threshold_1=float(t1))
    design['parent_hardware_design_id']=design.pop('design_id')
    design['design_id']=hashlib.sha256(json.dumps({'algorithm':design['algorithm'],'point':design['point']},sort_keys=True).encode()).hexdigest()
    design['quality_confirmation']=report
    design['task']['max_samples']=32
    design['evidence']='FP32 quality confirmation plus reused scheduler-verified hardware; full integration unverified'
    (args.out/'design.json').write_text(json.dumps(design,indent=2))
    print(json.dumps(report,indent=2))
    return 0 if report['quality_passed'] else 1


if __name__=='__main__': raise SystemExit(main())
