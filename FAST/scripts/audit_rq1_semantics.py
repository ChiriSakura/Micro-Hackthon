#!/usr/bin/env python3
"""Audit four fixed-point contracts against unchanged DynaX software functions."""
import argparse
import ast
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dynax', type=Path, required=True)
    p.add_argument('--plugin', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    import torch
    import torch.nn.functional as F
    torch.set_num_threads(1)
    source = args.dynax / 'models/utils/sparse_attention.py'
    names = ['gen_sparsity_mask_' + n for n in ('xm', 'nm', 'topk', 'sanger')]
    syntax = ast.parse(source.read_text())
    nodes = [node for node in syntax.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == 4
    # Execute the actual function ASTs unchanged. Only the statistics callback is
    # a no-op: it does not participate in mask generation or numerical output.
    namespace = {'torch': torch, 'F': F, '_record': lambda *args, **kwargs: None}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    spec = importlib.util.spec_from_file_location('rq1_audit', args.plugin)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    cases = m.DynaxXM().cases(913, 256)
    rows = []
    for cls, function in zip((m.DynaxXM, m.BlockNM, m.GlobalTopK, m.SangerThreshold), names):
        a = cls()
        for values in itertools.product(*a.space.values()):
            c = dict(zip(a.space, values)); same = ties = 0; changed = []; max_error = 0
            for index, case in enumerate(cases):
                r = a.reference(c, case); scores = torch.tensor(r['scores'], dtype=torch.float64).reshape(1,1,1,16) / 16
                bias = torch.zeros_like(scores)
                kwargs = ({'threshold_0': c['t0_quarters']/4, 'threshold_1': c['t1_quarters']/4,
                           'n1': c['n1'], 'n2': c['n2'], 'm': 8} if cls is m.DynaxXM else
                          {'m': 8, 'n': c['n']} if cls is m.BlockNM else
                          {'topk': c['k']} if cls is m.GlobalTopK else {'threshold': c['threshold_256']/256})
                additive = namespace[function](scores, bias, **kwargs).reshape(16)
                actual = sum(1 << i for i in range(16) if additive[i].item() == 0)
                if actual == r['keep_mask']:
                    same += 1
                else:
                    blocks = [range(0,8), range(8,16)] if cls in (m.DynaxXM, m.BlockNM) else [range(16)]
                    signature = lambda mask: [sorted(r['scores'][i] for i in block if mask >> i & 1) for block in blocks]
                    if signature(actual) == signature(r['keep_mask']):
                        ties += 1
                    else:
                        changed.append({'case': index, 'float_mask': actual, 'fixed_mask': r['keep_mask']})
                selected = [i for i in range(16) if r['keep_mask'] >> i & 1]
                e = [math.exp((s-max(r['scores']))/16) for s in r['scores']]
                out = 16*sum(e[i]*case[2][i] for i in selected)/sum(e[i] for i in selected) if selected else 0
                max_error = max(max_error, abs(out-r['result']))
            rows.append({'algorithm': a.name, 'config': c, 'cases': len(cases), 'exact_masks': same,
                         'legal_tie_refinements': ties, 'non_tie_float_vs_fixed_differences': changed,
                         'max_same_mask_numeric_error_q8_ticks': max_error})
    report = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'plugin_sha256': hashlib.sha256(args.plugin.read_bytes()).hexdigest(),
              'scope': 'unchanged actual function ASTs; statistics callback disabled; float vs LUT selection differences retained',
              'configs': len(rows), 'results': rows}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'configs': len(rows), 'non_tie_differences': sum(len(r['non_tie_float_vs_fixed_differences']) for r in rows),
                      'max_numeric_error_ticks': max(r['max_same_mask_numeric_error_q8_ticks'] for r in rows)}))


if __name__ == '__main__':
    main()
