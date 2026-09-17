"""Regenerate the observed latency/efficiency points from metrics.json."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
data = json.loads((root / 'metrics.json').read_text())
rows = [r for r in data['rounds'] if r['complete'] and r['feasible']]
fig, ax = plt.subplots(figsize=(7.2, 4.6), constrained_layout=True)
colors = ['#64748b', '#067a70']
for row, color in zip(rows, colors):
    x = row['latency_ns']
    y = row['energy_efficiency_queries_per_joule'] / 1e9
    ax.scatter(x, y, color=color, s=110, zorder=3)
    ax.annotate(f"Round {row['round']}\n{x:g} ns, {y:.3f} Gqueries/J", (x, y),
                xytext=(12 if row['round'] == 2 else -130, 10),
                textcoords='offset points', fontsize=10, color=color)
ax.annotate('', (rows[1]['latency_ns'], rows[1]['energy_efficiency_queries_per_joule']/1e9),
            (rows[0]['latency_ns'], rows[0]['energy_efficiency_queries_per_joule']/1e9),
            arrowprops=dict(arrowstyle='->', color='#94a3b8', linestyle='--', lw=1.5,
                            shrinkA=10, shrinkB=10))
ax.set(xlabel='Single-query latency (ns) — lower is better',
       ylabel='Energy efficiency (Gqueries/J) — higher is better',
       xlim=(145, 285), ylim=(0.7, 2.0), title='FAST autonomous DynaX: two measured feasible designs')
ax.text(0.02, 0.03, '8 keys · 100 MHz · Nangate45 · post-route modeled power\n'
        'Round 2 dominates Round 1; no global-optimum claim.', transform=ax.transAxes,
        fontsize=9, color='#475569')
ax.grid(alpha=0.2)
ax.spines[['top', 'right']].set_visible(False)
for suffix in ['png', 'pdf']:
    fig.savefig(root / f'pareto_latency_efficiency.{suffix}', dpi=200)
plt.close(fig)
