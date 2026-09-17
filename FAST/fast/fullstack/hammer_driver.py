"""Hammer CLI customization: export routed DEF/SPEF and PPA, without GDS streamout.

Executed only by the isolated Hammer environment (pydantic 1). All place/CTS/
route/extraction steps use Hammer's OpenROAD plugin, with explicit compatibility
hooks for mapping, pins, power-grid geometry, fillers, routing and reporting.
No routing stage is skipped and no synthetic PPA values are substituted.
"""
from hammer.vlsi import CLIDriver, HammerTool
from hammer.tech.specialcells import SpecialCell, CellType
from pathlib import Path
from decimal import Decimal, ROUND_CEILING
import re


def physical_cells(tool: HammerTool) -> bool:
    cells=tool.technology.config.special_cells
    if not any(c.cell_type == CellType.CTSBuffer for c in cells):
        cells.append(SpecialCell(cell_type='ctsbuffer', name=['BUF_X4','BUF_X8'], input_ports=['A'],output_ports=['Z']))
    for cell in cells:
        if cell.cell_type in (CellType.TieHiCell, CellType.TieLoCell) and not cell.output_ports:
            cell.output_ports=['Z']
    return True


def constrain_io(tool: HammerTool) -> bool:
    tool.block_append('''
    # Recent OpenROAD uses Tcl's native source, without the old echo/verbose flags.
    if {![llength [info commands fast_native_source]]} {
        rename source fast_native_source
        proc source {args} {
            set filtered {}
            foreach arg $args {
                if {$arg ni {"-echo" "-verbose"}} {lappend filtered $arg}
            }
            uplevel 1 [linsert $filtered 0 fast_native_source]
        }
    }
    set_input_delay 1.0 -clock clock [all_inputs -no_clocks]
    set_output_delay 1.0 -clock clock [all_outputs]
    set_load 5.0 [all_outputs]
    ''')
    policy = tool.get_setting('fast.setup_repair_policy')
    if policy == 'no-clone-buffer':
        # Explicit compatibility mode for the dbTechNonDefaultRule journal
        # rollback crash. Keep resizing/pin swaps, hold repair, routing,
        # extraction and all acceptance checks; never turn a violation into PASS.
        tool.block_append('''
        if {![llength [info commands fast_original_repair_timing]]} {
            rename repair_timing fast_original_repair_timing
            proc repair_timing {args} {
                if {[lsearch -exact $args -setup] >= 0} {
                    foreach flag {-skip_gate_cloning -skip_buffering} {
                        if {[lsearch -exact $args $flag] < 0} {lappend args $flag}
                    }
                }
                uplevel 1 [linsert $args 0 fast_original_repair_timing]
            }
        }
        ''')
    elif policy != 'default':
        raise ValueError('Unknown OpenROAD setup-repair policy: ' + str(policy))
    return True


def clock_tree_resize(tool: HammerTool) -> bool:
    # Keep the plugin's step name: its resume initialization indexes the native
    # step list. A late start does not run our post-init hook, so restore the
    # same IO constraints, compatibility wrapper and CTS placement padding.
    constrain_io(tool)
    padding = tool.get_setting('par.openroad.clock_tree.placement_padding')
    tool.block_append(f'set_placement_padding -global -left {padding} -right {padding}')
    return tool.clock_tree_resize()


def snap_power_grid(tool: HammerTool) -> bool:
    # Hammer's by_tracks arithmetic can emit sub-grid half spacings. Quantize
    # generated geometry upward to the Nangate45 5 nm manufacturing grid.
    path=Path(tool.run_dir)/'power_straps.tcl'
    original=path.read_text()
    path.with_suffix('.unsnapped.tcl').write_text(original)
    def snap(match):
        value=Decimal(match.group(2));grid=Decimal('0.005')
        return match.group(1)+str((value/grid).to_integral_value(rounding=ROUND_CEILING)*grid)
    path.write_text(re.sub(r'(-(?>width|spacing|pitch|offset)\s+)([0-9]+(?:\.[0-9]+)?)',snap,original))
    return True


def place_initial_pins(tool: HammerTool) -> bool:
    # OpenROAD 26Q1 ignores Hammer's obsolete `place_pins -random`, leaving
    # the clock unplaced. Run the supported deterministic pin placer instead.
    tool.block_append('place_pins -hor_layers {metal3} -ver_layers {metal2}')
    return True


def place_final_fillers(tool: HammerTool) -> bool:
    # Timing repair may insert cells after global routing. Fill remaining rows
    # only after those repairs, so a new hold buffer cannot collide with filler.
    return tool.add_fillers()


def route_current_openroad(tool: HammerTool) -> bool:
    # OpenROAD 26Q1 made routing-layer CLI flags an error; layers have already
    # been constrained by set_routing_layers in Hammer's global routing step.
    tool.block_append(f'''
    set_propagated_clock [all_clocks]
    set_thread_count {tool.get_setting('vlsi.core.max_threads')}
    detailed_route -output_drc {tool.run_dir}/{tool.top_module}_route_drc.rpt \\
      -output_maze {tool.run_dir}/{tool.top_module}_maze.log -save_guide_updates -verbose 1
    ''')
    return True


def map_sequential_cells(tool: HammerTool) -> bool:
    # Upstream Hammer 1.2 uses dfflibmap -map-only and leaves synchronous-reset
    # Yosys primitives unmapped. Full dfflibmap legalizes them before mapping.
    tool.block_append(f'''
    yosys proc
    hierarchy -check -top {tool.top_module}
    synth -top {tool.top_module} -flatten
    opt -purge
    ''')
    for liberty in tool.liberty_files_tt.split():
        tool.verbose_append(f'dfflibmap -liberty {liberty}')
    tool.verbose_append('opt_clean')
    tool.write_sdc_file()
    return True


def assert_fully_mapped(tool: HammerTool) -> bool:
    tool.verbose_append('check -assert')
    tool.verbose_append('select -assert-none {t:$*}')
    return True


def report_routed(tool: HammerTool) -> bool:
    # GDS/KLayout is intentionally outside this PPA milestone. Do not pretend
    # that the plugin's absent GDS output has been produced.
    activity=float(tool.get_setting('fast.activity'))
    fillers=' '.join(name for cell in tool.technology.get_special_cell_by_type(CellType.StdFiller) for name in cell.name)
    tool.block_append(f'''
    set_power_activity -global -activity {activity} -duty 0.5
    set_propagated_clock [all_clocks]
    global_connect
    write_db {tool.run_dir}/routed.odb
    write_def {tool.run_dir}/routed.def
    write_verilog {tool.run_dir}/routed.v
    puts FAST_FINAL_BEGIN
    report_power -corner setup -digits 8
    report_worst_slack -max -digits 8
    report_worst_slack -min -digits 8
    puts FAST_CRITICAL_PATHS_BEGIN
    report_checks -sort_by_slack -path_delay max -corner setup -group_count 3 -digits 8 -fields {{slew cap input nets fanout}}
    puts FAST_CRITICAL_PATHS_END
    report_check_types -max_slew -max_capacitance -violators
    report_design_area
    set fast_filler_names {{{fillers}}}
    ''')
    tool.block_append(r'''
    set block [ord::get_db_block]
    set dbu [$block getDbUnitsPerMicron]
    set cell_area 0.0
    foreach inst [$block getInsts] {
        set master [$inst getMaster]
        # Nangate45 LEF labels FILLCELL as CORE, not CORE_SPACER. Use the
        # technology's explicit filler inventory, retaining CTS and tie cells.
        if {[$master getName] ni $fast_filler_names} {
            set cell_area [expr {$cell_area + double([$master getWidth])*[$master getHeight]/($dbu*$dbu)}]
        }
    }
    set die [$block getDieArea]
    set core [$block getCoreArea]
    puts "FAST_CELL_AREA_UM2 $cell_area"
    puts "FAST_DIE_AREA_UM2 [expr {double([$die dx])*[$die dy]/($dbu*$dbu)}]"
    puts "FAST_CORE_AREA_UM2 [expr {double([$core dx])*[$core dy]/($dbu*$dbu)}]"
    puts FAST_FINAL_END
    ''', verbose=False)
    return True


class PpaDriver(CLIDriver):
    def get_extra_synthesis_hooks(self):
        return [HammerTool.make_pre_insertion_hook('init_environment', physical_cells),
                HammerTool.make_replacement_hook('syn_generic', map_sequential_cells),
                HammerTool.make_pre_insertion_hook('write_outputs', assert_fully_mapped)]

    def get_extra_par_hooks(self):
        return [HammerTool.make_pre_insertion_hook('init_design', physical_cells),
                HammerTool.make_post_insertion_hook('init_design', constrain_io),
                HammerTool.make_post_insertion_hook('floorplan_design', place_initial_pins),
                HammerTool.make_post_insertion_hook('power_straps', snap_power_grid),
                HammerTool.make_replacement_hook('clock_tree_resize', clock_tree_resize),
                HammerTool.make_removal_hook('add_fillers'),
                HammerTool.make_post_insertion_hook('global_route_resize', place_final_fillers),
                HammerTool.make_replacement_hook('detailed_route', route_current_openroad),
                HammerTool.make_replacement_hook('write_design', report_routed)]


if __name__ == '__main__':
    PpaDriver().main()
