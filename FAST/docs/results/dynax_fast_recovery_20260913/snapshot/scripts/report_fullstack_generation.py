#!/usr/bin/env python3
"""Archive finished generation runs and report measured whole-system results.

This reports integration/bring-up evidence, not a Critic ablation or an HDL
benchmark. Raw LLM replies, rejected builds, source, RTL and PPA logs are retained.
Compiled simulator and Scala build caches are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def number(value):
    return '—' if value is None else f'{value:.6g}'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, action='append', required=True)
    parser.add_argument('--source', type=Path, required=True, help='Frozen source snapshot used by the runs')
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(argv)
    summaries=[]
    for run in args.run:
        summaries.append((run, json.loads((run/'summary.json').read_text())))
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(args.source,args.output/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    lines=['# 完整系统生成：Chisel / Verilog 集成验证', '',
           '这是新主线的 bring-up 记录，不是 Critic 消融，也不是两种 HDL 的公平性能比较。', '',
           '算法为 4-bit threshold-attention：QK 阈值筛选、加权求和、整数归一化。'
           '它不等于 DynaX 或 softmax attention。每轮使用独立 Python 参考驱动的 100 个全系统数值用例。', '',
           '面积为完整生成顶层的 Nangate45 综合单元面积；功耗为 OpenSTA 全局活动率预布局估计，'
           '能量为该估计功耗乘以实测周期对应的延迟。没有布局布线或逐网工作负载活动标注。', '',
           '| 运行 | 轮次 | 语言 | threshold | 验证 | 面积 µm² | 功耗 mW | 延迟 ns | 能量 nJ | slack ns | 可行 |',
           '|---|---:|---|---:|---|---:|---:|---:|---:|---:|---|']
    for run,summary in summaries:
        shutil.copytree(run,args.output/'raw'/run.name,ignore=shutil.ignore_patterns(
            'obj_dir','scala_build','.scala-build','.bsp','__pycache__','*.pyc','core','core.*'))
        for record in summary['rounds']:
            e=record.get('evaluation',{})
            values=[run.name,str(record['round']),record.get('system_plan',{}).get('language','—'),
                    str(record.get('config',{}).get('threshold','—')),
                    '通过' if e.get('verification',{}).get('passed') else record['status'],
                    *[number(e.get(k)) for k in ('area_um2','power_mw','latency_ns','energy_nj','slack_ns')],
                    '是' if e.get('feasible') else '否']
            lines.append('| '+' | '.join(values)+' |')
    for run,summary in summaries:
        task=json.loads((run/'task.json').read_text())
        lines += ['',f'## {run.name}', '',
                  f'状态：`{summary["status"]}`；参考库完整性：`{summary["reference_integrity"]}`；'
                  f'保留的 Pareto 轮次：`{summary["pareto_rounds"]}`。', '',
                  f'约束与预算：`{json.dumps(task,ensure_ascii=False)}`', '',
                  f'LLM 调用次数：`{json.dumps(summary["agent_calls"],ensure_ascii=False)}`。', '']
        for record in summary['rounds']:
            lines += [f'### 轮次 {record["round"]}', '',
                      f'重入：`{record["reentry"]}`；状态：`{record["status"]}`。', '']
            if record.get('profile'):
                lines += [f'可信 Kernel 分析：`{json.dumps(record["profile"],ensure_ascii=False)}`。', '']
            if record.get('system_plan'):
                plan=record['system_plan']
                lines += [f'完整顶层：`{plan["top"]}`。下述为 Compiler 的接口/拓扑计划。UArch 重入会保留该计划，因此其中流水级等实现说明可能仍是初始值；最终实现以该轮源码、UArch 说明和实测周期为准：', '', plan['rationale'], '',
                          '| 新生成模块 | 依赖 | Compiler 分配的参考 | 职责 |', '|---|---|---|---|']
                for module in plan['modules']:
                    references=', '.join(module.get('reference_ids', [])) or '—'
                    lines.append('| '+module['name']+' | '+', '.join(module['dependencies'])+' | '+references+' | '+module['purpose'].replace('|','/')+' |')
                lines += ['']
            if record.get('critique'):
                c=record['critique']
                lines += [f'Critic → `{c["layer"]}`；有下一轮执行：`{record["critique_applied"]}`。', '',
                          '归因（模型分析，因果结论仍需对照）：'+c['reason'], '',
                          '具体干预：'+c['instructions'], '', f'引用字段：`{c["evidence"]}`。','']
        if summary.get('error'):
            lines += ['失败原因：`'+summary['error']+'`。','']
        lines += [f'[完整结果](raw/{run.name}/summary.json) · [事件与反馈](raw/{run.name}/events.json)', '']
    lines += ['## 证据使用边界', '',
              '本记录证明的是指定契约下的系统生成、验证、测量和角色重入。'
              '单次变好或变差都不足以证明 Critic 相比无 Critic / 规则 Critic 更有效。'
              '下一步应冻结工作负载、初始设计和预算，做多 seed 的有/无 Critic 对照，并增加真实 DynaX 契约和工作负载活动标注。', '',
              'raw 保留原日志中的绝对路径；它们对应运行时的 scratch 目录。归档的相对目录保持原层次。'
              'source 是执行时的冻结源码快照；当前工作区可能有后续兼容性修复，不能反向归算为本次运行的行为。', '']
    (args.output/'RESULTS.md').write_text('\n'.join(lines))
    manifest={str(path.relative_to(args.output)):hashlib.sha256(path.read_bytes()).hexdigest()
              for path in args.output.rglob('*') if path.is_file()}
    (args.output/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(args.output/'RESULTS.md')


if __name__=='__main__':
    main()
