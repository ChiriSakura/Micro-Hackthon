"""Load separately identified follow-up evidence without rewriting a cohort."""
import json
from pathlib import Path

from .library import digest


def load_followups(experiment: Path) -> list[dict]:
    manifest = experiment / 'followups.json'
    if not manifest.exists():
        return []
    rows, seen = [], set()
    for entry in json.loads(manifest.read_text()):
        if entry['id'] in seen or entry['evidence_class'] != 'assisted_repair':
            raise ValueError('Follow-up requires a unique ID and explicit assisted evidence class')
        seen.add(entry['id'])
        documents = {}
        for key in ('record', 'post', 'verification'):
            path = experiment / entry[key]
            if digest(path) != entry['sha256'][key]:
                raise ValueError(f'Follow-up evidence hash differs: {entry["id"]}/{key}')
            documents[key] = json.loads(path.read_text())
        record, post = documents['record'], documents['post']
        if post['algorithm'] != entry['algorithm']:
            raise ValueError('Follow-up algorithm differs from validation')
        checked = next(r for r in post['rounds'] if r['round'] == record['round'])
        evaluation = record.get('evaluation') or {}
        if (checked.get('config') != record.get('config')
                or checked.get('evaluation') != evaluation):
            raise ValueError('Follow-up record differs from independently validated design')
        qualified = bool(checked.get('independently_qualified')
            and evaluation.get('complete') and evaluation.get('feasible')
            and documents['verification'].get('passed'))
        heldout = checked.get('heldout') or {}
        rows.append({
            'evidence_id': entry['id'], 'evidence_class': entry['evidence_class'],
            'display_label': entry['label'], 'report': entry['report'],
            'algorithm': entry['algorithm'], 'round': record['round'],
            'status': record['status'], 'config': record.get('config'),
            'qualified': qualified, 'independently_qualified': qualified,
            'qualification_status': 'passed' if qualified else 'failed',
            'search_feasible': evaluation.get('feasible'),
            'heldout_rmse': heldout.get('quality_loss'), 'heldout_sparsity': heldout.get('sparsity'),
            'workload_sha256': heldout.get('workload_sha256'),
            'critic_layer': (record.get('critique') or {}).get('layer'),
            'critique': record.get('critique'), 'critique_applied': record.get('critique_applied', False),
            'system_plan': record.get('system_plan'), 'sources': record.get('sources'),
            'token_totals': post.get('token_totals'),
            'agent_calls': post.get('agent_calls', {}),
            'calls_missing_usage': post.get('calls_missing_usage'),
            **{key: evaluation.get(key) for key in ('complete', 'feasible', 'area_um2',
                'power_mw', 'frequency_mhz', 'latency_ns', 'energy_nj',
                'energy_efficiency_queries_per_joule', 'slack_ns', 'hold_slack_ns',
                'route_drc_violations')},
        })
    return rows
