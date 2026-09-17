"""Real Hammer Yosys/OpenROAD PPA; fail closed without routed DEF and extracted SPEF."""
from pathlib import Path
import math
import os
import re
import shutil

from .library import digest, save


def extract_timing_diagnosis(log, netlist):
    """Expose measured STA paths and endpoint nets, without guessing RTL causes."""
    log = re.sub(r'\x1b\[[0-9;]*m', '', log)
    if 'FAST_CRITICAL_PATHS_BEGIN' not in log or 'FAST_CRITICAL_PATHS_END' not in log:
        return None
    section = log.rsplit('FAST_CRITICAL_PATHS_BEGIN', 1)[1].split('FAST_CRITICAL_PATHS_END', 1)[0]
    paths = []
    for start, end in re.findall(r'Startpoint:\s+(\S+).*?Endpoint:\s+(\S+)', section, re.S)[:3]:
        cells = {}
        for endpoint in (start, end):
            match = re.search(r'\b\w+\s+' + re.escape(endpoint) + r'\s*\([^;]+;', netlist)
            cells[endpoint] = match.group(0) if match else None
        paths.append({'startpoint': start, 'endpoint': end,
                      'start_cell': cells[start], 'end_cell': cells[end]})
    return {'scope': 'Post-route extracted-RC STA, setup corner; mapped endpoint nets are evidence, not automatic source-level attribution.',
            'paths': paths, 'endpoint_mapping': '\n'.join(
                f"{p['startpoint']}: {p['start_cell']} -> {p['endpoint']}: {p['end_cell']}" for p in paths),
            'report_excerpt': section[:16000]}


def resume_clock_repair(tools, run, command, env, result, failed_log):
    """One bounded retry for the known OpenDB journal failure, with full repair.

    Preserve the failing script/log and checkpoint before Hammer rewrites its
    script. Unknown failures and missing checkpoints remain failures.
    """
    checkpoint = run/'par-rundir/pre_clock_tree_resize'
    signature = '[CRITICAL ODB-0445] No undo_updateField support for type dbTechNonDefaultRule'
    if signature not in failed_log or not checkpoint.is_file():
        return None
    preserved = run/'par_failed_attempt'
    preserved.mkdir()
    for path in (run/'par.log', run/'par-rundir/par.tcl', checkpoint):
        if path.is_file():
            shutil.copy2(path, preserved/path.name)
    retry = [*command, '--from_step', 'clock_tree_resize']
    result['par_recovery'] = {
        'reason': signature, 'from_step': 'clock_tree_resize',
        'checkpoint_sha256': digest(checkpoint),
        'preserved_artifacts': {str(p.relative_to(run)): digest(p) for p in preserved.iterdir()},
        'original_stage': result['par'], 'command': retry,
        'optimization_policy_changed': False,
    }
    result['active_stage'] = 'par_resume_clock_tree_resize'
    save(run/'result.json', result)
    stage = tools.command(retry, run, run/'par_resume.log', env=env)
    result['par_recovery']['retry_stage'] = stage
    result['par'] = stage
    result['par_measurement_log'] = 'par_resume.log'
    save(run/'result.json', result)
    return stage, (run/'par_resume.log').read_text()


def evaluate_hammer(tools, plan, design, verification, profile, task, work):
    root=tools.tool_root
    run=work/'hammer';run.mkdir()
    hp=root/'env/hammer-py312/bin'
    openroad=root/'tools/bin/openroad'
    pdk=root/'pdk/hammer45'
    driver=run/'hammer_driver.py'
    driver.write_bytes(Path(__file__).with_name('hammer_driver.py').read_bytes())
    driver.chmod(0o444)
    result={'complete':False,'feasible':False,'verification':verification,'design_sha256':digest(design),
            'setup_repair_policy':getattr(tools,'openroad_setup_policy','default'),
            'ppa_backend':'hammer_openroad','scope':'entire generated top, Nangate45 placement/CTS/detailed routing/OpenRCX',
            'power_method':'OpenROAD post-route extracted-RC power estimate; uniform activity, not silicon measurement',
            'activity':task.activity,'gds_generated':False,
            'driver_sha256':digest(driver),'physical_adapter_sha256':digest(Path(__file__)),
            'routing_tool':None}
    required=[hp/'python',hp/'hammer-vlsi',openroad,pdk/'setRC.tcl',pdk/'rcx_patterns.rules',pdk/'lib/NangateOpenCellLibrary_typical.lib']
    missing=[str(p) for p in required if not p.is_file()]
    if missing:return {**result,'error':'Missing physical tools: '+', '.join(missing)}
    version=tools.command([str(openroad),'-version'],run,run/'openroad_version.log')
    if not version['passed']:return {**result,'error':'Cannot identify the physical tool version'}
    result['routing_tool']=(run/'openroad_version.log').read_text().strip()
    result['pdk_sha256']={str(path.relative_to(pdk)):digest(path) for path in
        (pdk/'setRC.tcl',pdk/'rcx_patterns.rules',pdk/'lib/NangateOpenCellLibrary_typical.lib')}
    period=1000/task.constraints['frequency_mhz']
    # Fixed floorplan policy, shared across candidates: area budget / 50% utilization.
    side=math.ceil(math.sqrt(task.constraints['max_area_um2']/0.5)/10)*10+20
    (run/'empty_latch_map.v').write_text('// No latches expected in generated synchronous logic.\n')
    config={
        'vlsi.core.technology':'hammer.technology.nangate45','vlsi.core.node':45,
        'vlsi.core.synthesis_tool':'hammer.synthesis.yosys','vlsi.core.par_tool':'hammer.par.openroad',
        'vlsi.core.build_system':'none','vlsi.core.max_threads':4,
        'technology.nangate45.install_dir':str(pdk),
        'technology.core.stackup':'nangate45_3Ma_2Mb_2Mc_2Md',
        'technology.core.std_cell_rail_layer':'metal1',
        'technology.core.std_cell_supplies':{'power':['VDD'],'ground':['VSS']},
        'vlsi.inputs.supplies':{'power':[{'name':'VDD','pins':['VDD']}],'ground':[{'name':'VSS','pins':['VSS']}], 'VDD':'1.1 V','GND':'0 V'},
        'vlsi.inputs.mmmc_corners':[{'name':'setup','type':'setup','voltage':'1.1 V','temp':'25 C'},
                                    {'name':'hold','type':'hold','voltage':'1.1 V','temp':'25 C'}],
        'synthesis.inputs.top_module':plan.top,'synthesis.inputs.input_files':[str(design)],
        'synthesis.clock_gating_mode':'auto','synthesis.yosys.latch_map_file':str(run/'empty_latch_map.v'),
        'vlsi.inputs.clocks':[{'name':'clock','period':f'{period} ns','uncertainty':'0.1 ns'}],
        'vlsi.inputs.placement_constraints':[{'path':plan.top,'type':'toplevel','x':0,'y':0,'width':side,'height':side,
                                             'margins':{'left':10,'right':10,'top':10,'bottom':10}}],
        'par.openroad.openroad_bin':str(openroad),
        'par.openroad.setrc_file':str(pdk/'setRC.tcl'),
        'par.openroad.openrcx_techfiles':[str(pdk/'rcx_patterns.rules')],
        'par.openroad.timing_driven':True,'par.openroad.write_reports':True,
        # An extra 10 ps hold margin, on top of the 100 ps clock uncertainty.
        # The plugin's default 200 ps margin inserts thousands of needless
        # buffers and can exhaust its repair budget even with positive slack.
        'par.openroad.clock_tree_resize.hold_margin':0.01,
        'par.openroad.global_route_resize.hold_margin':0.01,
        'par.power_straps_mode':'generate',
        'par.generate_power_straps_options.by_tracks.strap_layers':['metal4','metal7'],
        'par.generate_power_straps_options.by_tracks.pin_layers':['metal7'],
        'par.generate_power_straps_options.by_tracks.track_width':4,
        'par.generate_power_straps_options.by_tracks.track_spacing':0,
        'par.generate_power_straps_options.by_tracks.power_utilization':0.05,
        'fast.activity':task.activity,
        'fast.setup_repair_policy':result['setup_repair_policy'],
    }
    save(run/'config.json',config)
    env=os.environ.copy();env['PATH']=str(hp)+':'+str(root/'tools/bin')+':'+str(openroad.parent)+':'+env.get('PATH','')
    for action,extra,output in [('syn',[],'syn-output.json'),('syn-to-par',['-p',str(run/'syn-output.json')],'par-input.json'),
                          ('par',['-p',str(run/'par-input.json')],'par-output.json')]:
        command=[str(hp/'python'),str(driver),action,'-p',str(run/'config.json'),*extra,'--obj_dir',str(run),'-o',str(run/output)]
        result['active_stage'] = action
        save(run/'result.json', result)
        stage=tools.command(command,run,run/f'{action}.log',env=env)
        result[action]=stage
        save(run/'result.json', result)
        stage_log=(run/f'{action}.log').read_text()
        if action == 'par' and (not stage['passed'] or 'ERROR: OpenROAD returned with a nonzero exit code' in stage_log):
            recovered = resume_clock_repair(tools, run, command, env, result, stage_log)
            if recovered is not None:
                stage, stage_log = recovered
        if not stage['passed'] or 'ERROR: OpenROAD returned with a nonzero exit code' in stage_log:
            result['error']=f'Hammer {action} failed';save(run/'result.json',result);return result
    par=run/'par-rundir';spefs=list(par.glob('*.spef'))
    artifacts=[par/'routed.def',par/'routed.v',par/'routed.odb',*spefs]
    if not spefs or any(not p.is_file() or p.stat().st_size==0 for p in artifacts):
        return {**result,'error':'Routed DEF/netlist/database or extracted SPEF missing'}
    if not any('*D_NET' in p.read_text() for p in spefs):
        return {**result,'error':'SPEF has no extracted nets'}
    drc=par/f'{plan.top}_route_drc.rpt'
    if not drc.is_file():
        return {**result,'error':'Detailed-route DRC report missing'}
    drc_text=drc.read_text()
    violations=len(re.findall(r'violation\s+type\s*:',drc_text,re.I))
    if drc_text.strip() and not violations:
        return {**result,'error':'Unrecognized nonempty detailed-route DRC report'}
    result.update(route_drc_violations=violations,io_delay_ns=1.0,output_load_ff=5.0,
                  process_corner='Nangate45 typical 1.1 V 25 C for setup and hold; not multi-PVT signoff')
    artifacts.append(drc)
    log=(run/result.get('par_measurement_log', 'par.log')).read_text()
    section=log.rsplit('FAST_FINAL_BEGIN',1)[-1]
    # Hammer prefixes subprocess output with color/labels; strip those first.
    section=re.sub(r'\x1b\[[0-9;]*m','',section)
    result['timing_diagnosis'] = extract_timing_diagnosis(log, (par/'routed.v').read_text())
    def value(pattern):
        found=re.search(pattern,section,re.M)
        if not found:raise ValueError('Missing physical metric: '+pattern)
        return float(found.group(1))
    try:
        area=value(r'FAST_CELL_AREA_UM2\s+([\d.eE+-]+)')
        die=value(r'FAST_DIE_AREA_UM2\s+([\d.eE+-]+)');core=value(r'FAST_CORE_AREA_UM2\s+([\d.eE+-]+)')
        power=value(r'Total\s+[\d.eE+-]+\s+[\d.eE+-]+\s+[\d.eE+-]+\s+([\d.eE+-]+)')
        slack=value(r'worst slack max\s+([\d.eE+-]+)')
        hold=value(r'worst slack min\s+([\d.eE+-]+)')
        latency=verification['mean_cycles']*period;energy=power*latency
        if not all(math.isfinite(x) for x in (area,power,slack,hold,latency,energy)) or min(area,power,latency,energy)<=0:
            raise ValueError('Invalid physical metrics')
        result.update(complete=True,area_um2=area,die_area_um2=die,core_area_um2=core,
            power_mw=power*1000,slack_ns=slack,hold_slack_ns=hold,frequency_mhz=task.constraints['frequency_mhz'],
            latency_ns=latency,energy_nj=energy,energy_efficiency_queries_per_joule=1e9/energy,
            quality_loss=profile['quality_loss'],
            efficiency_scope='one verified query; energy = modeled average power times single-query latency',
            feasible=violations==0 and slack>=0 and hold>=0 and area<=task.constraints['max_area_um2'] and profile['quality_loss']<=task.constraints['max_quality_loss'],
            artifacts={str(p.relative_to(work)):digest(p) for p in artifacts})
        if task.dense_equivalent_ops_per_query:
            result.update(dense_equivalent_ops_per_query=task.dense_equivalent_ops_per_query,
                          energy_efficiency_dense_equivalent_tops_per_w=task.dense_equivalent_ops_per_query/(energy*1000))
    except ValueError as exc:result['error']=str(exc)
    save(run/'result.json',result)
    return result
