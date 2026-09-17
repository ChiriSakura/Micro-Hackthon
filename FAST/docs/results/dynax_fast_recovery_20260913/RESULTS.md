# DynaX 恢复运行：两轮 E2E、Hammer 与 Critic

两轮均已完成 E2E 和 Hammer PPA，结束状态为 `budget_exhausted`，非支配轮次 `[2]`。这是辅助恢复证据；主结论使用 [从零自主运行](../dynax_autonomous_20260913/RESULTS.md)。

## 来源与实验边界

首轮采用外部选择的已有 Agent 模块组合，源码逐字保持不变，经重新编译和全部检查后进入标准 `FullStackFlow.run()` 的 PPA/Critic 环节。它不属于一次无干预的从零生成；[来源和哈希](run/recovery_provenance.json) 保留了选择过程。原来源 v7 已移入 [开发归档](../../history/dynax_development_20260913.tar.gz)。

软件配置 `t0_quarters=5, t1_quarters=1`，8 keys、Q/K dim=2、V dim=1；质量损失 0.105703591 < 0.15，来自 260 个合成查询的归一化 MAE。此配置与主自主运行不同，二者不构成公平对照。

## 两轮结果

| 指标 | 首轮恢复 | Critic 后第二轮 |
|---|---:|---:|
| 延迟 ns / 周期 | 270 / 27 | 180 / 18 |
| 标准单元面积 µm² | 46,633.258 | 44,256.016 |
| 建模功耗 mW | 5.39067667 | 4.93521709 |
| 能量 nJ/query | 1.4554827009 | 0.8883390762 |
| 能效 Gqueries/J | 0.687057290 | 1.125696287 |
| Setup / hold slack ns | 5.18562031 / 0.00784237 | 6.70438862 / 0.00819567 |
| Route DRC | 0 | 0 |
| 主流程独立 E2E | 100/100 | 100/100 |

完整顶层 Hammer/Yosys/OpenROAD、Nangate45 TT 1.1 V 25°C、100 MHz、activity=0.1，功率为布线后模型值。固定 die/core 为 435,600/395,923.71 µm²。功耗方法及能效定义与主报告一致；不是芯片实测。

首轮还通过 [100 次布线网表检查](gate_round_01/summary.json) 和 [600 次源码重建/额外种子检查](holdout_round_01/summary.json)。**第二轮有主流程 E2E/PPA，没有额外独立 gate/holdout 记录**；不把主自主运行的复验算到这里。

## Critic 的执行

第一次 Critic 请求 Compiler 将原生除法器从 16 调至 8 级，并修订顶层控制。该建议已执行，第二轮实测 18 拍；预测的约 19 拍与结果分开记录。第二次建议进一步改为 4 级，但两轮预算耗尽，`critique_applied=false`；没有第三轮测量。

最终结构为 ScoreWeightGen → SelectAccumulate → DividerWrapper → DynaX_XM_Row 控制。第二轮的接口、实现和源码哈希见 [result.json](run/round_02/result.json)。调用记录为 Kernel 0、Compiler 6、模块 UArch 7、组装 UArch 2、CompilerDiagnosis 3、Critic 2；首轮复用配置，不存在新 Kernel 调用。

## 保存

[机器指标](metrics.json) · [逐轮 CSV](metrics.csv) · [完整运行摘要](run/summary.json) · [冻结源码](snapshot/) · [完整归档](artifacts.tar.gz) · [逐文件校验](archive_verification.json)

归档保留 780 个文件，含恢复驱动、来源证明、失败尝试、两轮物理产物和首轮复验。SHA-256：`3bc2a0e13a96633de1755b00101a36afb87a4571e0bb8bc0677272cc8a4ce703`。阅读副本不依赖 scratch 软链接；完整物理产物在压缩包中。
