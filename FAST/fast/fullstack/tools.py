"""Generic generated-Verilog checks and full-top physical evaluation.

Generated HDL never supplies test code or arbitrary shell commands. All command
arguments and source paths come from the orchestrator. This is not an OS sandbox;
use a restricted worker for untrusted models/plugins in a multi-user deployment.
"""
from __future__ import annotations

from dataclasses import asdict
import math
import os
from pathlib import Path
import re
import subprocess
import signal
import time

from fast.adapters.synthesis import YosysSynthesisAdapter
from fast.adapters.timing import OpenStaTimingAdapter
from .contracts import Module, SystemPlan, Task, validate_module_tests
from .library import digest, save


def check_source(source: str, module: Module) -> None:
    if not isinstance(source, str) or len(source) > 200_000:
        raise ValueError('Missing/oversized RTL source')
    code = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    if '`' in code or re.search(r'\$(?!clog2\b)|\b(initial|final|bind|force|release|specify)\b', code):
        raise ValueError('Generated RTL contains test/simulation/preprocessor constructs')
    if re.findall(r'\bmodule\s+(\w+)', code) != [module.name] or len(re.findall(r'\bendmodule\b', code)) != 1:
        raise ValueError('Return exactly the requested module')
    check_verilog_ports(code, module)
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



def check_verilog_ports(code: str, module: Module) -> None:
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


def check_chisel_source(source: str, module: Module, *, library_symbols=None) -> None:
    if not isinstance(source, str) or len(source) > 200_000:
        raise ValueError('Missing/oversized Chisel source')
    if re.search(r'//\s*>', source):
        raise ValueError('Build directives belong to the trusted elaborator')
    code = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    definitions = re.findall(r'\bclass\s+(\w+)\s*(?:\([^{}]*?\))?\s+extends\s+(\w+)', code)
    hardware = [(name, base) for name, base in definitions if base not in ('Bundle', 'Record')]
    if hardware != [(module.name, 'RawModule')]:
        raise ValueError(f'Return exactly the requested hardware RawModule: expected only '
            f'{[(module.name, "RawModule")]}, found {hardware}. '
            'Do NOT paste additional hardware class definitions into the generated adapter. '
            'Native classes explicitly assigned through linked_reference_ids are compiled separately; '
            'instantiate those unchanged classes rather than copying their definitions. '
            'Bundle/Record helper types are allowed. If a separate hardware child is necessary, request '
            'Compiler replan to link a compatible library reference or declare and dispatch a new child. '
            'Unlinked references remain guidance only.')
    if len(definitions) != len(re.findall(r'\bclass\s+\w+', code)):
        raise ValueError('Unsupported Chisel helper class; use Bundle or Record for hardware data types')
    if not re.search(r'\bclass\s+' + re.escape(module.name) + r'\s*(?:\(\s*\))?\s+extends\s+RawModule\b', code):
        raise ValueError('Use a zero-argument RawModule with explicit flat IOs')
    forbidden = r'\b(package|object|App|BlackBox|ExtModule|HasBlackBoxInline|HasBlackBoxResource|System|Runtime|Process|sys|java|javax|reflect|Class|ClassLoader|Source|File|Files|URL|Socket|println|printf|assert|assume|cover)\b'
    if re.search(forbidden, code):
        raise ValueError('Chisel source contains unsupported executable/external/test constructs')
    symbols = library_symbols or {'classes': [], 'packages': []}
    for line in code.splitlines():
        if re.match(r'\s*import\s+', line):
            allowed = re.match(r'\s*import\s+chisel3(?:\.|\s)', line) or any(
                re.match(r'\s*import\s+' + re.escape(package) + r'\.', line)
                for package in symbols['packages'])
            if not allowed:
                raise ValueError('Only chisel3 and explicitly linked read-only library package imports are supported')
    children = set(re.findall(r'\bModule\s*\(\s*new\s+([\w.]+)', code))
    if not set(module.dependencies) <= children or children - set(module.dependencies) - set(symbols['classes']):
        raise ValueError(f'Chisel children {sorted(children)} differ from plan {module.dependencies}')


class RtlTools:
    def __init__(self, tool_root: Path, timeout: int = 300, *, openroad_setup_policy: str = 'default'):
        if openroad_setup_policy not in {'default', 'no-clone-buffer'}:
            raise ValueError('Unknown OpenROAD setup-repair policy')
        self.tool_root, self.timeout = tool_root.resolve(), timeout
        self.openroad_setup_policy = openroad_setup_policy

    def command(self, args: list[str], cwd: Path, log: Path, *, env=None) -> dict:
        started = time.monotonic()
        log.parent.mkdir(parents=True, exist_ok=True)
        timed_out, returncode = False, None
        # Stream output to disk: a scheduler kill must not discard an hour of
        # routing diagnostics. Own a process group so timeouts kill descendants.
        with log.open('w') as stream:
            try:
                proc = subprocess.Popen(args, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                        env=env, start_new_session=True, text=True)
                try:
                    returncode = proc.wait(timeout=self.timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    os.killpg(proc.pid, signal.SIGKILL)
                    returncode = proc.wait()
                    stream.write(f'\nTool timeout after {self.timeout}s\n')
                except BaseException:
                    if proc.poll() is None:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    raise
            except OSError as exc:
                stream.write(str(exc))
        output = log.read_text(errors='replace')
        record = {'passed': returncode == 0 and not timed_out, 'log': str(log),
                  'diagnostics': output[-16000:], 'timed_out': timed_out, 'returncode': returncode,
                  'wall_seconds': time.monotonic()-started, 'command': args}
        save(log.with_suffix('.json'), record)
        return record

    def verilator(self):
        return ['apptainer', 'exec', str(self.tool_root/'containers/verilator.sif'), 'verilator']

    def module(self, module: Module, sources: list[Path], work: Path,
               language: str = 'verilog') -> dict:
        # Elaborate/lint each module with real children, then numerically verify the whole system.
        elaboration = None
        if language == 'chisel':
            elaboration = self.elaborate(module, sources, work)
            if not elaboration['passed']:
                return elaboration
            sources = [Path(elaboration['elaborated_verilog'])]
        result = self.command(self.verilator() + ['--lint-only', '--Wall', '-Wno-fatal',
            '--top-module', module.name, *map(str, sources)], work, work/'module_lint.log')
        if elaboration:
            result['elaboration'] = elaboration
            result['elaborated_verilog'] = elaboration['elaborated_verilog']
        result['scope'] = 'elaboration/lint only'
        if result['passed'] and module.tests:
            functional = work/'functional'
            functional.mkdir()
            result['functional'] = self.verify(
                SystemPlan(module.name, (module,), 'Compiler module contract'),
                sources, module_testbench(module), functional)
            for metric in ('mean_cycles', 'min_cycles', 'max_cycles'):
                result['functional'].pop(metric, None)  # markers count scenarios, not module latency
            result['test_oracle'] = ('computed executable behavior contract' if module.behavior
                                     else 'explicit Compiler vectors')
            result['passed'] = result['functional']['passed']
            result['scope'] = 'structure and frozen Compiler functional vectors; not independent algorithm equivalence'
        return result

    def elaborate(self, module: Module, sources: list[Path], work: Path) -> dict:
        driver = work/'FASTGeneratedElaborate.scala'
        driver.write_text('''//> using scala "2.13.12"
//> using dep "edu.berkeley.cs::chisel3:3.6.1"
//> using plugin "edu.berkeley.cs:::chisel3-plugin:3.6.1"
import chisel3.stage.{ChiselGeneratorAnnotation, ChiselStage}
object FASTGeneratedElaborate extends App {
  (new ChiselStage).execute(Array("--target-dir", args(0), "-X", "verilog"),
    Seq(ChiselGeneratorAnnotation(() => new ''' + module.name + ''')))
}
''')
        environment = dict(os.environ)
        environment.setdefault('COURSIER_CACHE', str(self.tool_root/'cache/coursier'))
        environment.setdefault('SCALA_CLI_HOME', str(self.tool_root/'cache/scala-cli'))
        build_workspace = work/'scala_build'
        output = work/'emitted'
        result = self.command([str(self.tool_root/'tools/scala-cli'), 'run',
            *map(str, sources), str(driver), '--workspace', str(build_workspace),
            '--server=false', '--main-class', 'FASTGeneratedElaborate', '--', str(output)],
            work, work/'chisel_elaboration.log', env=environment)
        emitted = output/f'{module.name}.v'
        if result['passed']:
            try:
                code = re.sub(r'/\*.*?\*/|//[^\n]*', '', emitted.read_text(), flags=re.S)
                top = re.search(r'\bmodule\s+' + re.escape(module.name) + r'\b.*?\bendmodule\b', code, re.S)
                if top is None:
                    raise ValueError('Elaboration did not emit the declared top')
                check_verilog_ports(top.group(), module)
                result['elaborated_verilog'] = str(emitted)
                result['elaborated_sha256'] = digest(emitted)
            except (OSError, ValueError) as exc:
                result.update(passed=False, diagnostics=str(exc))
        save(work/'chisel_elaboration.json', result)
        return result

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
        if task.ppa_backend == 'hammer_openroad':
            from .physical import evaluate_hammer
            return evaluate_hammer(self, plan, design, verification, profile, task, work)
        liberty = self.tool_root/'pdk/nangate45/NangateOpenCellLibrary_typical.lib'
        synth = YosysSynthesisAdapter(self.tool_root/'containers/yosys.sif', liberty,
                                     timeout_seconds=self.timeout, work_root=work)
        sy = synth.synthesize(design, plan.top, work/'mapped.v')
        result = {'complete': False, 'feasible': False, 'synthesis': asdict(sy),
                  'verification': verification, 'design_sha256': digest(design),
                  'scope': 'entire generated top and all instantiated modules, memories mapped to flops',
                  'power_method': 'OpenSTA uniform-activity estimate, pre-layout Nangate45',
                  'activity': task.activity}
        result['ppa_backend'] = 'yosys_opensta'
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
        energy = result['energy_nj']
        if energy <= 0 or latency <= 0:
            result.update(complete=False, feasible=False, error='Nonpositive energy or latency')
        else:
            result.update(energy_efficiency_queries_per_joule=1e9/energy,
                          efficiency_scope='one verified query; energy = modeled average power times single-query latency')
            if task.dense_equivalent_ops_per_query:
                result.update(dense_equivalent_ops_per_query=task.dense_equivalent_ops_per_query,
                              energy_efficiency_dense_equivalent_tops_per_w=task.dense_equivalent_ops_per_query/(energy*1000))
        return result


def module_testbench(module: Module) -> dict:
    """Render bounded declarative tests, with no model-supplied executable code."""
    validate_module_tests(module.ports, module.tests, required=True)
    lines = ['module FASTTestbench;']
    for port in module.ports:
        kind = 'reg' if port.direction == 'input' else 'wire'
        lines.append(f'{kind} [{port.width-1}:0] {port.name};')
    lines.append(f'{module.name} dut(' + ','.join(f'.{p.name}({p.name})' for p in module.ports) + ');')
    clock = any(p.name == 'clock' for p in module.ports)
    lines.append('initial begin')
    if clock:
        lines.append('clock=0;')
    widths = {p.name: p.width for p in module.ports}
    for scenario, test in enumerate(module.tests):
        for index, step in enumerate(test['steps']):
            for name, value in step.get('inputs', {}).items():
                lines.append(f"{name}={widths[name]}'d{value};")
            lines.append('#5;')
            cycles = step.get('cycles', 0)
            if cycles:
                lines.append(f'repeat ({cycles}) begin clock=1; #5; clock=0; #5; end')
            for name, value in step.get('expected', {}).items():
                lines.append(f'if ({name} !== {widths[name]}\'d{value}) '
                    f'$fatal(1,"module case={scenario} step={index} output={name} expected={value} actual=%0d",{name});')
        lines.append('$display("FAST_CASE cycles=1");')
    lines.extend([f'$display("FAST_PASS cases={len(module.tests)}");', '$finish;', 'end', 'endmodule'])
    return {'testbench': '\n'.join(lines), 'vectors': list(module.tests),
            'expected_cases': len(module.tests),
            'coverage': 'Compiler-authored module scenarios; cycle marker is a case counter, not performance evidence'}
