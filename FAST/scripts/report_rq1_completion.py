#!/usr/bin/env python3
"""Audit the four-algorithm continuation; never fill missing PPA or qualification."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.library import save
from fast.fullstack.recovery import read_summary
from fast.fullstack.report_evidence import load_followups

NAMES = {'rq1_global_topk': 'Global Top-K', 'rq1_sanger_threshold': 'Sanger 概率阈值',
         'rq1_dynax_xm': 'DynaX X:M', 'rq1_block_nm': 'Block N:M'}


def number(value, scale=1):
    return '—' if value is None else f'{value*scale:.6g}'


def build_report(experiment):
    jobs = json.loads((experiment/'jobs.json').read_text())
    scheduler = {}
    try:
        proc = subprocess.run(['sacct', '-n', '-X', '-j', ','.join(str(j['job_id']) for j in jobs),
            '--format=JobIDRaw,State%30,Elapsed', '-P'], capture_output=True, text=True, timeout=20)
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                fields = line.split('|')
                if len(fields) >= 3:
                    scheduler[fields[0]] = {'state': fields[1], 'elapsed': fields[2]}
    except (OSError, subprocess.TimeoutExpired):
        pass  # Reading archived results does not require access to SLURM.
    rows, runs, designs = [], [], []
    baseline = experiment/'dynax_baseline/results.json'
    dynax_post = json.loads(baseline.read_text()) if baseline.exists() else {}
    for job in jobs:
        requested_run = Path(job['run'])
        run = requested_run
        if not (run/'summary.json').exists() and not list(run.glob('round_*/result.json')) and job.get('previous_run'):
            run = Path(job['previous_run'])
        summary = read_summary(run)
        scheduled = scheduler.get(str(job['job_id']), {})
        reported_status = 'resume_not_started' if run != requested_run else summary['status']
        state = scheduled.get('state', '').split()
        if (reported_status == 'running' and state and state[0] in
                {'TIMEOUT', 'CANCELLED', 'FAILED', 'OUT_OF_MEMORY', 'NODE_FAIL', 'PREEMPTED', 'COMPLETED'}):
            reported_status = 'interrupted_with_checkpoint'
        output = Path(job['output'])/'results.json'
        post = json.loads(output.read_text()) if output.exists() else {}
        previous = Path(job.get('previous_output', experiment/'_absent'))/'results.json'
        previous_post = json.loads(previous.read_text()) if previous.exists() else {}
        checks = {r['round']: r for r in post.get('rounds', [])}
        for record in summary['rounds']:
            evaluation = record.get('evaluation') or {}
            verified = checks.get(record['round'], {})
            # An unchanged historical baseline can retain its independently
            # checked result, but a round number alone is never sufficient.
            if 'independently_qualified' not in verified:
                historical = previous_post.get('rounds', []) + (dynax_post.get('rounds', []) if job['algorithm'] == 'rq1_dynax_xm' else [])
                for old in historical:
                    old_eval = old.get('evaluation') or {}
                    if (old.get('independently_qualified') and old.get('config') == record.get('config')
                            and old_eval.get('design_sha256') and old_eval.get('design_sha256') == evaluation.get('design_sha256')
                            and old_eval.get('artifacts') and old_eval.get('artifacts') == evaluation.get('artifacts')):
                        verified = old
            heldout = verified.get('heldout') or {}
            qualification = ('passed' if verified.get('independently_qualified') else
                'failed' if 'independently_qualified' in verified else
                'pending' if record['round'] in summary['pareto_rounds'] else 'not_selected')
            row = {'algorithm': job['algorithm'], 'round': record['round'], 'status': record['status'],
                'config': record.get('config'), 'qualified': verified.get('independently_qualified', False),
                'qualification_status': qualification,
                'setup_repair_policy': evaluation.get('setup_repair_policy', 'default') if evaluation else None,
                'heldout_rmse': heldout.get('quality_loss'), 'heldout_sparsity': heldout.get('sparsity'),
                'critic_layer': (record.get('critique') or {}).get('layer'),
                'critique_applied': record.get('critique_applied', False),
                'rollback_to_round': record.get('rollback_to_round') if not (record.get('prior_evaluations') and evaluation.get('complete')) else None,
                'historical_rollback_to_round': record.get('rollback_to_round') if record.get('prior_evaluations') and evaluation.get('complete') else None,
                'ppa_retries': len(record.get('prior_evaluations', [])),
                'physical_checkpoint_recovery': evaluation.get('par_recovery'),
                'error': record.get('error') or evaluation.get('error'),
                **{k: evaluation.get(k) for k in ('complete', 'feasible', 'area_um2', 'power_mw', 'latency_ns',
                    'energy_nj', 'energy_efficiency_queries_per_joule', 'frequency_mhz', 'slack_ns',
                    'hold_slack_ns', 'route_drc_violations')}}
            rows.append(row)
            plan = record.get('system_plan') or {}
            if plan:
                designs.append({'algorithm': job['algorithm'], 'round': record['round'], 'top': plan['top'],
                    'language': plan.get('language'), 'config': record.get('config'),
                    'modules': [{'name': m['name'], 'purpose': m.get('purpose'),
                        'latency': (m.get('behavior') or {}).get('latency'),
                        'linked_reference_ids': m.get('linked_reference_ids', [])} for m in plan['modules']]})
        origin_path = run/'recovery_origin.json'
        origin = Path(json.loads(origin_path.read_text())['original_run']) if origin_path.exists() else None
        costs = {'calls': 0, 'tokens': 0, 'new_calls': 0, 'new_tokens': 0, 'new_calls_missing_usage': 0}
        for call_path in (run/'agent_calls').rglob('*.json'):
            call = json.loads(call_path.read_text())
            tokens = (call.get('usage') or {}).get('total_token_count') or 0
            costs['calls'] += 1; costs['tokens'] += tokens
            if origin is not None and not (origin/call_path.relative_to(run)).exists():
                costs['new_calls'] += 1; costs['new_tokens'] += tokens
                costs['new_calls_missing_usage'] += call.get('usage') is None
        runs.append({'algorithm': job['algorithm'], 'status': reported_status, 'persisted_status': summary['status'],
            'scheduler': scheduled, 'error': summary.get('error'),
            'costs': costs,
            'attempted_rounds': [r['round'] for r in summary['rounds']],
            'completed_rounds': [r['round'] for r in summary['rounds'] if (r.get('evaluation') or {}).get('complete')],
            'search_pareto': summary['pareto_rounds'], 'post_status': post.get('status', 'not_finished'),
            'run': str(requested_run), 'evidence_run': str(run), 'output': job['output'], 'job_id': job['job_id']})
    followups = load_followups(experiment)
    for row in followups:
        plan = row['system_plan']
        designs.append({'algorithm': row['algorithm'], 'round': row['round'],
            'evidence_id': row['evidence_id'], 'top': plan['top'], 'language': plan['language'],
            'config': row['config'], 'modules': [{'name': m['name'], 'purpose': m.get('purpose'),
                'latency': (m.get('behavior') or {}).get('latency'),
                'linked_reference_ids': m.get('linked_reference_ids', [])} for m in plan['modules']]})
    data = {'followups': followups, 'updated_utc': datetime.now(timezone.utc).isoformat(), 'runs': runs, 'rounds': rows, 'designs': designs,
        'scope': 'Development continuations across different versions; NOT a uniform from-scratch success-rate experiment'}
    save(experiment/'RQ1_SUMMARY.json', data)
    lines = ['# RQ1：四种动态稀疏注意力机制的全栈适配实验', '',
        '> Can FAST generalize across diverse dynamic sparse-attention algorithms and automatically derive effective full-stack designs without algorithm-specific manual optimization?', '',
        f'更新时间：{data["updated_utc"]}。以下只使用已保存证据；运行/验收未结束的项目保持未完成。', '',
        '本报告汇总原实验、恢复和后续诊断辅助修复。原四算法各5候选、共20条记录保持不变；辅助修复单列为A1，不伪装成原实验R6或自主成功。这些结果不是同一框架版本从零运行的公平cohort。', '',
        '## 当前完成情况', '',
        '| 算法 | 搜索状态 | 尝试轮次 | 完成PPA轮次 | 独立合格轮次 |',
        '|---|---|---|---|---|']
    for r in runs:
        qualified = [x['round'] for x in rows if x['algorithm'] == r['algorithm'] and x['qualified']]
        lines.append(f'| {NAMES[r["algorithm"]]} | {r["status"]} | {r["attempted_rounds"]} | {r["completed_rounds"]} | {qualified} |')
    qualified_algorithms = {r['algorithm'] for r in rows if r['qualified']}
    lines += ['', f'原五候选轨迹中已有独立合格点的算法：**{len(qualified_algorithms)}/4**；计入单列后续修复后，工程上有合格设计的算法：**{len(qualified_algorithms | {r["algorithm"] for r in followups if r["qualified"]})}/4**。两者都不是统一随机实验的成功率。', '',
        '当前可以支持：FAST在给定算法语义、可信golden/testbench和只读参考库后，能够完成多种稀疏机制的模块实现/组装、数值验证、真实物理提取和Critic反馈。仍不能证明：任意新算法都能成功、优于人工专家，或在真实模型规模下取得加速。以下把可行性、优化收益与泛化证据分开报告。', '',
        '## 当前最佳已验收设计', '',
        '每算法选择独立合格点中能效最高的一点。R1–R5来自原轨迹；A1为外部诊断辅助修复，不能并入原轨迹的自主成功率或Critic收益。', '',
        '| 算法/轮次 | 软件配置 | 留出RMSE | 留出稀疏率 | 频率MHz | 单元面积µm² | 功耗mW | 延迟ns | 能量nJ/query | 能效Gqueries/J |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    selected = []
    for algorithm in NAMES:
        candidates = [r for r in rows + followups if r['algorithm'] == algorithm and r['qualified'] and r['energy_nj']]
        if not candidates:
            lines.append(f'| {NAMES[algorithm]} | 尚无本次独立合格点 | — | — | — | — | — | — | — | — |')
            continue
        best = min(candidates, key=lambda r: r['energy_nj']); selected.append(best)
        values = [f'{NAMES[algorithm]}/' + best.get('display_label', f'R{best["round"]}'), '`'+json.dumps(best['config'], sort_keys=True)+'`',
            number(best['heldout_rmse'], 100)+'%', number(best['heldout_sparsity'], 100)+'%',
            *[number(best[k]) for k in ('frequency_mhz','area_um2','power_mw','latency_ns','energy_nj')],
            number(best['energy_efficiency_queries_per_joule'], 1e-9)]
        lines.append('| '+' | '.join(values)+' |')
    lines += ['', '最终测试统一seed=2026091801、8192随机样本。RMSE由软件定点golden输出对浮点dense-softmax参考计算，包含稀疏化和定点近似误差，不是模型任务准确率。独立RTL检查另含重建及5×100次额外执行（边界向量可能重复），布线后网表再进行100次零延时功能检查；8192不表示8192次RTL仿真。', '',
        'PPA为Hammer/Yosys/OpenROAD布线后提取，Nangate45 TT；功耗使用统一activity=0.1，非芯片实测。能量定义为工具平均功耗×单query延迟；能效为其倒数。面积是单元面积，非die面积。', '',
        '## 软件配置与硬件方案', '']
    special_policies = [r for r in rows if r['setup_repair_policy'] not in (None, 'default')]
    if special_policies:
        lines += ['物理兼容性重试：' + '、'.join(f'{NAMES[r["algorithm"]]}/R{r["round"]}: `{r["setup_repair_policy"]}`' for r in special_policies)
            + '。该策略限制setup优化操作以绕过工具崩溃；完整布线、寄生提取、时序/DRC/面积/误差门槛保留。与默认策略的差异须单列，不能全归因于Agent设计改进。', '']
    for best in selected:
        design = next(d for d in designs if d['algorithm'] == best['algorithm'] and d['round'] == best['round'] and d.get('evidence_id') == best.get('evidence_id'))
        lines += [f'### {NAMES[best["algorithm"]]} / ' + best.get('display_label', f'R{best["round"]}'), '',
            f'顶层 `{design["top"]}`，语言 `{design["language"]}`，配置 `{json.dumps(design["config"], sort_keys=True)}`。', '',
            '| 模块 | 契约延迟/拍 | 原生链接库 | 职责 |', '|---|---:|---|---|']
        for m in design['modules']:
            lines.append('| '+' | '.join([m['name'], number(m['latency']), ', '.join(m['linked_reference_ids']) or '无',
                (m['purpose'] or '').replace('|','/').replace('\n',' ')])+' |')
        lines.append('')
    if followups:
        lines += ['## 后续诊断辅助修复（独立候选）', '',
            '| 算法/编号 | 独立验收 | Setup/ns | Hold/ns | DRC | 延迟ns | 能效Gqueries/J |',
            '|---|---|---:|---:|---:|---:|---:|']
        for r in followups:
            lines.append('| ' + ' | '.join([f'{NAMES[r["algorithm"]]}/{r["display_label"]}',
                '通过' if r['qualified'] else '未通过',
                *[number(r[k]) for k in ('slack_ns', 'hold_slack_ns', 'route_drc_violations', 'latency_ns')],
                number(r['energy_efficiency_queries_per_joule'], 1e-9)]) + ' |')
            lines += ['', f'详细证据：[修复报告]({r["report"]})。', '']
        lines += ['Block N:M：外部诊断将score→h_reg的15级串行比较定位为瓶颈；FAST组装UArch一次生成4层平衡树。n=7、系统计划、FindMin8和DividerWrapper、70拍调度均不变。setup从−1.85258663 ns变为+0.43733039 ns，hold转正且DRC=0；独立RTL和布线后网表验证通过。Critic随后收到新源码与测量并选择停止。', '',
            '这是错误归因纠正后的工程修复证据，不证明原Critic自主发现了正确修复。原R5时序失败，不能以其名义能效计算有效性能加速比。', '']
    lines += ['## 原五候选轨迹：全部外层轮次', '',
        '| 算法/轮次 | 状态 | 搜索可行 | 独立验收 | 延迟ns | 能量nJ | 能效Gqueries/J | Critic层 | 回退至 |',
        '|---|---|---|---|---:|---:|---:|---|---|']
    for r in rows:
        qualification_label = {'passed': '通过', 'failed': '未通过', 'pending': '待完成', 'not_selected': '未选入验收'}
        lines.append('| '+' | '.join([f'{NAMES[r["algorithm"]]}/R{r["round"]}', r['status'], str(r['feasible']), qualification_label[r['qualification_status']],
            number(r['latency_ns']), number(r['energy_nj']), number(r['energy_efficiency_queries_per_joule'], 1e-9),
            str(r['critic_layer'] or '—'), str(r['rollback_to_round'] or '—')])+' |')
    lines += ['', '独立验收只覆盖搜索Pareto及按哈希确认未改变的已验收基线；待完成和未选入验收都不等于功能失败。', '',
        '### 未通过约束的完整物理测量', '',
        '以下点保留用于诊断，不进入有效Pareto；负slack下按目标频率计算的延迟/能效不能作为可运行性能。', '',
        '| 算法/轮次 | 单元面积µm² | 模型功耗mW | Setup slack/ns | Hold slack/ns | DRC数 |',
        '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        if r['complete'] and not r['feasible']:
            lines.append('| '+' | '.join([f'{NAMES[r["algorithm"]]}/R{r["round"]}',
                *[number(r[k]) for k in ('area_um2','power_mw','slack_ns','hold_slack_ns','route_drc_violations')]])+' |')
    lines += ['',
        '## Agent执行开销', '',
        '| 算法 | 累计调用 | 累计已记录tokens | 本次恢复新增调用 | 新增已记录tokens | 新增缺usage调用 |',
        '|---|---:|---:|---:|---:|---:|']
    for r in runs:
        c = r['costs']
        lines.append('| '+' | '.join([NAMES[r['algorithm']], *[str(c[k]) for k in
            ('calls','tokens','new_calls','new_tokens','new_calls_missing_usage')]])+' |')
    for r in followups:
        calls = sum(r['agent_calls'].values())
        tokens = (r.get('token_totals') or {}).get('total_token_count', 0)
        lines.append(f'| {NAMES[r["algorithm"]]}/{r["display_label"]}（辅助，单列） | {calls} | {tokens} | {calls} | {tokens} | {r.get("calls_missing_usage")} |')
    lines += ['', 'tokens按服务返回的total_token_count求和；缺失usage的调用不估算。Top-K本次只做工具补验，新增Agent调用为0。', '',
        '## 原五候选轨迹的Critic效果与可支持的结论', '']
    for algorithm in NAMES:
        measured = [r for r in rows if r['algorithm'] == algorithm and r['complete'] and r['feasible'] and r['energy_nj']]
        if not measured:
            lines.append(f'- {NAMES[algorithm]}：原五候选没有可行PPA；后续A1单列，不能计算原轨迹内的有效改善。'); continue
        first = min(measured, key=lambda r: r['round']); best = min(measured, key=lambda r: r['energy_nj'])
        latency = min(measured, key=lambda r: r['latency_ns'])
        lines.append(f'- {NAMES[algorithm]}：首个物理可行点R{first["round"]}；最高能效R{best["round"]}，'
            f'相对该起点{first["energy_nj"]/best["energy_nj"]:.3f}×；最低延迟R{latency["round"]}，'
            f'相对该起点加速{first["latency_ns"]/latency["latency_ns"]:.3f}×。独立验收状态另见表。')
        if first['setup_repair_policy'] != best['setup_repair_policy']:
            lines.append('  该算法起点和最佳点的物理修复策略不同，上述比值不是同条件的Critic改善证据。')
    lines += ['', '这些是单次流程轨迹，不是Critic因果消融；改善可能来自Kernel参数、Compiler规划或UArch实现。没有等预算Critic OFF、固定模板/仅参数搜索及人工优化对照，不能声称取代专家优化。', '',
        '已核对的跨层变更见 `cross_layer_trace.json`：N:M R1→R2复用相同hash的FindMin8/DividerWrapper，将顶层同拍最大值/掩码/指数逻辑拆为两个状态；Sanger R4→R5保持threshold=1，将Softmax契约3→7拍、选择累加2→5拍并重新实现；DynaX R1→R5同时改变稀疏配置和Selection模块，因此不能把收益只归于某一个层。每个修改是否有效仍以对应PPA和独立验证为准。', '',
        '## 修复与证据边界', '',
        '- 已加入阶段保存、独立目录恢复、源文件/库hash核对、失败回退和PPA失败反馈。没有summary.json也可验收逐轮记录。',
        '- Sanger R5的ODB-0445属于工具崩溃。CTS检查点重载探针保留默认全部优化动作后可继续；后端已加入精确错误匹配的一次自动恢复，恢复原IO约束及placement padding，保存原失败和重试日志。是否最终合格仍按布线后结果判断。限制clone/buffer的早期兼容试跑已取消并保留记录，不计新候选。',
        '- Sanger原失败与默认策略重测的CTS前检查点逐字节hash相同；见`sanger_cts_checkpoint_comparison.json`。实际恢复Tcl的约束与完整物理步骤审计见`sanger_checkpoint_constraint_audit.json`。',
        '- Sanger旧ExpStage误诊已经用到期交易的捕获时刻与数学计算复核：golden与契约一致；原始Agent把当前输入误当作流水线输出对应输入。诊断修复不改变测试答案。',
        '- 原Sanger R3的ExpStage还存在具体LUT错误：声明256项但实际240项，索引188的数值也与契约不符；饱和索引255落入默认65535而不是0。详见sanger_lut_diagnosis.json。该只读诊断没有修改原RTL。',
        '- 原Block N:M部分物理日志显示布线前setup slack约−3.142 ns，关键路径涉及score最大值/减法/指数查表。同拍组合逻辑过长的推断见block_nm_ppa_diagnosis.json，最终可行性仍以布线后测量为准。',
        '- 补测的N:M R1与Sanger R4均完成物理流程但违反约束。只读重载布线数据库/SPEF精确重现slack −3.10006952 ns与−2.59888577 ns：N:M路径到exp寄存器，Sanger路径经过组合score及Softmax最大值/差值。证据在`ppa_diagnostics/`；这些外部复核未向运行中的Agent注入答案。',
        '- N:M R2的布线后复核重现slack −1.81639135 ns，最差路径为score寄存器→最大值h_reg。把最大值与指数逻辑拆开已有改善，但若后续只分离并行的mask支路，并不会自动缩短最大值归约本身；需要用真实路径验证后续修复效果。证据见`ppa_diagnostics/block_nm_r2/`。',
        '- N:M R3只改善至−1.80368257 ns，Critic随后猜测乘加器瓶颈。R4的86拍RTL已通过E2E后，受控停止旧作业并切换通用STA反馈版本v4：同一R4重新测量，把工具报告的关键路径和端点网名交给Critic，再用剩余R5预算迭代。没有人工改生成RTL，但有框架开发干预；不能算未干预的原版本Critic成功。',
        '- R4新测量为slack −1.67740512 ns、DRC=1。Critic确实引用了新增路径数据，却把FindMin前缀当成了掩码阶段回传。实际展开RTL中，该网只是score寄存器拼接；h_reg来自串行最大值归约。详见`block_nm_r4_critic_attribution_audit.json`。',
        '- N:M最终R5通过100/100 E2E，完成布线后DRC=0，但setup slack为−1.85258663 ns、hold slack为−0.00002837 ns，仍不可行。五轮预算已用完，未追加第六候选。末轮Critic仍重复网名误归因；其建议没有执行，也不算优化成果。',
        '- 请求审计进一步发现，v4及更早的Critic只拿到实现说明/源码hash，没有已验收的实际代码。后续v5为`accepted_sources`提供经hash核对的当前源码，并提醒综合网名可能是别名。原v4五候选实验未使用此修复；N:M辅助修复后的末轮Critic使用了新上下文，但正确设计建议来自外部诊断，不能归因于v5自主诊断成功。见`critic_input_observability_audit.json`及`critic_source_context_tests.xml`。',
        '- Critic仍有决策质量问题：DynaX R5的末轮建议试图在UArch层缩短固定契约延迟，应进入Compiler重新规划；该建议因预算结束未执行。Sanger的部分建议持续降低误差，但误差≤5%是约束，不能用更低误差代替延迟–能效收益。',
        '- Sanger恢复后的R5完整PPA已修复setup/hold时序，但最终还有via1 Cut Spacing与metal1 Metal Spacing两项DRC，因此排除出有效前沿。末轮Critic把R1称为唯一可行设计并不精确：R2也物理可行，只是被R1支配。详见`sanger_r5_final_ppa_diagnosis.json`。',
        '- 原始任务保留；恢复源目录与预算变更见PROTOCOL.md及recovery_origin.json。旧测量标记为继承证据，新PPA不能伪装成原作业正常完成。',
        '- 四机制规模统一为16 keys、head_dim=2、value_dim=1。Sanger是概率阈值契约，不是完整论文架构；Block N:M的动态选择索引不等于动态保留数量。',
        '- 无需人工修改生成RTL的证据，应连同库组件来源、链接/生成模块和开发期间的框架修正一起披露；不同版本累计成功不能称为无干预的一次性泛化。', '',
        'Top-K轨迹也说明稀疏率不能代替PPA：k由14变15，删除的key更少，但最终设计能效更高。参数改变与重新生成的选择逻辑/调度同时发生，具体贡献仍需固定架构对照隔离。', '',
        '## 优先改进项', '',
        '1. 将Critic的契约修改请求结构化：延迟、吞吐率或接口改变必须由Compiler重新下发契约；不能只依靠自然语言提醒。',
        '2. 通用后端已在v4加入真实关键路径及端点网名反馈；后续增加可靠的源代码映射和DRC类型归因，并验证诊断是否减少无效修改。布线前诊断可用于搜索，最终合格点仍完成布线、寄生提取和独立验证。',
        '3. 对有限查表域补充边界及饱和索引测试；流水线失败诊断始终对齐实际捕获的交易，避免以修改golden掩盖RTL错误。',
        '4. 将精度作为可行性约束，保留所有延迟–能效非支配点；只有同负载、同技术与功耗口径的测量才能用于改善判断。', '',
        '5. 库源码只读不等于架构选择不可替换。DynaX已验收R5的归一化模块契约为41拍，选择模块为7拍；下一阶段应让Compiler评估替换归一化实现的方案并重新验证，不能只在较小的选择模块内反复压缩一拍。', '',
        '6. 用同一真实工作负载的VCD/SAIF活动补充功耗分析。当前统一activity=0.1提供一致的物理建模口径，但没有测量不同稀疏模式的实际切换活动；不能据此推断数据相关门控的真实节能幅度。', '',
        '## 后续正式RQ1实验', '',
        '冻结同一框架、同一只读库和预算，四算法各至少3次Agent运行、每次最多5候选；最终留出集不反馈搜索。增加固定模板/仅参数搜索和同条件dense基线，另做等预算Critic ON/OFF。报告最终合格率、首次可行耗时、token成本、每算法latency–energy-efficiency Pareto，并增加较大规模或真实模型Q/K/V验证。', '',
        'Critic OFF对照应让Compiler仍可看到相同的真实测量，并控制总调用/token预算；否则同时去掉反馈信息，无法单独判断Critic角色的价值。', '',
        '建议再做一次“留出目标算法专属模板”的迁移测试：只保留通用算术、排序、归约、缓冲和接口参考，检验Agent是否仍能适配目标机制。当前DynaX直接链接已验证的专属Score/Exp与Normalization组件，因此“运行期间未手改RTL”和“从未依赖算法专属人工优化知识”是不同命题。算法契约/golden属于正确性规格，专属优化模板属于先验，两者应分别披露。', '',
        '证据入口：[补完协议](PROTOCOL.md)、[调度任务](all_jobs.json)、[冻结源码](source_freeze.json)、[逐轮结构化汇总](RQ1_SUMMARY.json)、[Sanger失败复核](sanger_failure_witness.json)。', '']
    (experiment/'RQ1_SUMMARY.md').write_text('\n'.join(lines))
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', type=Path, required=True)
    args = parser.parse_args()
    result = build_report(args.experiment.resolve())
    print(json.dumps({'runs': len(result['runs']), 'rounds': len(result['rounds'])}))
