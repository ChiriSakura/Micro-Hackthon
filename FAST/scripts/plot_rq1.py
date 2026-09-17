#!/usr/bin/env python3
"""Standalone latency-energy-efficiency figure from measured RQ1 records."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((args.experiment / 'metrics.json').read_text())
    canonical = args.experiment / 'RQ1_SUMMARY.json'
    qualifications = {(r['algorithm'], r['round']): r['qualified']
        for r in json.loads(canonical.read_text())['rounds']} if canonical.exists() else {}
    rows = [r for r in data['rounds'] + data.get('followups', []) if r['latency_ns'] is not None
            and r['energy_efficiency_queries_per_joule'] is not None]
    if not rows:
        print('No measured PPA points; no figure generated.')
        return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    columns = min(2, len(data['runs']))
    panels = (len(data['runs']) + columns - 1) // columns
    fig, axes = plt.subplots(panels, columns, figsize=(4 * columns, 3 * panels), squeeze=False,
                             sharex=True, sharey=True, constrained_layout=True)
    colors = ['#0072B2', '#009E73', '#D55E00', '#CC79A7']
    for index, (ax, run) in enumerate(zip(axes.flat, data['runs'])):
        color = colors[index % len(colors)]
        group = [r for r in rows if r['algorithm'] == run['algorithm']]
        for r in group:
            x, y = r['latency_ns'], r['energy_efficiency_queries_per_joule'] / 1e9
            good = r['search_feasible']
            assisted = r.get('evidence_class') == 'assisted_repair'
            qualified = (r.get('independently_qualified', False) if assisted else
                qualifications.get((r['algorithm'], r['round']), r.get('independently_qualified', False)))
            ax.scatter(x, y, color=color if good else '#888888',
                       marker='D' if assisted and qualified else '*' if qualified else 'o' if good else 'x',
                       s=65 if assisted else 110 if qualified else 45,
                       zorder=4 if qualified else 3 if good else 2)
            offsets = ((5, 12), (5, -16), (5, 28), (5, -22), (-5, 12))
            offset = (-38, -16) if assisted else offsets[(r['round'] - 1) % len(offsets)]
            ax.annotate(r.get('display_label', 'R' + str(r['round'])), (x, y), xytext=offset,
                        ha='right' if offset[0] < 0 else 'left', textcoords='offset points', fontsize=8,
                        arrowprops={'arrowstyle': '-', 'color': '#aaaaaa', 'linewidth': .5})
        good = [r for r in group if r['search_feasible'] and r.get('evidence_class') != 'assisted_repair']
        frontier = [r for r in good if not any(s['latency_ns'] <= r['latency_ns']
                    and s['energy_efficiency_queries_per_joule'] >= r['energy_efficiency_queries_per_joule']
                    and (s['latency_ns'] < r['latency_ns'] or s['energy_efficiency_queries_per_joule'] > r['energy_efficiency_queries_per_joule'])
                    for s in good)]
        frontier.sort(key=lambda r: r['latency_ns'])
        ax.plot([r['latency_ns'] for r in frontier], [r['energy_efficiency_queries_per_joule']/1e9 for r in frontier],
                color=color, linewidth=1, linestyle='--')
        titles = {'rq1_dynax_xm': 'DynaX X:M', 'rq1_block_nm': 'Block N:M',
                  'rq1_sanger_threshold': 'Sanger threshold', 'rq1_global_topk': 'Global Top-K'}
        ax.set_title(titles.get(run['algorithm'], run['algorithm']))
        ax.grid(alpha=.2)
        ax.margins(x=.12, y=.25)
    for ax in list(axes.flat)[len(data['runs']):]:
        ax.set_visible(False)
    fig.supxlabel('Latency (ns, lower is better)')
    fig.supylabel('Energy efficiency (Gqueries/J, higher is better)')
    fig.suptitle('Target 300 MHz · relative output RMSE ≤ 5%\nStars: qualified original points; diamond A1: qualified assisted repair\n'
                 'Circles: search-feasible; crosses: infeasible (nominal clock); dashed: original Pareto', fontsize=10)
    for extension in ('pdf', 'svg', 'png'):
        fig.savefig(args.experiment / f'latency_energy_efficiency.{extension}', dpi=240)
    plt.close(fig)


if __name__ == '__main__':
    main()
