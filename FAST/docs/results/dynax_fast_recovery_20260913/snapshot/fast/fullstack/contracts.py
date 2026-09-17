"""Strict, serializable contracts at the agent/tool boundary."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


def identifier(value: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid RTL identifier: {value!r}")
    return value


@dataclass(frozen=True)
class Port:
    name: str
    direction: str
    width: int

    @classmethod
    def parse(cls, obj: dict) -> 'Port':
        name = identifier(obj['name'])
        if obj['direction'] not in ('input', 'output'):
            raise ValueError('Only input/output ports are supported')
        width = obj['width']
        if type(width) is not int or not 1 <= width <= 65536:
            raise ValueError('Port width must be a positive bounded integer')
        return cls(name, obj['direction'], width)


@dataclass(frozen=True)
class Module:
    name: str
    purpose: str
    ports: tuple[Port, ...]
    dependencies: tuple[str, ...]
    implementation: str
    reference_ids: tuple[str, ...] = ()
    design_prompt: str = ''
    tests: tuple[dict, ...] = ()
    behavior: dict | None = None
    linked_reference_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SystemPlan:
    top: str
    modules: tuple[Module, ...]  # topological order, leaves first
    rationale: str
    language: str = "verilog"

    @classmethod
    def parse(cls, obj: dict, top_ports: list[dict], *, require_jobs=False) -> 'SystemPlan':
        top = identifier(obj['top'])
        language = obj.get('language', 'verilog')
        if language not in ('chisel', 'verilog'):
            raise ValueError('System language must be chisel or verilog')
        raw = obj['modules']
        if not isinstance(raw, list) or not 1 <= len(raw) <= 32:
            raise ValueError('Plan requires 1..32 modules')
        modules, test_errors = {}, []
        for entry in raw:
            name = identifier(entry['name'])
            ports = tuple(Port.parse(p) for p in entry['ports'])
            deps = tuple(identifier(d) for d in entry.get('dependencies', []))
            if name in modules or len({p.name for p in ports}) != len(ports):
                raise ValueError('Duplicate module or port')
            if len(set(deps)) != len(deps):
                raise ValueError('Duplicate dependency')
            refs = entry.get('reference_ids', [])
            if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs) or len(set(refs)) != len(refs):
                raise ValueError('reference_ids must be a list of unique catalog IDs')
            linked = entry.get('linked_reference_ids', [])
            if (not isinstance(linked, list) or any(not isinstance(r, str) for r in linked)
                    or len(set(linked)) != len(linked) or not set(linked) <= set(refs)):
                raise ValueError('linked_reference_ids must be unique assigned reference_ids')
            if linked and language != 'chisel':
                raise ValueError('Native library linking currently requires Chisel')
            prompt = entry.get('design_prompt', '')
            if not isinstance(prompt, str) or (require_jobs and not prompt.strip()):
                raise ValueError(f'{name} requires a Compiler-authored design_prompt')
            tests = entry.get('tests', [])
            behavior = entry.get('behavior')
            try:
                if behavior is not None:
                    from .behavior import compile_tests
                    generated = compile_tests(ports, behavior)
                    if tests and list(tests) != generated:
                        raise ValueError('Explicit tests cannot override executable behavior expectations')
                    tests = generated
                validate_module_tests(ports, tests, required=require_jobs and name != top)
            except ValueError as exc:
                test_errors.append(f'{name} test contract: {exc}')
            modules[name] = Module(name, str(entry['purpose']), ports, deps,
                                   str(entry['implementation']), tuple(refs), prompt, tuple(tests), behavior, tuple(linked))
        if test_errors:
            raise ValueError('; '.join(test_errors))
        if top not in modules:
            raise ValueError('Missing top module')
        expected = {Port.parse(p) for p in top_ports}
        if set(modules[top].ports) != expected:
            raise ValueError('Top ports differ from the trusted algorithm contract')
        ordered, visiting, visited = [], set(), set()
        def visit(name):
            if name not in modules:
                raise ValueError(f'Unknown dependency: {name}')
            if name in visiting:
                raise ValueError('Cyclic module graph')
            if name in visited:
                return
            visiting.add(name)
            for dep in modules[name].dependencies:
                visit(dep)
            visiting.remove(name)
            visited.add(name)
            ordered.append(modules[name])
        visit(top)
        if visited != set(modules):
            raise ValueError('Plan contains modules disconnected from top')
        return cls(top, tuple(ordered), str(obj['rationale']), language)


@dataclass(frozen=True)
class Task:
    algorithm: str
    prompt: str
    constraints: dict[str, float]
    max_loops: int = 2
    compiler_attempts: int = 2
    module_attempts: int = 3
    seed: int = 17
    kernel_profile_budget: int = 16
    activity: float = 0.1
    hdl: str = "auto"
    template_read_budget: int = 2
    module_workers: int = 1
    assembly_attempts: int = 3
    ppa_backend: str = 'yosys_opensta'
    dense_equivalent_ops_per_query: int | None = None

    @classmethod
    def parse(cls, obj: dict) -> 'Task':
        task = cls(**obj)
        for name, upper in [('max_loops', 5), ('compiler_attempts', 5), ('module_attempts', 5), ('kernel_profile_budget', 256), ('template_read_budget', 8), ('module_workers', 8), ('assembly_attempts', 5)]:
            value = getattr(task, name)
            if type(value) is not int or not 1 <= value <= upper:
                raise ValueError(f'{name} must be in 1..{upper}')
        required = {'max_quality_loss', 'max_area_um2', 'frequency_mhz'}
        if set(task.constraints) != required:
            raise ValueError(f'Constraints must contain exactly {sorted(required)}')
        for name, value in task.constraints.items():
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'Invalid constraint {name}')
        if task.constraints['frequency_mhz'] <= 0 or task.constraints['max_area_um2'] <= 0:
            raise ValueError('Frequency and area constraints must be positive')
        if not math.isfinite(task.activity) or not 0 <= task.activity <= 1:
            raise ValueError('activity must be in [0, 1]')
        if task.hdl not in ('auto', 'chisel', 'verilog'):
            raise ValueError('hdl must be auto, chisel or verilog')
        if task.ppa_backend not in ('yosys_opensta', 'hammer_openroad'):
            raise ValueError('ppa_backend must be yosys_opensta or hammer_openroad')
        if task.dense_equivalent_ops_per_query is not None and (type(task.dense_equivalent_ops_per_query) is not int
                or not 0 < task.dense_equivalent_ops_per_query <= 10**15):
            raise ValueError('dense_equivalent_ops_per_query must be a fixed positive integer or null')
        if not task.algorithm or not task.prompt:
            raise ValueError('Algorithm id and algorithm/task prompt are required')
        return task


def validate_module_tests(ports, tests, *, required=False):
    """Validate declarative planner tests; never execute model-generated test code."""
    if not isinstance(tests, (list, tuple)) or len(tests) > 32 or (required and not tests):
        raise ValueError('Non-top modules require 1..32 Compiler functional test scenarios')
    inputs = {p.name: p.width for p in ports if p.direction == 'input' and p.name != 'clock'}
    outputs = {p.name: p.width for p in ports if p.direction == 'output'}
    clocks = [p for p in ports if p.name == 'clock']
    if tests and clocks and (clocks[0].width != 1 or clocks[0].direction != 'input'):
        raise ValueError('Test clock must be a one-bit input named clock')
    for test in tests:
        if not isinstance(test, dict) or not isinstance(test.get('name'), str):
            raise ValueError('Test requires a name and steps')
        steps = test.get('steps')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 256:
            raise ValueError('Test requires 1..256 steps')
        checked = set()
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError('Test step must be an object')
            cycles = step.get('cycles', 0)
            if type(cycles) is not int or not 0 <= cycles <= 256 or (cycles and not clocks):
                raise ValueError('cycles must be 0..256; positive cycles require clock')
            for field, ports_by_name in [('inputs', inputs), ('expected', outputs)]:
                values = step.get(field, {})
                if not isinstance(values, dict):
                    raise ValueError(f'Test {field} must be an object')
                if field == 'inputs' and index == 0 and set(values) != set(inputs):
                    raise ValueError('First step must initialize every non-clock input')
                for name, value in values.items():
                    if name not in ports_by_name or type(value) is not int or not 0 <= value < 2**ports_by_name[name]:
                        raise ValueError(f'Invalid test {test["name"]} step {index} {field} value for {name}: {value}; '
                                         f'expected unsigned integer fitting {ports_by_name.get(name, "declared")} bits')
                if field == 'expected':
                    checked.update(values)
        if checked != set(outputs) or not checked:
            raise ValueError('Each scenario must check every output at least once')


def pareto(records: list[dict[str, Any]]) -> list[int]:
    """Minimize latency, maximize queries/J for the same fixed query workload.

    Legacy records derive efficiency from energy. This reciprocal transformation
    preserves dominance without reinterpreting sparse operations as useful work.
    """
    valid = [r for r in records if r.get('evaluation', {}).get('feasible')
             and math.isfinite(r['evaluation'].get('energy_nj', float('nan')))
             and r['evaluation']['energy_nj'] > 0
             and math.isfinite(r['evaluation'].get('latency_ns', float('nan')))
             and r['evaluation']['latency_ns'] > 0]
    result = []
    for record in valid:
        p = record['evaluation']
        dominated = any(
            1e9/q['evaluation']['energy_nj'] >= 1e9/p['energy_nj']
            and q['evaluation']['latency_ns'] <= p['latency_ns']
            and (1e9/q['evaluation']['energy_nj'] > 1e9/p['energy_nj']
                 or q['evaluation']['latency_ns'] < p['latency_ns'])
            for q in valid
        )
        if not dominated:
            result.append(record['round'])
    return result
