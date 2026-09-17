# 结束状态核对（2026-09-17 UTC）

**主作业已经停止，但五轮完整实验没有完成。** SLURM 17879193 为 TIMEOUT，运行 06:00:10；第5轮在详细布线阶段被6小时时限终止。以下结论取自保留的逐轮 result.json、仿真日志和调度记录，不能用作完整五轮验收。

| 轮次 | 实际结果 | Critic / 后续动作 |
|---|---|---|
| R1 | RTL E2E 100/100；物理PPA完成，搜索约束可行 | 已调用，建议UArch优化 |
| R2 | PPA完成，但300 MHz setup slack = −0.0729401 ns，不可行 | 已调用，建议Kernel改参 |
| R3 | 模块构建预算耗尽；没有PPA | 回退R1，Critic收到失败证据并建议Compiler修正 |
| R4 | E2E/PPA完成，指标与R1相同 | 已调用，继续Kernel改参 |
| R5 | RTL E2E 100/100，56拍；PPA详细布线未完成 | 超时；没有最终PPA或本轮Critic结果 |

已完成可行点为R1/R4：n1=8、n2=7、t0_quarters=2、t1_quarters=0；300 MHz、60拍/200 ns、标准单元面积132392.988 µm²、工具分析功耗47.665570 mW、能量9.533114 nJ/query、能效0.104898 Gqueries/J；setup +0.318823 ns、hold +0.004170 ns、布线DRC=0。面积不是die面积；功耗是Nangate45典型角、统一活动率0.1的布线后工具估计，不是实测芯片功耗。

精度0.2364%是校准及选参验证的最差相对输出RMSE，**不是最终独立测试结果**。独立8192样本、额外RTL向量、布线后门级功能验收均被收尾脚本跳过：主任务未写出summary.json，后处理虽退出成功，但results.json实际状态为aborted_without_summary，rounds为空。报告作业另因Python环境缺少matplotlib而失败。

目前只能确认FAST打通过本轮规模的DynaX算法→硬件生成/组装→RTL E2E→物理PPA→Critic，并发生过失败回退；尚未证明Critic改善可行点的latency–energy-efficiency Pareto。R5从60拍降至56拍是RTL层面的进展，未完成时序/PPA验证，不能当作可行性能提升。R1仅1.64%稀疏率，约73.83%的查询全保留，也不能据此宣称有效稀疏加速。

原始产物已归档：rq1_dynax_xm/artifacts.tar.gz，共1426文件，archive_verification.json记录SHA-256复核通过。原始记录保持不变。后续需要补齐R5物理评估与独立验收，并修复缺失summary时的收尾恢复，再形成最终实验结论。

---

# 本次恢复运行的启动记录

作业 17879193 已实际运行，不是排队状态。实时阶段以 [RESULTS.md](RESULTS.md) / run/events.json 为准；本文记录启动时的选择，不冒充最终结果。

- 可信算法完整枚举 36 个配置，其中 8 个 n1≠n2 的配置满足校准＋两组选参验证最差RMSE≤4.5%。
- Kernel 首选：{"n1": 8, "n2": 7, "t0_quarters": 2, "t1_quarters": 0}。
- 校准RMSE：0.00236381；三组数据最差RMSE：0.00236381。
- 校准稀疏率：0.01635599；全保留查询比例：0.73830409。该起点接近稠密，不能宣传高稀疏率收益。
- Compiler 已实际读取 verified_rq1_score_exp、verified_rq1_normalization、attention_tile_system_reference 和 bitonic_sort_network。初步计划选择两个原生组件链接，以及新生成的选择模块；计划正式通过、模块检查和E2E/PPA仍以运行结果为准。

Kernel 理由中把更低误差/更低稀疏率视作更好延迟和能效的代理，这不是已证实的关系。保留该原始回复；只能根据后续物理测量判断性能，不能把模型理由当作实验结论。

Compiler 曾因非法 behavior 表达式与括号错误被拒绝，另有一次API 429；修复调用原文保留在 agent_calls/。这些不算已完成的外层设计轮次。

## 首轮已完成的闭环

首轮100/100个RTL E2E测试通过，平均60拍；完整Hammer布局、CTS、详细布线、寄生提取和STA完成，300MHz可行、DRC=0。Critic已经返回建议，第二轮已经开始，并出现已验证score/exp模块的复用与重新验证记录。

| 指标 | 首轮结果 |
|---|---:|
| 面积 µm² | 132392.988 |
| 工具分析功耗 mW | 47.665570 |
| 延迟 ns | 200.000 |
| 能量 nJ/query | 9.533114 |
| 能效 Gqueries/J | 0.104898 |
| setup slack ns | 0.318823 |
| hold slack ns | 0.004170 |
| 校准＋选参验证最差RMSE | 0.2364% |

这是本次恢复运行的首个搜索可行点，不是5轮最终结果。最终8192条独立精度、额外RTL向量、布线后门级功能均等搜索结束后执行。当前稀疏率仅约1.64%，不能宣传高稀疏率收益或相对旧配置的公平性能提升。

Critic建议将SelectionUnit由12拍改为9拍，却选择uarch层；现有模块契约固定12拍，若要改变对外延迟必须通过Compiler重规划。运行仍执行原固定契约检查，不把建议当作已实现的优化。后续应进一步强化Critic层级与契约修改的一致性。

首轮物理构建、全部失败尝试、源码、引用库和测量已归档到 first_feasible_build.tar.gz，273个文件、SHA-256复核通过；测量快照 first_feasible_round.json。完整5轮产物另在主任务结束后归档。
