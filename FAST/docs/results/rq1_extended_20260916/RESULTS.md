# RQ1 实验进度与结果

更新时间：2026-09-16T10:00:56.640057+00:00。协议见 [PROTOCOL.md](PROTOCOL.md)。

2 个算法运行；设计轮数、预算与共同约束以本批次 PROTOCOL.md 为准。

| 算法 | 状态 | 最近事件 | 已返回/已发起调用 | 已记录 tokens | 搜索 Pareto | 独立验证通过的 Pareto |
|---|---|---|---:|---:|---|---|
| rq1_block_nm | ppa_failed | ppa | 18/18 | 1000135 | [] | [] |
| rq1_sanger_threshold | failed | failure | 113/113 | 7160536 | [1] | [1] |

## 逐轮数据

| 算法/轮次 | 校准 RMSE | 留出 RMSE | 搜索可行 | 面积 µm² | 功耗 mW | 延迟 ns | 能效 Gqueries/J | Critic |
|---|---:|---:|---|---:|---:|---:|---:|---|
| rq1_block_nm/1 | 0.0335866 | 0.0377542 | False | — | — | — | — | None |
| rq1_sanger_threshold/1 | 0.0383919 | 0.0388676 | True | 74779.5 | 23.3001 | 73.3333 | 0.58525 | kernel |
| rq1_sanger_threshold/2 | 0.0240712 | 0.0239968 | True | 81281.9 | 25.676 | 140 | 0.278192 | compiler |
| rq1_sanger_threshold/3 | 0.0240712 | 0.0239968 | None | — | — | — | — | None |

**rq1_sanger_threshold 失败原因：** RuntimeError: Compiler/UArch build budget exhausted; see compiler_feedback.json

## 迭代观察

软件参数、模块划分与每轮 Critic 原文见 [DESIGNS.md](DESIGNS.md)。

- rq1_block_nm：当前没有满足全部搜索约束的点；不能填报有效能效改善。
- rq1_sanger_threshold：首个可行点 R1；最高能效 R1 （相对首个可行点 1.000×），最低延迟 R1（加速 1.000×）。这是单次搜索观察，非 Critic 因果消融。

## 结论边界

搜索可行要求校准精度、RTL E2E 与完整 Hammer 物理约束同时通过；独立合格还要求留出精度、额外 RTL 向量及布线后门级验证通过。空列表不是证明不存在可行设计。

功耗来自布线寄生与统一活动率的工具分析，并非芯片实测。RMSE 是输出误差，不是模型任务准确率。本轮没有人工优化对照与重复实验，不能据此声称取代专家优化或证明 Critic 的因果收益。

改善比例仅比较同一次运行内可行点，不把时序失败点当成有效初始基线。Critic 的建议被尝试、最终设计通过与可行指标改善是三个不同层次的证据。

后续优先：增加独立重复运行；对相同起点做等预算 Critic ON/OFF；引入真实模型 QKV；扩展 head dimension/序列长度；比较固定模板与人工调参基线。
