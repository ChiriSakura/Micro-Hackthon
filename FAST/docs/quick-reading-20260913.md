> 实验结果已更新：请以[RQ1四算法总报告](results/rq1_completion_20260917/RQ1_SUMMARY.md)和[最终设计代码](results/rq1_completion_20260917/designs/README.md)为准。下文2026-09-13的性能数字属于历史实验。

# 20 分钟读懂 FAST

先理解一条链：**输入算法 → 规划模块 → 生成并验证 → 组装系统 → 数值 E2E → Hammer → Critic → 新一轮**。

## 推荐阅读顺序

1. **3 分钟：读结果。** 打开 [DynaX 报告](results/dynax_autonomous_20260913/RESULTS.md)，看任务范围、两轮表格和证据边界。先知道“通过”具体意味着什么。
2. **3 分钟：读配置和库。** 看 `configs/fullstack/dynax_autonomous.json`、`libraries/catalog.json`、`libraries/algorithms/dynax_xm_row.py`。区分任务预算、算法数学、硬件参考。
3. **5 分钟：读总循环。** `fast/fullstack/cli.py` → `flow.py`。关注一轮何时进入 PPA、何时调用 Critic、何时停止；看 `contracts.py` 中的 Task/SystemPlan。
4. **5 分钟：读实现调度。** `agents.py` 中 Compiler/UArch/Assembly/Critic 的 prompt，再看 `dispatch.py` 的模块尝试、replan、组装。Compiler 负责计划，不直接替代 UArch 写整个硬件。
5. **4 分钟：对照真实产物。** 打开报告目录的 `run/round_02/result.json`，沿 `sources` 找 4 个 Scala 文件；看 `events.json` 的 `compiler_replan_review` 和 `critic`，再核对 `gate_round_02/summary.json`。

## 阅读时回答五个问题

- 谁定义数学正确性？可信算法插件；Compiler 局部契约是辅助验证。
- 原库可以被 Agent 改吗？不可以。链接 native IP 和生成薄适配器是两件事。
- 为什么模块全通过仍可能 E2E 失败？端口时序、模块连接或 Compiler 的数学契约仍可能错误。
- Critic 起作用了吗？本轮建议改变除法器流水级，实际触发重规划并获得第二轮 PPA 改善。
- 能否据此说替代人工优化？当前证明一次有难度的自主适配与改进；还需等预算对照和更大工作负载。

先不用通读 `fast/agents/rediscovery.py`、旧 `FiveAgentFlow`、GCP 脚本或全部硬件参考文件。它们的用途在 [架构表](agent-architecture.md) 中单独标明。

默认 `rg` 代码搜索会跳过结果目录中的冻结源码和原始运行副本，避免把旧实现误认为当前实现。查看证据时使用 `rg --no-ignore PATTERN docs/results/<实验>/run`，或直接打开报告链接。
