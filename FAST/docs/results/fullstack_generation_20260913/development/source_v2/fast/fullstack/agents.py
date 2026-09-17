"""Five distinct roles; all raw requests/replies are recorded before parsing."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import time

from .library import save


class JsonAgent:
    def __init__(self, llm, role: str, audit: Path):
        self.llm, self.role, self.audit = llm, role, audit
        self.calls = 0

    def ask(self, instruction: str, context: dict) -> dict:
        self.calls += 1
        path = self.audit / self.role / f'{self.calls:04d}.json'
        prompt = (f'You are FAST {self.role} Agent. Return exactly one JSON object, no markdown.\n'
                  + instruction + '\nCONTEXT:\n' + json.dumps(context, ensure_ascii=False))
        record = {'role': self.role, 'prompt': prompt, 'started_unix': time.time()}
        save(path, record)
        try:
            reply = self.llm.prompt(prompt)
            record.update(response=reply.result, success=reply.success, stderr=reply.stderr,
                          wall_seconds=time.time()-record['started_unix'])
            save(path, record)
            if not reply.success:
                raise ValueError(f'{self.role} LLM failed: {reply.stderr}')
            body = reply.result.strip()
            if body.startswith('```'):
                body = body.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            result = json.loads(body)
            if not isinstance(result, dict):
                raise ValueError('Expected a JSON object')
            return result
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
            save(path, record)
            raise


class KernelAgent(JsonAgent):
    def run(self, context):
        return self.ask('Select a legal algorithm configuration from config_space using the task prompt and measured_config_profiles. '
            'Do not change the specified algorithm. Return {"config": {...}, "rationale": "..."}. '
            'The trusted plugin will execute profiling and measure quality/sparsity; never invent measurements.', context)


class CompilerAgent(JsonAgent):
    def run(self, context):
        return self.ask('Design a COMPLETE synthesizable RTL system for the specified algorithm contract. '
            'Choose decomposition, dataflow, scheduling, buffer organization and numeric widths. '
            'Reference templates are read-only examples; you may design new modules and topology. '
            'Backend: Verilog-2005, no external IP, no blackboxes. Every dependency is a child module '
            'that must be instantiated; every module must be reachable from top. Use a few well-defined modules. '
            'All top ports must EXACTLY match algorithm ports. Declare each port separately with concrete numeric widths. '
            'Specify concrete child connections/protocol and cycle timing in implementation. '
            'Address any UArch/verification feedback; do not change the algorithm math or trusted top contract. '
            'Return {"top":"Name", "rationale":"...", "modules":[{"name":"...", "purpose":"...", '
            '"ports":[{"name":"...", "direction":"input|output", "width":1}], '
            '"dependencies":["Child"], "implementation":"detailed architecture, arithmetic and connections"}]}.', context)


class UArchAgent(JsonAgent):
    def run(self, context):
        return self.ask('Implement exactly the requested module of the Compiler system plan. '
            'Return {"rtl":"complete module source", "rationale":"..."}. '
            'Use synthesizable Verilog-2005, explicit ports exactly as specified; no includes, testbench, '
            'system tasks, initial blocks, blackboxes, external modules or preprocessor conditionals. '
            'Instantiate exactly the declared child module types using their agreed interfaces. '
            'Widen unsigned expressions before addition/multiplication to avoid silent truncation; '
            'respect finite numeric bounds and synchronous reset/handshake contract. '
            'Implement the entire function, never placeholder outputs. '
            'You may use templates as reference text, but return a new independent file. '
            'If the plan is inconsistent, return {"replan_reason":"specific interface/architecture conflict"}. '
            'After a failed check, use the diagnostics to repair this module.', context)


class CriticAgent(JsonAgent):
    def run(self, context):
        return self.ask('Analyze only the completed whole-system numerical verification and physical results. '
            'Optimize latency-energy Pareto subject to quality, cell area and clock constraints. '
            'Separate measurement from hypothesis. Power is a uniform-activity pre-layout estimate. '
            'Assign one actionable cross-layer intervention: kernel (legal sparse config), compiler '
            '(topology/scheduling), uarch (implementation under same module interfaces), or stop. '
            'Use history and retained Pareto designs; a regressing last round does not erase earlier best designs. '
            'Return {"layer":"kernel|compiler|uarch|stop", "reason":"...", '
            '"evidence":["evaluation.area_um2"], "instructions":"concrete change and expected effect"}. '
            'Each evidence string is an existing dotted path in current; include at least one.', context)


def validate_critique(value: dict, current: dict) -> dict:
    if value.get('layer') not in ('kernel', 'compiler', 'uarch', 'stop'):
        raise ValueError('Critic returned an invalid reentry layer')
    if not value.get('reason') or not value.get('instructions') or not value.get('evidence'):
        raise ValueError('Critic must provide reasoning, instructions and evidence')
    for path in value['evidence']:
        cursor = current
        if not isinstance(path, str) or not path.startswith(('evaluation.', 'profile.')):
            raise ValueError('Critic evidence must reference measured evaluation/profile')
        for part in path.split('.'):
            if not isinstance(cursor, dict) or part not in cursor:
                raise ValueError(f'Unknown Critic evidence path: {path}')
            cursor = cursor[part]
        if cursor is None:
            raise ValueError(f'Critic cites absent evidence: {path}')
    return value
