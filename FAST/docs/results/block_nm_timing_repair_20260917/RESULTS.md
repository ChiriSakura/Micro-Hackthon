# Block N:M 时序修复：独立后续实验

**验收结果：通过。** 状态：`assisted_repair_complete`。

本次从原RQ1第五候选出发，由外部诊断指出串行最大值归约，FAST组装UArch生成修复代码。原五轮失败记录未改变；本结果不计为原始自主RQ1成功或第六轮。

## 修改与约束

原始score→h_reg路径包含15级串行比较；修复目标是显式4层平衡最大值树。实现差异见[top_change.diff](top_change.diff)，实际源码和调用记录保存在验证归档内。

固定Block N:M配置n=7、M=8；16 keys、head_dim=2、value_dim=1。目标300 MHz、相对输出RMSE≤5%、单元面积≤200000 µm²。现有golden、子模块及数值规则不变。

## 完整物理测量

| 指标 | 原R5（时序失败） | 本次修复 |
|---|---:|---:|
| frequency_mhz | 300 | 300 |
| area_um2 | 42292.93599999565 | 41780.88599999517 |
| power_mw | 13.7061542 | 13.4159094 |
| latency_ns | 233.33333333333334 | 233.33333333333334 |
| energy_nj | 3.198102646666667 | 3.13037886 |
| energy_efficiency_queries_per_joule | 312685398.3383818 | 319450151.15518636 |
| slack_ns | -1.85258663 | 0.43733039 |
| hold_slack_ns | -2.837e-05 | 0.00664113 |
| route_drc_violations | 0 | 0 |

原R5的目标频率延迟/能效是名义数值，不能作为有效性能基线。新结果只有在完整setup/hold/DRC与独立检查均通过后才算合格。

PPA使用Hammer/Yosys/OpenROAD、Nangate45 TT、详细布线与寄生提取；功耗是activity=0.1的工具建模，非芯片实测。面积为单元面积。

## 数值与独立验证

最终软件留出集8192样本、seed=2026091801，与原四算法一致；软件定点输出对dense浮点参考的相对RMSE为 0.033320809848209114。该误差包含稀疏化和定点近似，不是模型任务准确率。

RTL与布线后网表检查状态：`{"gates": true, "rtl_holdout": true}`。详细日志与归档见[validation/](validation/)。

## Critic与证据完整性

Critic在物理测量保存后分析当前源码及实际路径；建议仅作末尾分析，本次未额外执行其建议。

```json
{
  "checks": {
    "original_record_unchanged": true,
    "original_top_unchanged": true,
    "accepted_children_unchanged": true,
    "config_unchanged": true,
    "plan_unchanged": true,
    "archive_verified": true,
    "independently_qualified": true,
    "critic_called_with_measured_result": true
  },
  "critic": {
    "layer": "stop",
    "reason": "The assisted repair was successful. The design meets all constraints, including timing (slack +0.437 ns), area (41.8k um^2 < 200k um^2), and quality (0.0336 < 0.05). The critical path violation from the previous design, caused by a serial reduction chain, was resolved by implementing a balanced comparator tree for the max-score calculation. Since a feasible point has been established and the experiment's loop budget (max_loops=1) is exhausted, the process concludes.",
    "evidence": [
      "evaluation.feasible",
      "evaluation.slack_ns",
      "evaluation.area_um2",
      "evaluation.quality_loss"
    ],
    "instructions": "Stop. A feasible design point that meets all constraints has been successfully generated and measured. The timing violation has been fixed. No further action is required for this task."
  }
}
```

下一步用冻结后的统一FAST版本从头运行，才能评估自动归因是否稳定复现该修复。当前结果应作为带诊断指导的工程修复单独报告。
