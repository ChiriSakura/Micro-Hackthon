# Latency–Energy Efficiency 实验协议

当前目标：在质量、面积、频率和功能约束下，寻找延迟更低、能效更高的测得设计。旧协议和失效功耗口径下的实验叙述已保存到 [历史文档](history/before-cleanup-energy-latency-hackathon.md)，不再用作当前结果。

## 指标和有效性

- `latency_ns`：固定输入范围下，独立 E2E 实测周期 × 目标时钟周期。
- `energy_nj`：建模平均功率 × 单请求延迟；注明 activity、工艺角和后端。
- `energy_efficiency_queries_per_joule`：每查询能量的倒数；同一任务下与最小化能量等价。
- 先通过功能、质量、物理完成性、面积与时序约束，再纳入 Pareto 比较。
- 标准单元面积、core、die 分开报告。查询能效与 dense-equivalent TOPS/W 分开，注明 ops/query 定义。
- 原始 Hammer 数据、独立复验和预布局估计分开记录。不同算法/规模/质量指标的点不放入同一前沿。

## 下一次 Critic 受控对照

固定算法及工作负载、起始设计、工具/模型版本、约束和停止条件；分别跑无 Critic、规则 Critic、LLM Critic。多 seed 重复，每种方法记录相同口径的 LLM 调用、token、硬件工具调用和总耗时。明确公平预算采用哪一种，并同时报告其他成本。

评价成功率、首次可行时间、等预算非支配点、相对共同起点的改进与失败尝试。保留所有无效候选和预算耗尽情况；固定超体积参考点后才比较前沿质量。分析模块改写范围，避免把整轮变化归因于单一参数。

本次 [DynaX 两轮实验](results/dynax_autonomous_20260913/RESULTS.md) 已证明一轮可验证的改进，但不是上述 ON/OFF 消融。历史 [5-loop 消融](results/critic_ablation_20260911/RESULTS.md) 属于参数修正路径，不能替代新任务的对照。
