"""Exercise the actual Tcl proxy; this is not physical-design evidence."""
import ast
import os
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest

from fast.fullstack.tools import RtlTools


def emitted_tcl(policy, *, resume=False):
    # Hammer has its own isolated Python environment. This hook uses only the
    # public get_setting/block_append interface, so extract its actual body.
    path = Path(__file__).parents[1] / 'fast/fullstack/hammer_driver.py'
    functions = [n for n in ast.parse(path.read_text()).body
                 if isinstance(n, ast.FunctionDef) and n.name in {'constrain_io', 'clock_tree_resize'}]
    namespace = {'HammerTool': object}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
    class Tool:
        blocks = []
        def get_setting(self, name):
            if name == 'par.openroad.clock_tree.placement_padding':
                return 1
            assert name == 'fast.setup_repair_policy'
            return policy
        def block_append(self, value):
            self.blocks.append(value)
        def clock_tree_resize(self):
            self.blocks.append('repair_timing -setup -setup_margin 0.05')
            return True
    tool = Tool()
    namespace['clock_tree_resize' if resume else 'constrain_io'](tool)
    return '\n'.join(tool.blocks)


@pytest.mark.parametrize('policy', ['default', 'no-clone-buffer'])
def test_setup_compatibility_keeps_hold_repair_and_default_moves(policy):
    stub = '''
proc set_input_delay {args} {}
proc set_output_delay {args} {}
proc set_load {args} {}
proc all_inputs {args} {return inputs}
proc all_outputs {args} {return outputs}
proc repair_timing {args} {puts [join $args ,]}
'''
    commands = '''
repair_timing -setup -setup_margin 0.05
repair_timing -hold -hold_margin 0.01 -allow_setup_violations
repair_timing -setup -skip_gate_cloning -skip_buffering
'''
    command = shlex.split(os.environ.get('FAST_TEST_TCL_COMMAND', 'tclsh'))
    if not shutil.which(command[0]):
        pytest.skip('Tcl interpreter required; FAST_TEST_TCL_COMMAND can select the EDA container')
    # Full runs invoke the hook twice; a checkpoint restart invokes it once.
    run = subprocess.run(command, input=stub + emitted_tcl(policy)*2 + commands,
                         text=True, capture_output=True, check=True)
    assert not run.stderr
    lines = run.stdout.splitlines()
    extra = ',-skip_gate_cloning,-skip_buffering' if policy != 'default' else ''
    assert lines == ['-setup,-setup_margin,0.05' + extra,
                     '-hold,-hold_margin,0.01,-allow_setup_violations',
                     '-setup,-skip_gate_cloning,-skip_buffering']


def test_unknown_policy_fails_closed(tmp_path):
    with pytest.raises(ValueError, match='Unknown OpenROAD'):
        RtlTools(tmp_path, openroad_setup_policy='skip-all-checks')
    with pytest.raises(ValueError, match='Unknown OpenROAD'):
        emitted_tcl('skip-all-checks')


def test_checkpoint_hook_restores_constraints_and_preserves_default_repair():
    tcl = emitted_tcl('default', resume=True)
    assert 'set_input_delay 1.0 -clock clock [all_inputs -no_clocks]' in tcl
    assert 'set_output_delay 1.0 -clock clock [all_outputs]' in tcl
    assert 'set_load 5.0 [all_outputs]' in tcl
    assert 'set_placement_padding -global -left 1 -right 1' in tcl
    assert 'repair_timing -setup -setup_margin 0.05' in tcl
    assert '-skip_' not in tcl


def test_known_journal_failure_restarts_once_and_preserves_evidence(tmp_path):
    from fast.fullstack.physical import resume_clock_repair
    from fast.fullstack.library import digest
    par = tmp_path/'par-rundir'; par.mkdir()
    checkpoint = par/'pre_clock_tree_resize'; checkpoint.write_bytes(b'checkpoint')
    (par/'par.tcl').write_text('original script')
    (tmp_path/'par.log').write_text('original failure')
    class Tools:
        def command(self, command, cwd, log, env):
            assert command[-2:] == ['--from_step', 'clock_tree_resize']
            assert (cwd/'par_failed_attempt/par.tcl').read_text() == 'original script'
            (par/'par.tcl').write_text('new script')
            log.write_text('FAST_FINAL_BEGIN')
            return {'passed': True}
    result = {'par': {'passed': False}}
    assert resume_clock_repair(Tools(), tmp_path, ['hammer', 'par'], {}, result, 'unknown failure') is None
    signature = '[CRITICAL ODB-0445] No undo_updateField support for type dbTechNonDefaultRule'
    assert resume_clock_repair(Tools(), tmp_path, ['hammer', 'par'], {}, result, signature)[0]['passed']
    assert result['par_recovery']['checkpoint_sha256'] == digest(checkpoint)
    assert result['par_recovery']['original_stage']['passed'] is False
    assert result['par_recovery']['optimization_policy_changed'] is False
    assert result['par_measurement_log'] == 'par_resume.log'
    assert (tmp_path/'par.log').read_text() == 'original failure'
