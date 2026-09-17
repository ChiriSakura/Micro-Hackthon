# RQ1 实验进度与结果

更新时间：2026-09-16T02:46:04.878164+00:00。协议见 [PROTOCOL.md](PROTOCOL.md)。

4 个算法运行；设计轮数、预算与共同约束以本批次 PROTOCOL.md 为准。

| 算法 | 状态 | 最近事件 | 已返回/已发起调用 | 已记录 tokens | 搜索 Pareto | 独立验证通过的 Pareto |
|---|---|---|---:|---:|---|---|
| rq1_dynax_xm | failed | failure | 71/71 | 6285977 | [1] | [] |
| rq1_block_nm | failed | failure | 22/22 | 1971365 | [] | [] |
| rq1_global_topk | critic_stopped | critic | 74/74 | 4292457 | [5] | [5] |
| rq1_sanger_threshold | failed | failure | 38/38 | 2359424 | [] | [] |

## 逐轮数据

| 算法/轮次 | 校准 RMSE | 留出 RMSE | 搜索可行 | 面积 µm² | 功耗 mW | 延迟 ns | 能效 Gqueries/J | Critic |
|---|---:|---:|---|---:|---:|---:|---:|---|
| rq1_dynax_xm/1 | 0.0447458 | 0.0526185 | True | 125673 | 45.6256 | 200 | 0.109588 | compiler |
| rq1_dynax_xm/2 | 0.0447458 | 0.0526185 | None | — | — | — | — | None |
| rq1_block_nm/1 | 0.0335866 | 0.0377542 | None | — | — | — | — | None |
| rq1_global_topk/1 | 0.0288443 | 0.0349658 | True | 24802.6 | 8.65797 | 283.333 | 0.407649 | kernel |
| rq1_global_topk/2 | 0.0184194 | 0.0209839 | True | 24090 | 8.45907 | 276.667 | 0.427288 | uarch |
| rq1_global_topk/3 | 0.0184194 | 0.0209839 | True | 24108.9 | 8.44735 | 276.667 | 0.427881 | compiler |
| rq1_global_topk/4 | 0.0184194 | 0.0209839 | False | 22738.2 | 7.21269 | 223.333 | 0.620796 | compiler |
| rq1_global_topk/5 | 0.0184194 | 0.0209839 | True | 19154.9 | 6.23409 | 230 | 0.697427 | stop |
| rq1_sanger_threshold/1 | 0.0383919 | 0.0388676 | None | — | — | — | — | None |

**rq1_dynax_xm 失败原因：** RuntimeError: Compiler/UArch build budget exhausted; see compiler_feedback.json

**rq1_block_nm 失败原因：** RuntimeError: Compiler/UArch build budget exhausted; see compiler_feedback.json

**rq1_sanger_threshold 失败原因：** RuntimeError: Compiler/UArch build budget exhausted; see compiler_feedback.json

## 迭代观察

软件参数、模块划分与每轮 Critic 原文见 [DESIGNS.md](DESIGNS.md)。

- rq1_dynax_xm：首个可行点 R1；最高能效 R1 （相对首个可行点 1.000×），最低延迟 R1（加速 1.000×）。这是单次搜索观察，非 Critic 因果消融。
- rq1_block_nm：当前没有满足全部搜索约束的点；不能填报有效能效改善。
- rq1_global_topk：首个可行点 R1；最高能效 R5 （相对首个可行点 1.711×），最低延迟 R5（加速 1.232×）。这是单次搜索观察，非 Critic 因果消融。
- rq1_sanger_threshold：当前没有满足全部搜索约束的点；不能填报有效能效改善。

## 结论边界

搜索可行要求校准精度、RTL E2E 与完整 Hammer 物理约束同时通过；独立合格还要求留出精度、额外 RTL 向量及布线后门级验证通过。空列表不是证明不存在可行设计。

功耗来自布线寄生与统一活动率的工具分析，并非芯片实测。RMSE 是输出误差，不是模型任务准确率。本轮没有人工优化对照与重复实验，不能据此声称取代专家优化或证明 Critic 的因果收益。

改善比例仅比较同一次运行内可行点，不把时序失败点当成有效初始基线。Critic 的建议被尝试、最终设计通过与可行指标改善是三个不同层次的证据。

后续优先：增加独立重复运行；对相同起点做等预算 Critic ON/OFF；引入真实模型 QKV；扩展 head dimension/序列长度；比较固定模板与人工调参基线。
