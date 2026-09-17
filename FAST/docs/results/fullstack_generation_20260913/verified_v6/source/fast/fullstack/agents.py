"""Five distinct roles; all raw requests/replies are recorded before parsing."""
from __future__ import annotations

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
            'You own hardware-library retrieval and reference assignment. The hardware_catalog is an index, not code. '
            'First request relevant source using {"read_templates":["catalog_id"]}; you will receive it in reference_code. '
            'Then produce the complete plan, assigning reference_ids separately for each module. '
            'Assign only IDs you have read; UArch receives only the references you bind to its module. '
            'Use [] only when no supplied template is appropriate and explain the from-scratch design. '
            'Reference templates are read-only examples; you may design new modules and topology. '
            'Choose language chisel or verilog; obey task.hdl when not auto. Chisel backend is Scala 2.13.12/Chisel 3.6.1; '
            'Verilog backend is Verilog-2005. No external IP or blackboxes. Every dependency is a child module '
            'that must be instantiated; every module must be reachable from top. Use a few well-defined modules. '
            'All top ports must EXACTLY match algorithm ports. Declare each port separately with concrete numeric widths. '
            'Specify concrete child connections/protocol and cycle timing in implementation. '
            'Address any UArch/verification feedback; do not change the algorithm math or trusted top contract. '
            'For Chisel, every named module is a zero-argument RawModule class, with individually named IO vals '
            '(no io Bundle prefix); explicitly plan clock/reset connections and use withClockAndReset for registers. '
            'Return {"language":"chisel|verilog", "top":"Name", "rationale":"...", "modules":[{"name":"...", "purpose":"...", '
            '"ports":[{"name":"...", "direction":"input|output", "width":1}], '
            '"dependencies":["Child"], "reference_ids":["catalog_id"], '
            '"implementation":"detailed architecture, arithmetic, connections, and how to adapt selected references"}]}.', context)


class UArchAgent(JsonAgent):
    def run(self, context):
        return self.ask('Implement exactly the requested module of the Compiler system plan. '
            'Return {"source":"complete module source in system_plan.language", "rationale":"..."}. '
            'If language is chisel: use only chisel3 imports, one zero-argument class with the exact module name '
            'extending RawModule; internal Bundle/Record helper types are allowed. Do not redefine child modules. '
            'Use individually named IO vals (no io Bundle), Clock() for clock, Bool() for reset; '
            'use withClockAndReset(clock, reset) for ALL Reg/RegInit/RegNext/RegEnable creation and updates, '
            'and Module(new Child) for dependencies. Chisel UInt + truncates carry: use +& for widening sums '
            'and explicitly size each lane before packing with Cat. Assignment to a wider output does not '
            'recover carry bits lost inside intermediate expressions or concatenations. '
            'No package declaration, standalone App/main, file/process/network APIs, BlackBox, inline Verilog, '
            'compiler directives, dontTouch, print, assertion, or external libraries. Registers and IO must be fully assigned. '
            'For Chisel combinational modules without a clock port, use only combinational hardware. '
            'For Verilog: '
            'Use synthesizable Verilog-2005, explicit ports exactly as specified; no includes, testbench, '
            'system tasks, initial blocks, blackboxes, external modules or preprocessor conditionals. '
            'Instantiate exactly the declared child module types using their agreed interfaces. '
            'Widen unsigned expressions before addition/multiplication to avoid silent truncation; '
            'respect finite numeric bounds and synchronous reset/handshake contract. '
            'Implement the entire function, never placeholder outputs. '
            'Compiler has assigned reference_code and reference_provenance specifically for this module. '
            'Use that code as design guidance and explain the adaptation; return a new independent file. '
            'Critic UArch instructions may revise internal scheduling/latency while preserving the external handshake. '
            'If that conflicts with a fixed-cycle dependency in the plan, request a Compiler replan. '
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
            'Choose evidence strings VERBATIM from available_evidence; include at least one. '
            'Do not prepend current. Do not invent a path or cite system_plan as a measured metric. '
            'Address validation_feedback if a previous reply was rejected.', context)


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
