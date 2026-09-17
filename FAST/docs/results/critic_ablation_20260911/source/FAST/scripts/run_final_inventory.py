"""Reproduce a frozen candidate's scheduler gate and component PPA inventory.

Component sums are NOT an integrated accelerator. Power is an explicitly
assumed global-activity sensitivity study, never workload or silicon power.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.adapters.synthesis import YosysSynthesisAdapter
from fast.adapters.timing import OpenStaTimingAdapter
from fast.agents.codesign import CoDesignPoint, to_schedule
from fast.agents.templates import _SRAM_MACROS


def banked_memory(point):
    """Keep logical depth explicit: unused macro width is not usable capacity."""
    banks, width = point['bank_count'], point['data_width']
    if point['sram_bytes'] * 8 % (banks * width):
        raise ValueError('memory must have an integral per-bank logical depth')
    depth = point['sram_bytes'] * 8 // (banks * width)
    options = []
    for (md, mw), (area, access, leak, read) in _SRAM_MACROS.items():
        across, deep = math.ceil(width / mw), math.ceil(depth / md)
        count = banks * across * deep
        options.append(dict(macro_depth=md, macro_width=mw, macros=count,
            across_per_bank=across, deep_per_bank=deep, banks=banks,
            logical_depth_per_bank=depth, logical_width=width,
            logical_bytes=point['sram_bytes'], physical_bits=count*md*mw,
            area_um2=count*area, leakage_mw=count*leak*1e-6,
            one_bank_read_energy_pj=across*read*1e-3, macro_access_ns=access))
    best = min(options, key=lambda x: x['area_um2'])
    best['evidence'] = 'analytical fakeram45 macro table; no macro mapping or physical layout'
    best['excluded'] = 'depth decoder/multiplexer overhead, writes, interconnect; no measured activity'
    return best


def inventory(point, algorithm, head_dim):
    r, p, w = point['num_rows'], point['pe_per_row'], point['reg_width']
    m, n = algorithm['block_m'], algorithm['kept_high']
    depth = point['sram_bytes'] * 8 // (point['bank_count'] * point['data_width'])
    if point['data_width'] != 16:
        raise ValueError('inventory targets currently implement Q8.8 only')
    return [
        (f'InventoryRePE_R{r}P{p}W{w}', 'RePEArray', 1, False),
        (f'InventoryPrePE_R{r}D{head_dim}', 'PrePEArray_1_2', 1, False),
        (f'InventoryTopK_M{m}N{n}', 'TopK', r, False),
        (f'DivPipe{point["divider_stages"]}', 'FixedPointDivPipelined', r, False),
        (f'InventoryFeeder_W{w}B{point["bank_count"]}D{depth}', 'KeyFeeder', 1, True),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--design', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--dynax-python', required=True)
    ap.add_argument('--frequency-mhz', type=float, default=350)
    args = ap.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[2]
    design = json.loads(args.design.read_text()); p = design['point']; a = design['algorithm']
    task = design['task']; period = 1000 / args.frequency_mhz
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    sources = [*sorted((repo/'FAST/hardware/chisel').rglob('*.scala')),
               repo/'FAST/hardware/tb/tb_block_scheduler.cpp', Path(__file__)]
    result = dict(design=design, commands=[], stage='pre-layout',
                  source_hashes={str(x.relative_to(repo)):digest(x) for x in sources},
                  liberty_sha256=digest(args.root/'pdk/nangate45/NangateOpenCellLibrary_typical.lib'),
                  frequency_mhz=args.frequency_mhz, blocks={}, complete=False,
                  integrated_attention_verified=False,
                  power_scope='uniform global activity assumed; duty 0.5; no per-net activity annotation; ideal clock tree',
                  exclusions=['dynamic X:M threshold selector integration', 'global FSM/DMA',
                              'full attention Q/K/V datapath verification at chosen fixed point',
                              'memory macro mapping and read/write activity', 'clock tree and physical routing'])
    schedule = asdict(to_schedule(CoDesignPoint(**p), (), 0.0,
                                  block_m=a['block_m'], kept_per_block=a['kept_high']))
    schedule['predicted_utilization'] = None  # not measured by this experiment
    (out/'schedule.json').write_text(json.dumps(schedule, indent=2))
    (out/'design.json').write_text(json.dumps(design, indent=2))
    def save(): (out/'inventory.json').write_text(json.dumps(result, indent=2))
    def run(argv, name, cwd=repo/'FAST'):
        print(name, flush=True)
        with (out/f'{name}.log').open('w') as log:
            done = subprocess.run([str(x) for x in argv], cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
        result['commands'].append(dict(argv=[str(x) for x in argv], cwd=str(cwd), exit_code=done.returncode, log=name+'.log'))
        save()
        return done.returncode
    run([args.dynax_python, repo/'DynaX/capture_row_workload.py', '--model', task['model'],
         '--dataset', 'wiki', '--layer', str(task['capture_layer']), '--head', str(task['capture_head']),
         '--seq-len', str(task['sequence_length']), '--seed', str(task['data_seed']),
         '--methods', design['label'], '--rows', str(p['num_rows']), '--block', str(a['block_m']),
         '--device', 'cpu', '--max-tiles', '262144', '--out', out/'workload.json'], 'capture')
    if not (out/'workload.json').is_file(): return 1
    run([sys.executable, repo/'FAST/scripts/validate_pareto_scheduler.py', '--design', out/'design.json',
         '--workload', out/'workload.json', '--tile-offset', '0', '--tile-count', '0',
         '--out', out/'scheduler', '--frequency-mhz', str(args.frequency_mhz),
         '--containers', args.root/'containers', '--liberty', args.root/'pdk/nangate45/NangateOpenCellLibrary_typical.lib'], 'scheduler')
    if not (out/'scheduler/validation.json').is_file(): return 1
    validation = json.loads((out/'scheduler/validation.json').read_text())
    result['scheduler_validation'] = validation
    entries = inventory(p, a, task['head_dim'])
    rc = run(['scala-cli', 'run', 'chisel', '--server=false', '--workspace', out/'scala-build',
              '--main-class', 'Elaborate', '--', 'LIST:'+','.join(x[0] for x in entries), out/'rtl'],
             'elaborate', repo/'FAST/hardware')
    if rc: return 1
    syn = YosysSynthesisAdapter(container=args.root/'containers/yosys.sif',
        liberty=args.root/'pdk/nangate45/NangateOpenCellLibrary_typical.lib', work_root=out/'syn')
    sta = OpenStaTimingAdapter(container=args.root/'containers/opensta.sif', liberty=syn.liberty, work_root=out/'sta')
    def power(netlist, top, target):
        values = {}
        for alpha in (.05, .1, .2):
            t = sta.analyse(netlist, top, period_ns=period, activity=alpha, label=f'{target}_{alpha}')
            values[str(alpha)] = {**asdict(t), 'setup_feasible': t.success and t.timing_credible
                                and t.slack_ns is not None and t.slack_ns >= 0}
        return values
    for target, top, copies, memory in entries:
        print('synth '+target, flush=True)
        rtl = out/'rtl'/target/(top+'.v'); net = out/(target+'.mapped.v')
        s = syn.synthesize(rtl, top, net, has_memory=memory)
        entry = dict(copies=copies, synthesis=asdict(s), rtl_sha256=digest(rtl),
                     memory_blackboxed=memory, power=None)
        if s.success:
            entry['netlist_sha256'] = digest(net)
            if not memory: entry['power'] = power(net, top, target)
        result['blocks'][target] = entry; save()
    scheduler_nets = list((out/'scheduler/build').rglob('*.mapped.v'))
    if len(scheduler_nets) == 1:
        result['scheduler_power'] = power(scheduler_nets[0], 'BlockScheduler', 'scheduler')
        result['scheduler_netlist_sha256'] = digest(scheduler_nets[0])
    memory = banked_memory(p); result['memory'] = memory
    sr = validation['results'][0]
    missing = [k for k,v in result['blocks'].items() if not v['synthesis']['success']]
    subtotal = sum(v['copies'] * (v['synthesis']['cell_area_um2'] or 0) for v in result['blocks'].values())
    sched_area = sr['metrics'].get('area_um2')
    result['component_area_sum_um2'] = subtotal + memory['area_um2'] + (sched_area or 0) if not missing and sched_area else None
    result['power_sensitivity_mw'] = {}
    for alpha in ('0.05', '0.1', '0.2'):
        timed = [v['copies'] * v['power'][alpha]['total_power_w'] * 1000
                 for v in result['blocks'].values() if v['power'] and v['power'][alpha]['total_power_w'] is not None]
        sp = result.get('scheduler_power', {}).get(alpha, {}).get('total_power_w')
        result['power_sensitivity_mw'][alpha] = dict(
            nonmemory_logic_plus_sram_leakage=sum(timed)+(sp or 0)*1000+memory['leakage_mw'],
            missing=['KeyFeeder logic power', 'SRAM read/write dynamic', 'integration and physical overhead'],
            complete=False)
    result['sources_unchanged'] = all(digest(x) == result['source_hashes'][str(x.relative_to(repo))] for x in sources)
    result['complete'] = not missing and result['sources_unchanged'] and sr['passed'] and bool(result.get('scheduler_power'))
    save()
    print(json.dumps({k:result[k] for k in ('complete','component_area_sum_um2','power_sensitivity_mw')}, indent=2), flush=True)
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
