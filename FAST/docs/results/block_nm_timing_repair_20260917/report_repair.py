"""Build an evidence-only follow-up report without changing original RQ1 results."""
import difflib
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
paths = json.loads((root/'paths.json').read_text())
protocol = json.loads((root/'PROTOCOL.json').read_text())
run = Path(paths['run'])
old = Path(protocol['original_run'])
baseline = json.loads((root/'baseline_r5.json').read_text())
summary = json.loads((run/'summary.json').read_text())
record = summary['rounds'][-1]
post = json.loads((Path(paths['output'])/'results.json').read_text())
validation = next(r for r in post['rounds'] if r['round'] == record['round'])
measurement = record.get('evaluation') or {}
archive = json.loads((Path(paths['output'])/'archive_verification.json').read_text())
qualified = validation.get('independently_qualified') is True and archive['passed']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

sources = {Path(p).stem: run/p for p in record.get('sources', {})}
old_sources = {Path(p).stem: old/p for p in baseline['sources']}
children = [n for n in old_sources if n != 'Rq1BlockNmTop']
checks = {
    'original_record_unchanged': sha(old/'round_05/result.json') == protocol['original_record_sha256'],
    'original_top_unchanged': sha(old_sources['Rq1BlockNmTop']) == protocol['original_top_sha256'],
    'accepted_children_unchanged': all(sha(sources[n]) == sha(old_sources[n]) for n in children),
    'config_unchanged': record['config'] == baseline['config'],
    'plan_unchanged': record['system_plan'] == baseline['system_plan'],
    'archive_verified': archive['passed'],
    'independently_qualified': qualified,
    'critic_called_with_measured_result': bool(record.get('critique')),
}
if 'Rq1BlockNmTop' in sources:
    diff = ''.join(difflib.unified_diff(old_sources['Rq1BlockNmTop'].read_text().splitlines(True),
        sources['Rq1BlockNmTop'].read_text().splitlines(True), fromfile='original_R5.scala', tofile='assisted_repair.scala'))
    (root/'top_change.diff').write_text(diff)
metrics = ['frequency_mhz','area_um2','power_mw','latency_ns','energy_nj',
           'energy_efficiency_queries_per_joule','slack_ns','hold_slack_ns','route_drc_violations']
data = {'scope': protocol['scope'], 'run': str(run), 'status': summary['status'],
    'qualified': qualified, 'checks': checks, 'before': {k: baseline['evaluation'].get(k) for k in metrics},
    'after': {k: measurement.get(k) for k in metrics}, 'heldout': validation.get('heldout'),
    'independent_checks': validation.get('independent_checks'), 'critic': record.get('critique'),
    'token_totals': post.get('token_totals'), 'source_hashes': record.get('sources')}
(root/'RESULTS.json').write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
lines = ['# Block N:M 时序修复：独立后续实验', '',
    '**验收结果：'+('通过' if qualified else '未通过')+'。** 状态：`'+summary['status']+'`。', '',
    '本次从原RQ1第五候选出发，由外部诊断指出串行最大值归约，FAST组装UArch生成修复代码。原五轮失败记录未改变；本结果不计为原始自主RQ1成功或第六轮。', '',
    '## 修改与约束', '',
    '原始score→h_reg路径包含15级串行比较；修复目标是显式4层平衡最大值树。实现差异见[top_change.diff](top_change.diff)，实际源码和调用记录保存在验证归档内。', '',
    '固定Block N:M配置n=7、M=8；16 keys、head_dim=2、value_dim=1。目标300 MHz、相对输出RMSE≤5%、单元面积≤200000 µm²。现有golden、子模块及数值规则不变。', '',
    '## 完整物理测量', '', '| 指标 | 原R5（时序失败） | 本次修复 |', '|---|---:|---:|']
for k in metrics:
    lines.append(f'| {k} | {data["before"][k]} | {data["after"][k]} |')
lines += ['', '原R5的目标频率延迟/能效是名义数值，不能作为有效性能基线。新结果只有在完整setup/hold/DRC与独立检查均通过后才算合格。', '',
    'PPA使用Hammer/Yosys/OpenROAD、Nangate45 TT、详细布线与寄生提取；功耗是activity=0.1的工具建模，非芯片实测。面积为单元面积。', '',
    '## 数值与独立验证', '',
    '最终软件留出集8192样本、seed=2026091801，与原四算法一致；软件定点输出对dense浮点参考的相对RMSE为 '+str((validation.get('heldout') or {}).get('quality_loss'))+'。该误差包含稀疏化和定点近似，不是模型任务准确率。', '',
    'RTL与布线后网表检查状态：`'+json.dumps({k:v['passed'] for k,v in (validation.get('independent_checks') or {}).items()})+'`。详细日志与归档见[validation/](validation/)。', '',
    '## Critic与证据完整性', '',
    'Critic在物理测量保存后分析当前源码及实际路径；建议仅作末尾分析，本次未额外执行其建议。', '',
    '```json', json.dumps({'checks':checks,'critic':record.get('critique')},indent=2,ensure_ascii=False),'```', '',
    '下一步用冻结后的统一FAST版本从头运行，才能评估自动归因是否稳定复现该修复。当前结果应作为带诊断指导的工程修复单独报告。', '']
(root/'RESULTS.md').write_text('\n'.join(lines))
print(json.dumps({'qualified':qualified,'checks':checks}))
