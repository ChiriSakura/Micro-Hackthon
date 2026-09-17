> 2026-09-17 UTC 补完进度：Top-K R5及DynaX R5均已通过共同8192样本、额外RTL种子和布线后网表独立验收。DynaX R5为300MHz、186.67ns、117718.83µm²、41.45mW、RMSE 3.681%，相对保留R1能效提升23.2%。N:M与Sanger剩余轮次仍在运行。最新结果以 [RQ1总结](results/rq1_completion_20260917/RQ1_SUMMARY.md) 为准；下文为早期记录。

> 2026-09-17 UTC 状态更正：DynaX recovery v3 已因6小时时限停止，未完成五轮。R1/R4完成E2E和PPA且搜索可行；R2时序失败、R3构建失败后回退、R5通过100/100 RTL测试（56拍）但PPA中断。独立最终验收未执行，不能宣称最终通过或Critic带来PPA改善。详见 [结束状态核对](results/dynax_recovery_20260916/CURRENT.md)。下文早期进度记录不代表当前仍在运行。

# 当前状态与证据

更新：2026-09-16。当前主线为 `FullStackFlow`；历史阶段状态见 [旧状态快照](history/before-cleanup-STATUS.md)。

DynaX 工程恢复运行（17879193）首轮已通过100例E2E及完整Hammer PPA：300MHz、200ns、132392.99µm²、47.66557mW、DRC=0；已进入Critic第2轮尝试，最终独立精度待搜索结束验证。300 MHz / 5% 最终 RMSE 门槛不变，新增选参验证与0.5个百分点余量、已验证组件只读参考、模块复用后重验证、失败候选回退继续。单列为恢复实验，不计入从零 RQ1 成功率。见 [协议](results/dynax_recovery_20260916/PROTOCOL.md)及[实时结果](results/dynax_recovery_20260916/RESULTS.md)。

新增 N:M / Sanger 扩展库 cohort：4 个上游仓库、6 个只读模板条目，含组件实测和通用框架修正；各要求 5 轮，主作业 8h。该批次与原四算法 v1 分开归档，见 [新协议](results/rq1_extended_20260916/PROTOCOL.md)、[进度/结果](results/rq1_extended_20260916/RESULTS.md)和[参考兼容性调查](results/rq1_extended_20260916/REFERENCE_DISCOVERY.md)。作业提交不代表硬件已通过；以逐轮测量与独立验证为准。

RQ1 v1 主搜索已结束：Top-k完成5轮且R5独立合格；DynaX首轮硬件通过但留出RMSE为5.26%，第二轮构建失败；N:M/Sanger初轮构建失败。四种机制统一 16-key、相对输出 RMSE ≤5%、300 MHz、最多 5 轮。见 [协议](results/rq1_20260915/PROTOCOL.md)与[进度/结果](results/rq1_20260915/RESULTS.md)。以下已验证能力仍对应 9 月 13 日的历史运行，不自动算作新实验结果。

| 能力/结论 | 当前状态 | 证据或限制 |
|---|---|---|
| 从只读参考出发自主生成 DynaX 行级系统 | 已通过 | 主运行 17708305，没有旧计划/RTL 注入或逐次人工修复 |
| Kernel 自选稀疏阈值 | 已通过 | 四个合法配置的真实合成查询分析，最终 6/2 |
| Compiler 分派、UArch 模块实现和独立组装 | 已通过 | 4 个生成模块；本次串行执行 |
| 复用原 native Chisel IP | 已通过 | 只读链接 FixedPointDivPipelined，包含依赖及哈希 |
| 数值 E2E 和 mask 一致 | 两轮通过 | 每轮主流程 100 次；重建及额外种子 600 次 |
| 完整生成顶层的 Hammer 物理 PPA | 两轮通过 | Nangate45，布局/CTS/详细布线/OpenRCX，DRC=0 |
| 布线后网表功能 | 两轮通过 | 各 100 次，零延时功能仿真；时序由 STA 单独检查 |
| Critic 被调用且建议落实 | 已通过 | 2 次 Critic；除法器 18→9 级，重新规划契约与组装 |
| 本次迭代改善 Latency–Energy Efficiency | 已通过 | 260→170 ns，0.958→1.722 Gqueries/J，第二轮支配首轮 |
| 优于无 Critic 的普遍因果结论 | 尚未证明 | 本 DynaX 运行没有等预算、多 seed 的 ON/OFF 对照 |
| 完整 DynaX 模型/长序列加速 | 尚未覆盖 | 8-key、Q/K dim=2、V dim=1 行级合成工作负载 |
| 实测芯片功耗、GDS、多 PVT signoff | 尚未覆盖 | 当前为 activity=0.1 的布线后 EDA 建模 |
| 可脱离旧 scratch 路径保存 | 已归档 | 常规文件、完整压缩包、SHA-256 清单，见报告 |

最终设计：100 MHz；标准单元面积 34,272.77 µm²；建模功耗 3.41660227 mW；每查询能耗 0.5808223859 nJ；延迟 170 ns；能效 1.721696726 Gqueries/J。质量损失 0.139733210 < 0.15，质量定义是合成查询上的归一化 MAE。

[完整结果与方法](results/dynax_autonomous_20260913/RESULTS.md) · [当前架构](agent-architecture.md) · [历史证据索引](results/README.md)
