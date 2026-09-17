# Micro-Hackthon：FAST 工作区

当前成果：**FAST 自主生成小规模 DynaX X:M 查询行硬件，完成 E2E → Hammer PPA → Critic → 第二轮设计验证。** 第二轮为 170 ns、1.722 Gqueries/J；范围和建模方法见 [实验报告](FAST/docs/results/dynax_autonomous_20260913/RESULTS.md)。

## 目录与来源

| 目录 | 责任 |
|---|---|
| `FAST/` | 本项目：Agent 框架、可信验证、PPA、参考库和实验报告 |
| `DynaX/` | 算法与上游硬件参考；算法评估侧有本项目此前的参数化/画像扩展 |
| `chia/` | 上游工作流运行时；当前 FullStackFlow 使用自己的调度器 |
| `slurm/` | 集群环境、算法、RTL 和历史闭环作业 |
| `MICRO_A3_Proposal.pdf` | 原始提案 |

DynaX 原硬件、FAST 中维护的硬件参考副本、Agent 新生成设计是三种不同来源。当前生成流程不修改参考库，新设计放入独立运行目录并保留来源哈希。整理过程中不改动算法和硬件库。

## 阅读入口

- [项目 README 与结构](FAST/README.md)
- [20 分钟代码阅读](FAST/docs/quick-reading-20260913.md)
- [架构与 A/B/C 历史路径](FAST/docs/agent-architecture.md)
- [当前状态与证据边界](FAST/docs/STATUS.md)
- [实验复现与归档](FAST/docs/dynax-autonomous.md)
- [PPT 汇报提纲](FAST/docs/presentation-outline-20260913.md)
- [全部保留结果的索引](FAST/docs/results/README.md)
- [本次清理记录](FAST/docs/cleanup-2026-09-13.md)

`FAST_实验执行计划.md` 等早期计划按对应日期解释；最新验收以以上报告为准。环境配置与凭据继续放在各自环境中，实验归档保存工具配置和关键哈希，不包含云凭据或完整工具环境。
