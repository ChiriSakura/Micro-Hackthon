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


@dataclass(frozen=True)
class SystemPlan:
    top: str
    modules: tuple[Module, ...]  # topological order, leaves first
    rationale: str
    language: str = "verilog"

    @classmethod
    def parse(cls, obj: dict, top_ports: list[dict]) -> 'SystemPlan':
        top = identifier(obj['top'])
        language = obj.get('language', 'verilog')
        if language not in ('chisel', 'verilog'):
            raise ValueError('System language must be chisel or verilog')
        raw = obj['modules']
        if not isinstance(raw, list) or not 1 <= len(raw) <= 32:
            raise ValueError('Plan requires 1..32 modules')
        modules = {}
        for entry in raw:
            name = identifier(entry['name'])
            ports = tuple(Port.parse(p) for p in entry['ports'])
            deps = tuple(identifier(d) for d in entry.get('dependencies', []))
            if name in modules or len({p.name for p in ports}) != len(ports):
                raise ValueError('Duplicate module or port')
            if len(set(deps)) != len(deps):
                raise ValueError('Duplicate dependency')
            modules[name] = Module(name, str(entry['purpose']), ports, deps,
                                   str(entry['implementation']))
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

    @classmethod
    def parse(cls, obj: dict) -> 'Task':
        task = cls(**obj)
        for name, upper in [('max_loops', 5), ('compiler_attempts', 5), ('module_attempts', 5), ('kernel_profile_budget', 256)]:
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
        if not task.algorithm or not task.prompt:
            raise ValueError('Algorithm id and algorithm/task prompt are required')
        return task


def pareto(records: list[dict[str, Any]]) -> list[int]:
    """Minimize energy per task and latency, only among measured feasible designs."""
    valid = [r for r in records if r.get('evaluation', {}).get('feasible')]
    result = []
    for record in valid:
        p = record['evaluation']
        dominated = any(
            q['evaluation']['energy_nj'] <= p['energy_nj']
            and q['evaluation']['latency_ns'] <= p['latency_ns']
            and (q['evaluation']['energy_nj'] < p['energy_nj']
                 or q['evaluation']['latency_ns'] < p['latency_ns'])
            for q in valid
        )
        if not dominated:
            result.append(record['round'])
    return result
