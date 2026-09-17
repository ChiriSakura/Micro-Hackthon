"""Ablation controls and audit utilities; these never change acceptance gates."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import random
import shutil
import time

from fast.schemas.models import Critique, Decision, Layer, Mutation, Status, digest_json


def atomic_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


class RecordingLLM:
    """Persist exact prompts before calls and raw replies/errors after calls."""
    def __init__(self, delegate, role, directory):
        self.delegate, self.role, self.directory = delegate, role, directory
        self.calls = []

    def prompt(self, prompt):
        started = time.monotonic()
        entry = dict(role=self.role, index=len(self.calls), prompt=prompt,
                     prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), state='running')
        self.calls.append(entry)
        path = self.directory/f'api_{self.role}_{entry["index"]:03d}.json'
        atomic_json(path, entry)
        try:
            reply = self.delegate.prompt(prompt)
            entry.update(response=getattr(reply, 'result', str(reply)),
                         success=getattr(reply, 'success', True), error=getattr(reply, 'stderr', ''),
                         usage=getattr(reply, 'usage', None))
            return reply
        except Exception as exc:
            entry.update(success=False, error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            entry.update(state='finished', wall_seconds=time.monotonic()-started)
            atomic_json(path, entry)


class LocalRandomCritic:
    """Match one-field local actions without diagnosis or model lookahead."""
    name = 'local-random-control'

    def __init__(self, seed):
        self.rng = random.Random(seed)

    def review_search(self, context):
        parent = context['parent_point']
        seen = [h['point'] for h in context['history']]
        actions = [(field, value) for field, values in context['domains'].items()
                   for value in values if value != parent[field]
                   and {**parent, field: value} not in seen]
        if not actions:
            return Critique(Status.PASSED, Layer.COMPILER, Decision.CONTINUE,
                            'No untried local action remains', ('domains', 'history'))
        field, value = self.rng.choice(actions)
        return Critique(Status.PASSED, Layer.COMPILER, Decision.CONTINUE,
                        'Uniform random untried single-field intervention; no diagnosis',
                        ('domains', 'parent_point'), (Mutation(Layer.COMPILER, field, 'set', value,
                        'measure the outcome of this local random control', 'may worsen or fail constraints'),))


def without_independent_feedback(context, model_history):
    """Remove measurements AND feasibility flags derived from independent gates."""
    filtered = deepcopy(context)
    filtered['validation'] = []
    filtered['history'] = [dict(point=asdict(h.point), metrics=deepcopy(h.metrics),
        feasible=h.feasible, violations=list(h.violations)) for h in model_history]
    filtered['scope'] += '; independent validation hidden from Critic for ablation'
    return filtered


def workload_key(design):
    task = design['task']
    identity = {key: task[key] for key in ('model', 'dataset', 'sequence_length',
                'head_dim', 'data_seed', 'capture_layer', 'capture_head', 'dtype')}
    identity.update(label=design['label'], rows=design['point']['num_rows'],
                    block=design['algorithm']['block_m'])
    return digest_json(identity)


def copy_cached_workload(cache, design, destination):
    """Reuse only a frozen same-task trace, not a hardware measurement/result."""
    index = json.loads((cache/'index.json').read_text())
    key = workload_key(design)
    entry = index[key]
    source = cache/entry['file']
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != entry['sha256']:
        raise ValueError('cached workload hash changed')
    payload = json.loads(source.read_text())
    task = design['task']
    wanted = dict(model=task['model'], seq_len=task['sequence_length'], seed=task['data_seed'],
                  layer=task['capture_layer'], head=task['capture_head'])
    if (any(payload['source'].get(k) != v for k, v in wanted.items())
        or payload['tile']['rows'] != design['point']['num_rows']
        or payload['tile']['block'] != design['algorithm']['block_m']
        or not payload['methods'][design['label']].get('complete_task')):
        raise ValueError('cached workload identity/coverage differs from the requested task')
    shutil.copyfile(source, destination)
    return dict(cache_key=key, source=str(source), sha256=actual,
                token_sha256=payload['source']['token_sha256'], hardware_result_reused=False)
