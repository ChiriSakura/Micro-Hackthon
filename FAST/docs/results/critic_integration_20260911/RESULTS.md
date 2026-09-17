# Critic 接入与实际验证

现在联合重搜索默认调用现有的 CriticAgent / LLMCriticAgent，分析可以驱动算法候选、硬件参数和独立失败后的逐轮修正。完整接口见 [Critic 接入说明](../../critic-integration.md)。

## 代码验证

- 全量 Python 回归：**420 passed in 57.48s**。
- 覆盖等预算开关、实际参数改变、算法候选重新测量、未改善如实记录、证据路径/参数域/重复点拒绝、跨层归因与执行，以及独立失败进入下一轮分析。
- 两个脚本的 `--help`、Slurm shell 语法、修改范围的空白检查通过。
- 通过 `--critic off` 做无 Critic 消融；固定工具预算下，Critic 的额外 LLM 调用仍需单独计入成本。

## 最终版本真实复验：作业 17424429

复用原实验的真实质量测量，让 LLM Critic 读取失败的 BlockScheduler 验证结果，最多提出 **2 个新硬件候选**。通过模型约束的候选重新执行 DynaX 工作量捕获、Verilator 功能/周期验证、Yosys 综合和 OpenSTA 目标频率检查。

- 算法：`xm:16:8:32:1.5:0.05`，原记录质量损失 `0.036288`。
- 任务：TinyLlama-1.1B，WikiText，512 tokens，layer 10 / head 0，seed 20260903。
- 目标频率：350 MHz；接受条件使用该目标周期下非负 setup slack。
- LLM Critic：Gemini 2.5 Pro，调用 2 次，合法分析 2 次，总调用耗时 192.97 秒。调用成本未计价。
- FAST 冻结源码哈希复核：通过；运行时只追加了 `hardware/tool_commands.log`，见 source_audit.json；DynaX 使用工作区已有实现。

| 轮次 | 实际动作来源 | 参数变化 | 调度周期 | 调度器面积 μm² | setup slack ns | 独立 gate |
|---|---|---|---:|---:|---:|---|
| 1 | LLM | queue_depth: 4 → 2 | 188.0 | 41951.658 | -0.0701 | 未通过 |
| 2 | LLM | queue_depth: 2 → 0 | 222.0 | 13940.262 | 0.3378 | 通过 |

分析、完整输入、回复、回退、前后参数和独立验证结果见 [最终 refinement.json](v3_final/refinement.json)。每个子目录保存原始设计输入、validation.json 及工具日志；最终验证状态以 refinement.json / validation.json 为准。

## 验证范围

这次证明的是 Critic 接线、动作执行与子系统约束修正；尚未进行同预算的真实无 Critic 对照，因此不能由这次复验推断 Critic 的净收益或 LLM 优于规则。

复用的算法质量记录仅覆盖历史 2 个窗口，没有重新做扩大样本的质量确认。该配置不能因此重新认定为通过扩大后的质量门。本次新捕获的硬件工作量是单个完整 512-token 窗口，独立结果只覆盖 BlockScheduler。

面积是调度器标准单元面积，时序是预布局估计。没有新的整机功耗/能耗测量，`independent_energy_improvement` 保持 null；频率约束恢复也不意味着周期数减少。

## 接入调试记录

前两版真实运行均保留，没有将规则回退记成 LLM 成功：

- [v1](v1_fallback/refinement.json)：LLM 将 attribution 写成说明文字，被解析器拒绝；已明确枚举和证据路径格式。
- [v2](v2_fallback/refinement.json)：LLM 将根因归到硬件，要求 Compiler 改参数，被过严的同层校验拒绝；已将问题归因与动作执行层分开。
- 两版规则回退均执行 queue 4 → 2 → 0。深度 2：188 cycles、41951.658 μm²、slack −0.0701 ns；深度 0：222 cycles、13940.262 μm²、slack +0.3378 ns，通过 350 MHz gate。

三个版本各有 2 个候选，是接线调试与回归复验，不是一个仅花 2 次评估的优化对照实验。全部版本摘要见 [summary.json](summary.json)。
