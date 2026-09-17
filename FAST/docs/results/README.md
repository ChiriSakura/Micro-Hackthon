# 实验结果索引

## 当前汇报入口

| 入口 | 内容与证据范围 |
|---|---|
| [RQ1四算法总报告](rq1_completion_20260917/RQ1_SUMMARY.md) | 原20候选＋N:M辅助修复A1；完整配置、硬件、精度、PPA和Critic分析 |
| [四个最终合格设计的代码](rq1_completion_20260917/designs/README.md) | 生成源码、展开RTL、实际链接库、系统计划及逐文件SHA256 |
| [逐候选数据](rq1_completion_20260917/metrics.csv) | 21条记录，evidence_class区分原轨迹和辅助修复 |
| [延迟–能效图](rq1_completion_20260917/latency_energy_efficiency.pdf) | A1用独立菱形标记，不并入原轨迹前沿 |
| [Block N:M时序修复](block_nm_timing_repair_20260917/RESULTS.md) | 300 MHz、setup/hold通过、DRC=0；外部诊断后由FAST生成修复 |

原五轮开发轨迹中3/4算法有合格点，加入单列辅助修复后四种算法均有合格设计。它们不是统一从零的4/4自主泛化成功率，也不是严格Critic因果消融。统一负载为16 keys、head_dim=2、value_dim=1；最终8192样本为软件输出RMSE检查；功耗为布线后工具建模。

## 历史与辅助证据

| 结果 | 用途与限制 |
|---|---|
| [DynaX自主两轮](dynax_autonomous_20260913/RESULTS.md) | 早期8-key/100 MHz自主闭环；不能与当前16-key/300 MHz数字直接混用 |
| [DynaX恢复两轮](dynax_fast_recovery_20260913/RESULTS.md) | 恢复机制辅助证据；首轮外部选取旧模块 |
| [历史Critic消融](critic_ablation_20260911/RESULTS.md) | 24×5-loop参数修正，历史路径B；不能替代当前硬件生成的消融 |
| [RQ1扩展库](rq1_extended_20260916/RESULTS.md) | N:M/Sanger上游参考、通用诊断与失败轨迹 |
| [DynaX工程恢复](dynax_recovery_20260916/RESULTS.md) | 额外选参、已验证组件和失败回退 |
| `fullstack_extensions_20260913/` | threshold-attention的Hammer、生成对照与辅助修复 |
| `fullstack_e2e_20260913/`、`parallel_uarch_20260913/` | 模块/组装bring-up和并发机制验证 |
| `fullstack_generation_20260913/` | 初期Chisel/Verilog生成，算法与后端口径不同 |
| `critic_integration_20260911/`、`critic_audit_20260911/` | 历史Critic接入和作用审计 |
| `dynax_rediscovery_20260910/`、`final_experiment_20260911/` | 算法搜索和组件验证，部分功耗口径已被修正 |

每份`artifacts.tar.gz`及对应`archive_verification.json`保存可复验的完整运行证据；日志、失败尝试、冻结库和生成源码均保留。可重建缓存按[清理记录](../maintenance/20260917/README.md)处理。汇总前报告与旧生成器保存在[历史归档](../history/rq1_consolidation_20260917/README.md)。
