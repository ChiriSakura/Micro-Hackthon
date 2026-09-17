# RQ1 补完实验阅读入口

先读 [RQ1_SUMMARY.md](RQ1_SUMMARY.md)。现已汇总原20候选和后续N:M辅助修复A1：原轨迹3/4算法有合格点，加入A1后四种算法均有合格设计。辅助修复不算原始自主成功。

| 文件 | 内容 |
|---|---|
| [RQ1_SUMMARY.md](RQ1_SUMMARY.md) / [JSON](RQ1_SUMMARY.json) | 主结论、最佳已验收软硬件方案、全部轮次、Critic分析和下一步 |
| [metrics.csv](metrics.csv) / [metrics.json](metrics.json) | CSV含21候选并标明evidence_class；JSON将原20轮与followups分开 |
| [最终设计代码](designs/README.md) | 四个已验收设计的源码、展开RTL、链接库和哈希 |
| [followups.json](followups.json) | A1证据文件与哈希；不会覆盖原N:M R1–R5 |
| [DESIGNS.md](DESIGNS.md) | 各轮模块计划、只读库链接、原始Critic建议 |
| [Pareto图](latency_energy_efficiency.png) | latency–energy efficiency；菱形A1表示辅助修复，同名SVG/PDF可用于排版 |
| [PROTOCOL.md](PROTOCOL.md) | 科学约束、恢复规则、存储故障和框架版本变化 |
| [jobs.json](jobs.json) | 四算法当前主记录、scratch工作目录和发布目录 |
| [development_checks.json](development_checks.json) | 框架回归检查；不等于硬件正确性证据 |
| [cross_layer_trace.json](cross_layer_trace.json) | 已接受源码hash及跨层模块/调度变化 |
| `ppa_diagnostics/` | 只读STA复核；与Agent实际收到的证据分别记录 |

## 已保存的独立验收

- `rq1_dynax_xm/`：DynaX本次最终验收；`dynax_baseline/`保留原成功设计的补验。
- `topk_common_test/`：Top-K统一留出集和RTL/网表检查。
- `rq1_sanger_threshold/`：Sanger原R1成功设计验收。
- `rq1_sanger_threshold_checkpoint_retry/`：Sanger五轮恢复结果已发布；最终合格仍为R1，R5时序通过但DRC=2。
- `rq1_block_nm_sta_retry/`：N:M原五轮失败证据；最终R5 DRC=0但时序失败。
- [N:M辅助修复验收](../block_nm_timing_repair_20260917/validation/)：A1通过300 MHz setup/hold、DRC=0及独立验证，单列保留。

各验收目录的`results.json`给出实际检查结果，`artifacts.tar.gz`及`archive_verification.json`保存完整运行与逐文件hash。构建缓存可重建，未纳入发布副本。所有本次候选和独立收尾均已完成；失败候选的功能/PPA证据也保留。

## 版本与异常记录

- `source_freeze.json`：初始补完版本v1。
- `source_freeze_policy_v2.json`：限制clone/buffer的兼容试跑；已取消，原记录保留，不作为最终设计。
- `source_freeze_checkpoint_v3.json`：Sanger保留默认优化动作的CTS检查点恢复。
- `source_freeze_sta_v4.json`：N:M自动STA路径反馈、同R4恢复后继续R5。
- `source_freeze_context_v5.json`：后续Critic实际源码上下文修复，未用于原五候选；已用于A1修复后的Critic分析，不证明自主定位成功。
- 各`source_*.tar.gz`及对应验证JSON保存冻结源码；原始算法库和生成RTL不手改。
- `cache_cleanup.json`、`dynax_post_quota_recovery.json`：home配额故障和仅清理可重建缓存的记录。
- `sanger_checkpoint_recovery.json`、`sanger_checkpoint_constraint_audit.json`：真实工具恢复和约束审计。
- `block_nm_sta_recovery.json`：N:M阶段保存后切换通用诊断后端的记录。

这些版本构成开发恢复证据，不是统一版本的从零泛化率或Critic因果消融。

最终核验：`origin_preservation_audit.json`、`common_workload_audit.json`、`cross_layer_trace.json`、`block_nm_publication_verification.json`。N:M主作业退出码1表示五轮预算耗尽且无可行点；收尾与归档已完成，afterany守护作业退出码0。

## 保存与维护

[最终核验](final_acceptance_audit.json)记录本次合并后的数据一致性和设计完整性。原汇总与旧报告生成器的精确副本见[历史归档](../../history/rq1_consolidation_20260917/README.md)。可重建缓存清单见[清理记录](../../maintenance/20260917/README.md)。当前可维护的报告入口统一在`scripts/report_rq1_completion.py`、`scripts/report_rq1.py`与`scripts/plot_rq1.py`，冻结源码另行归档。

当前框架/报告代码冻结包：[current_code.tar.gz](../../maintenance/20260917/current_code.tar.gz)，[校验清单](../../maintenance/20260917/current_code_verification.json)。

报告可在FAST根目录重建（需要原始运行记录仍可访问）：

```bash
PYTHONDONTWRITEBYTECODE=1 /scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python scripts/report_rq1_completion.py --experiment docs/results/rq1_completion_20260917
PYTHONDONTWRITEBYTECODE=1 /scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python scripts/report_rq1.py --experiment docs/results/rq1_completion_20260917
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 scripts/plot_rq1.py --experiment docs/results/rq1_completion_20260917
PYTHONDONTWRITEBYTECODE=1 python3 docs/maintenance/20260917/audit_consolidation.py
```

画图使用安装了Matplotlib的系统Python；代码/结果归档无需重跑硬件即可查看。
