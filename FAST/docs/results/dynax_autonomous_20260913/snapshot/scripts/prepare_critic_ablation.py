"""Prepare two independently rejected parents and frozen complete-task traces."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fast.adapters.dynax import _dataset_flag, _profile
from fast.agents.codesign import CoDesignPoint, estimate, violations
from fast.agents.templates import TemplateRegistry
from fast.experiments.critic_ablation import atomic_json, workload_key
from fast.schemas.conversions import kernel_result_from_measurement
from fast.schemas.models import ArchSpecs, KernelMeasurement, Status, digest_json, to_primitive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--dynax-python', required=True)
    parser.add_argument('--containers', required=True)
    parser.add_argument('--liberty', required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    final = json.loads((ROOT/'docs/results/final_experiment_20260911/final_design.json').read_text())
    quality_path = ROOT/'docs/results/final_experiment_20260911/confirmation_32.json'
    quality = json.loads(quality_path.read_text())
    row = next(r for r in quality['results'] if r['method'] == final['label'])
    stats = row['sparsity_stats']['xm']
    measurement = KernelMeasurement(label=final['label'], status=Status(row['status']),
        perplexity=row['perplexity'], quality_loss=row['relative_quality_loss'],
        actual_sparsity=stats['mean_sparsity'], index_entropy=stats['mean_index_entropy'],
        block_occupancy=stats['mean_block_occupancy'], row_kept_min=stats['row_kept_min'],
        row_kept_max=stats['row_kept_max'], wall_seconds=row['wall_seconds'], profile=_profile(stats),
        proposed_by='frozen 32-window confirmation')
    assert measurement.within and measurement.quality_loss <= final['task']['epsilon']
    config = json.loads((ROOT/'configs/experiments/dynax_rediscovery.json').read_text())
    config['task'] = final['task']
    specs = ArchSpecs(**config['constraints'])
    kernel = kernel_result_from_measurement(None, measurement)
    cache = args.out/'workloads'; cache.mkdir()
    index = {}
    audit = dict(quality_sha256=hashlib.sha256(quality_path.read_bytes()).hexdigest(), quality_loss=measurement.quality_loss,
                 commands=[], parents=[], state='running')
    atomic_json(args.out/'preparation.json', audit)
    for name, changes in [('main32', dict(tile_q=64, tile_k=64, parallelism=16, double_buffer=True,
            num_rows=32, reg_width=32, sram_bytes=262144, divider_stages=12, bank_count=32)), ('confirm16', {})]:
        point = CoDesignPoint(**dict(final['point'], **changes, queue_depth=4))
        metrics = estimate(point, kernel, 512, head_dim=64, block_m=32, kept_per_block=16)
        problems = violations(point, kernel, specs, TemplateRegistry(), head_dim=64, block_m=32, kept_per_block=16)
        assert not problems, problems
        design = dict(design_id=digest_json({'case': name, 'point': asdict(point), 'label': final['label']}),
            label=final['label'], algorithm=final['algorithm'], point=asdict(point), task=final['task'],
            quality_loss=measurement.quality_loss, metrics=metrics, analytical_violations=problems, feasible=True)
        case = args.out/name; directory = case/'candidates'/design['design_id']; directory.mkdir(parents=True)
        atomic_json(directory/'design.json', design)
        trace = cache/f'{name}.json'
        capture = [args.dynax_python, str(ROOT.parent/'DynaX/capture_row_workload.py'),
            '--model', final['task']['model'], '--dataset', _dataset_flag(final['task']['dataset']),
            '--layer', '10', '--head', '0', '--seq-len', '512', '--seed', str(final['task']['data_seed']),
            '--methods', final['label'], '--rows', str(point.num_rows), '--block', '32',
            '--device', 'cpu', '--max-tiles', str(512**2), '--out', str(trace)]
        validate = [sys.executable, str(ROOT/'scripts/validate_pareto_scheduler.py'), '--design', str(directory/'design.json'),
            '--workload', str(trace), '--tile-offset', '0', '--tile-count', '0', '--out', str(directory/'rtl'),
            '--frequency-mhz', '350', '--containers', args.containers, '--liberty', args.liberty]
        for stage, cmd in [('capture', capture), ('validate', validate)]:
            record = dict(case=name, stage=stage, command=cmd, state='running')
            audit['commands'].append(record); atomic_json(args.out/'preparation.json', audit)
            started = time.monotonic()
            with (directory/f'{stage}.log').open('w') as log:
                done = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
            record.update(exit_code=done.returncode, wall_seconds=time.monotonic()-started, state='finished')
            atomic_json(args.out/'preparation.json', audit)
            assert done.returncode in ([0] if stage == 'capture' else [0,1]), record
        validation = json.loads((directory/'rtl/validation.json').read_text())
        assert validation['sources_unchanged'] and validation['complete_captured_task']
        assert all(r['passed'] for r in validation['results']), 'parent functional/infrastructure failure'
        assert any(not r['frequency_feasible'] for r in validation['results']), 'parent unexpectedly satisfies timing'
        index[workload_key(design)] = dict(file=trace.name, sha256=hashlib.sha256(trace.read_bytes()).hexdigest())
        atomic_json(case/'search.json', dict(config=config, search_seed=0, frontier=[design], designs=[design],
            measurements=[to_primitive(measurement)], provenance='frozen parent freshly independently validated'))
        audit['parents'].append(dict(case=name, design_id=design['design_id'], validation=validation))
        atomic_json(args.out/'preparation.json', audit)
    atomic_json(cache/'index.json', index)
    tokens = {json.loads((cache/v['file']).read_text())['source']['token_sha256'] for v in index.values()}
    assert len(tokens) == 1, 'different captured token sequence'
    audit.update(state='finished', token_sha256=tokens.pop())
    atomic_json(args.out/'preparation.json', audit)

if __name__ == '__main__':
    main()
