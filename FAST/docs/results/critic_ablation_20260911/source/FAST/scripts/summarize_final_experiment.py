"""Aggregate completed quality, scheduler and component-inventory evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.select_confirmed_candidate import split_quality, select
from fast.agents.codesign import CoDesignPoint, estimate
from fast.adapters.dynax import _profile
from fast.schemas.models import KernelResult, Status


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); base=args.root; out=args.out
    out.mkdir(parents=True,exist_ok=True)
    def unique(pattern):
        paths=list(base.glob(pattern))
        if len(paths)!=1: raise ValueError(f'expected one {pattern}: {paths}')
        return paths[0]
    def read(path): return json.loads(path.read_text())
    quality_path=unique('quality_*/results.json'); confirm_path=unique('confirm_*/results.json')
    aligned_path=unique('aligned_*/results.json')
    q,c,aligned=map(read,(quality_path,confirm_path,aligned_path))
    assert all(x['manifest']['complete'] for x in (q,c,aligned))
    rows=split_quality(c['results']); chosen=select(rows)
    design=read(base/'final_candidate.json')
    assert chosen and chosen['label']==design['label']
    inventories={name:read(unique(f'inventory_{name}_*/inventory.json')) for name in ('baseline','fast','random')}
    assert all(j['complete'] for j in inventories.values())
    replay_path=unique('final_replay_*/rtl/validation.json'); replay=read(replay_path)
    assert replay['sources_unchanged'] and replay['results'][0]['frequency_feasible']
    assert replay['complete_captured_task']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    final_net=unique('final_replay_*/rtl/build/*/synth/*.mapped.v')
    assert sha(final_net)==inventories['fast']['scheduler_netlist_sha256']
    assert design['point']==inventories['fast']['design']['point']
    for field in ('block_m','kept_high'):
        assert design['algorithm'][field]==inventories['fast']['design']['algorithm'][field]
    report={'final_design':design,'quality_confirmation':rows,'selected_quality':chosen,
        'quality_gate_passed':chosen['heldout']['relative_ppl_loss']<=.05,
        'quality_scope':'DynaX FP32 masks, 16 calibration + 16 selection-heldout windows; RTL Q8.8 quality not evaluated',
        'scheduler_netlist_reuse_verified':True,'scheduler':replay,
        'inventories':inventories,'full_system_feasible':None,
        'whole_attention_latency_s':None,'whole_attention_energy_j':None,
        'whole_accelerator_measured_power_w':None,
        'unverified':['dynamic threshold selector + gather + compute system integration',
                      'full-system numerical accuracy at Q8.8',
                      'predictor fanout/timing closure and memory interface timing',
                      'workload activity power including SRAM and routed interconnect'],
        'quality_controls':[{k:r.get(k) for k in ('method','perplexity','relative_quality_loss','windows')} for r in q['results']],
        'measurement_files':{str(p):sha(p) for p in (quality_path,confirm_path,aligned_path,replay_path)},
        'analytical_comparison':[]}
    dense=next(r for r in q['results'] if r['method']=='dense')
    aligned_dense=next(r for r in aligned['results'] if r['method']=='dense')
    assert dense['per_window_loss']==aligned_dense['per_window_loss']
    calibrated={r['method']:r for r in [*q['results'],*aligned['results']]}
    for name,d in [('fixed baseline',inventories['baseline']['design']),('initial FAST',inventories['fast']['design']),
                   ('random',inventories['random']['design']),('confirmed candidate',design)]:
        r=calibrated[d['label']]; s=r['sparsity_stats']['xm']
        k=KernelResult(status=Status.PASSED,baseline_metric=dense['perplexity'],candidate_metric=r['perplexity'],
            metric_name='perplexity',quality_loss=max(0,r['relative_quality_loss']),
            actual_sparsity=s['mean_sparsity'],index_entropy=s['mean_index_entropy'],
            block_occupancy=s['mean_block_occupancy'],trace_uri=str(aligned_path if name=='confirmed candidate' else quality_path),
            sparse_method=d['label'],profile=_profile(s))
        metrics=estimate(CoDesignPoint(**d['point']),k,512,head_dim=64,
            block_m=d['algorithm']['block_m'],kept_per_block=d['algorithm']['kept_high'])
        report['analytical_comparison'].append(dict(name=name,label=d['label'],metrics=metrics,
            quality_passed=k.quality_loss<=.05,evidence='original L1 partial model; not independent PPA; same 16 windows'))
    for name,j in inventories.items():
        directory=out/name; directory.mkdir(exist_ok=True)
        src=unique(f'inventory_{name}_*/inventory.json')
        shutil.copy2(src,directory/'inventory.json')
        for folder in ('sta','syn'):
            shutil.copytree(src.parent/folder,directory/folder,dirs_exist_ok=True)
        shutil.copy2(src.parent/'schedule.json',directory/'schedule.json')
    for name,path in [('quality_16.json',quality_path),('confirmation_32.json',confirm_path),
                      ('aligned_profile_16.json',aligned_path),('final_validation.json',replay_path),
                      ('final_design.json',base/'final_candidate.json'),('final_workload.json',unique('final_replay_*/workload.json')),
                      ('snapshot_manifest.json',base/'snapshot_manifest.json')]:
        shutil.copy2(path,out/name)
    report['final_scheduler_assumed_activity_energy_nj']={alpha:t['total_power_w']*replay['results'][0]['latency_s']*1e9
        for alpha,t in inventories['fast']['scheduler_power'].items()}
    (out/'summary.json').write_text(json.dumps(report,indent=2))
    # A figure of measured/estimated components, with all scopes in the labels.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    names=['baseline','fast','random']; labels=['Fixed baseline','FAST hardware','Random hardware']
    bottoms=[0.,0.,0.]
    components=[('RePE','InventoryRePE_'),('Predictor','InventoryPrePE_'),('TopK','InventoryTopK_'),('Divider','DivPipe'),('Feeder logic','InventoryFeeder_')]
    for label,prefix in components:
        vals=[sum(v['copies']*v['synthesis']['cell_area_um2'] for k,v in inventories[n]['blocks'].items() if k.startswith(prefix))/1e6 for n in names]
        axes[0].bar(labels,vals,bottom=bottoms,label=label);bottoms=[a+b for a,b in zip(bottoms,vals)]
    for label,vals in [('Scheduler',[inventories[n]['scheduler_validation']['results'][0]['metrics']['area_um2']/1e6 for n in names]),
                       ('SRAM model',[inventories[n]['memory']['area_um2']/1e6 for n in names])]:
        axes[0].bar(labels,vals,bottom=bottoms,label=label);bottoms=[a+b for a,b in zip(bottoms,vals)]
    axes[0].set_ylabel('Component area sum (mm²), pre-layout');axes[0].set_title('Separate components; not integrated die area')
    axes[0].legend(fontsize=7,ncol=2)
    quality=[r['relative_quality_loss']*100 for r in report['quality_controls'] if r['method']!='dense']+[chosen['calibration']['relative_ppl_loss']*100,chosen['heldout']['relative_ppl_loss']*100]
    axes[1].bar(['Fixed','Initial FAST','Random','Confirmed\ncalibration','Confirmed\nheldout'],quality,color=['#999999','#999999','#999999','#177c66','#326bba'])
    axes[1].axhline(5,color='red',linestyle='--',label='5% quality limit')
    axes[1].set_ylabel('Perplexity increase vs dense (%)');axes[1].set_title('DynaX FP32, 16 windows per bar');axes[1].legend(fontsize=8)
    for i,v in enumerate(quality):axes[1].text(i,v+.25,f'{v:.2f}%',ha='center',fontsize=8)
    fig.savefig(out/'results.png',dpi=180);fig.savefig(out/'results.pdf')
    print(json.dumps({'selected':chosen,'area_um2':inventories['fast']['component_area_sum_um2'],
                      'power_sensitivity_mw':inventories['fast']['power_sensitivity_mw']},indent=2))


if __name__=='__main__':main()
