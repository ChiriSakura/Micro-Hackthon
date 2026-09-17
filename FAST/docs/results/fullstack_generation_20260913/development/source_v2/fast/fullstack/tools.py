"""Generic generated-Verilog checks and full-top physical evaluation.

Generated HDL never supplies test code or arbitrary shell commands. All command
arguments and source paths come from the orchestrator. This is not an OS sandbox;
use a restricted worker for untrusted models/plugins in a multi-user deployment.
"""
from __future__ import annotations

from dataclasses import asdict
import math
from pathlib import Path
import re
import subprocess
import time

from fast.adapters.synthesis import YosysSynthesisAdapter
from fast.adapters.timing import OpenStaTimingAdapter
from .contracts import Module, SystemPlan, Task
from .library import digest, save


def check_source(source: str, module: Module) -> None:
    if not isinstance(source, str) or len(source) > 200_000:
        raise ValueError('Missing/oversized RTL source')
    code = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    if '`' in code or re.search(r'\$(?!clog2\b)|\b(initial|final|bind|force|release|specify)\b', code):
        raise ValueError('Generated RTL contains test/simulation/preprocessor constructs')
    if re.findall(r'\bmodule\s+(\w+)', code) != [module.name] or len(re.findall(r'\bendmodule\b', code)) != 1:
        raise ValueError('Return exactly the requested module')
    # Both ANSI and non-ANSI declarations are normal Verilog. Validate explicit
    # numeric widths, without rejecting a correct implementation for formatting.
    header = code.split(');', 1)[0]
    declaration_text = header + ');' if re.search(r'\b(input|output)\b', header) else code
    matches = re.findall(r'\b(input|output)\s+(?:(?:wire|reg)\s+)?(?:\[\s*(\d+)\s*:\s*0\s*\]\s*)?(\w+)\s*(?=,|\)|;)', declaration_text)
    actual = {(name, direction, int(msb)+1 if msb else 1) for direction, msb, name in matches}
    expected = {(p.name, p.direction, p.width) for p in module.ports}
    if actual != expected or len(matches) != len(module.ports):
        raise ValueError(f'Ports differ from plan. Declare each port separately with numeric width: '
                         f'actual={sorted(actual)}, expected={sorted(expected)}')
    # Remove balanced parameter overrides before recognizing named child instances.
    # Verilator subsequently checks the real instantiated interfaces and widths.
    instance_code = code
    while re.search(r'#\s*\(', instance_code):
        match = re.search(r'#\s*\(', instance_code)
        depth, index = 1, match.end()
        while index < len(instance_code) and depth:
            depth += (instance_code[index] == '(') - (instance_code[index] == ')')
            index += 1
        if depth:
            raise ValueError('Unbalanced parameter override')
        instance_code = instance_code[:match.start()] + ' ' + instance_code[index:]
    if '#' in instance_code:
        raise ValueError('Simulation delays are forbidden in generated RTL')
    instances = set(re.findall(r'\b(\w+)\s+(\w+)\s*\(\s*\.', instance_code))
    children = {kind for kind, _ in instances}
    if children != set(module.dependencies):
        raise ValueError(f'Instantiated children {sorted(children)} differ from plan {module.dependencies}; use named ports')



class RtlTools:
    def __init__(self, tool_root: Path, timeout: int = 300):
        self.tool_root, self.timeout = tool_root.resolve(), timeout

    def command(self, args: list[str], cwd: Path, log: Path) -> dict:
        started = time.monotonic()
        try:
            proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            output, passed = proc.stdout + proc.stderr, proc.returncode == 0
        except subprocess.TimeoutExpired as exc:
            output, passed = f'Tool timeout after {self.timeout}s: {exc}', False
        except OSError as exc:
            output, passed = str(exc), False
        log.write_text(output)
        record = {'passed': passed, 'log': str(log), 'diagnostics': output[-16000:],
                  'wall_seconds': time.monotonic()-started, 'command': args}
        save(log.with_suffix('.json'), record)
        return record

    def verilator(self):
        return ['apptainer', 'exec', str(self.tool_root/'containers/verilator.sif'), 'verilator']

    def module(self, module: Module, sources: list[Path], work: Path) -> dict:
        # Elaborate the real dependencies and lint the implementation. This is structural,
        # not standalone functional equivalence; full numerical checks follow at system level.
        return self.command(self.verilator() + ['--lint-only', '--Wall', '-Wno-fatal',
            '--top-module', module.name, *map(str, sources)], work, work/'module_lint.log')

    def verify(self, plan: SystemPlan, sources: list[Path], trusted: dict, work: Path) -> dict:
        tb = work/'trusted_testbench.sv'
        tb.write_text(trusted['testbench'])
        tb.chmod(0o444)
        tb_hash = digest(tb)
        save(work/'trusted_vectors.json', {k:v for k,v in trusted.items() if k != 'testbench'})
        built = self.command(self.verilator() + ['--binary', '--timing', '--assert', '-Wno-fatal',
            '--top-module', 'FASTTestbench', '-j', '2', '-Mdir', str(work/'obj_dir'),
            *map(str, sources), str(tb)], work, work/'e2e_build.log')
        if not built['passed']:
            return {'passed': False, 'stage': 'build', 'build': built}
        result = self.command(['apptainer', 'exec', str(self.tool_root/'containers/verilator.sif'),
            str(work/'obj_dir/VFASTTestbench')], work, work/'e2e_sim.log')
        text = (work/'e2e_sim.log').read_text()
        cycles = [int(n) for n in re.findall(r'^FAST_CASE cycles=(\d+)$', text, re.M)]
        count = trusted['expected_cases']
        passed = (result['passed'] and f'FAST_PASS cases={count}' in text
                  and len(cycles) == count and all(c > 0 for c in cycles) and digest(tb) == tb_hash)
        return {'passed': passed, 'stage': 'simulation', 'simulation': result,
                'cases': len(cycles), 'expected_cases': count,
                'mean_cycles': sum(cycles)/len(cycles) if cycles else None,
                'min_cycles': min(cycles) if cycles else None, 'max_cycles': max(cycles) if cycles else None,
                'testbench_sha256': tb_hash, 'coverage': trusted['coverage']}

    def evaluate(self, plan: SystemPlan, sources: list[Path], verification: dict,
                 profile: dict, task: Task, work: Path) -> dict:
        if not verification['passed']:
            raise ValueError('PPA requires independent whole-system functional verification')
        design = work/'whole_system.v'
        design.write_text('\n'.join(p.read_text() for p in sources))
        liberty = self.tool_root/'pdk/nangate45/NangateOpenCellLibrary_typical.lib'
        synth = YosysSynthesisAdapter(self.tool_root/'containers/yosys.sif', liberty,
                                     timeout_seconds=self.timeout, work_root=work)
        sy = synth.synthesize(design, plan.top, work/'mapped.v')
        result = {'complete': False, 'feasible': False, 'synthesis': asdict(sy),
                  'verification': verification, 'design_sha256': digest(design),
                  'scope': 'entire generated top and all instantiated modules, memories mapped to flops',
                  'power_method': 'OpenSTA uniform-activity estimate, pre-layout Nangate45',
                  'activity': task.activity}
        if not sy.success:
            return result
        sta = OpenStaTimingAdapter(self.tool_root/'containers/opensta.sif', liberty,
                                   timeout_seconds=self.timeout, work_root=work)
        period = 1000/task.constraints['frequency_mhz']
        ti = sta.analyse(work/'mapped.v', plan.top, period_ns=period, activity=task.activity)
        result['timing'] = asdict(ti)
        metrics = [sy.cell_area_um2, ti.total_power_w, ti.slack_ns, verification['mean_cycles']]
        if not ti.success or any(x is None or not math.isfinite(x) for x in metrics):
            return result
        latency = verification['mean_cycles'] * period
        result.update(complete=True, area_um2=sy.cell_area_um2, power_mw=ti.total_power_w*1000,
            frequency_mhz=task.constraints['frequency_mhz'], max_frequency_mhz=ti.max_frequency_mhz,
            slack_ns=ti.slack_ns, latency_ns=latency, energy_nj=ti.total_power_w*latency,
            quality_loss=profile['quality_loss'],
            feasible=(ti.timing_credible and ti.slack_ns >= 0
                      and sy.cell_area_um2 <= task.constraints['max_area_um2']
                      and profile['quality_loss'] <= task.constraints['max_quality_loss']))
        return result
