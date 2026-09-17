本次审计结论：**Critic 在旧五 Agent 流程中被实际使用，也触发过动作；但现有证据没有证明它改善了最终受约束的能耗–延迟目标。最近的 DynaX 联合重搜索、硬件修正和最终确认绕过了 Critic 类，不能把这些收益归因于 Critic。**

审计读取 18 份历史 `codesign.json`、共 58 轮记录；其中 15 份配置了 Gemini Critic。配置记录不等于每轮 API 都成功，已记录的失败与规则回退保留在 [audit.json](audit.json)。这不是新的消融实验，也没有重新运行历史 RTL patch。

| 最近实验的动作 | 实际执行路径 | 能否归因于 CriticAgent / LLMCriticAgent |
|---|---|---|
| N1/N2/M/T0/T1 与硬件联合重搜索 | DynaXRediscovery → Kernel proposer / CoOptimizer | 不能：没有实例化或调用 Critic |
| 独立 STA 拒绝后修改 queue 等参数 | refine_rediscovery.py 的 FeedbackLLM → LLMPlanProposer → 独立验证 | 不能：脚本直接构造反馈，旁路 Critic |
| 16 窗口质量失败、确认 T0=0.75 | 后续质量复核与选择脚本，复用之前 LLM 提议 | 不能：由本次交互中的助手安排、脚本执行 |
| schedule 导出、setup、SRAM banking 修正 | 本次交互中的工程修改 | 不能：不是 FAST Critic 发起 |

这区分的是具体软件模块的贡献。独立门与反馈机制确实发挥了作用，但“存在反馈”不能单独证明“这个 Critic 有效”。

**旧流程的具体证据**

- `codesign_17245379`：Critic 指向 queue 的时序瓶颈，脚本随即停止，原因明确是该层 mutation 没有被施加。诊断没有形成优化。
- `codesign_17291098`：Critic 以改善 PE 利用率为由切换到 `xm:32:32:64`。记录中的利用率由 0.8389 升到 0.8992，但模型周期由 5838 升到 8536，约增加 46.2%；模型面积同时下降。这证明它能驱动设计变化，不能证明改善了能耗–延迟目标。这些性能数字在 evaluation.evidence 中明确注明仍为 L1 模型，只有功能做了 RTL 验证。
- 多次记录将已经满足 5% 门限的质量损失 +0.0271 称为不可接受，继而转向更稠密配置。当前 prompt 已加入“精度是门限”说明，但历史行为不能因此改写成成功。
- `codesign_17300572`：4 轮中有 2 次 RTL mutation 被旧门接受，4 轮系统模型周期却一直是 5838，利用率一直是 0.8389336553，最后由 orchestrator 的无进展规则停止。局部过门不等于系统指标改善。
- `codesign_17333938`：仍连续报告旧 queue=2 的 2.528 ns；一条通过的 mutation 测的是 `BlockSched_S4`，即 32×4、queue=4，而当前 plan 为 16×16、queue=2。通用 Scala 源码可能影响多个配置，但这个验收不能证明当前候选改善。最终 `clock_period_constraint_ns` 动作被执行器报不支持；当前源码已补上相关别名，这只说明接线缺陷已修复，不代表此前那次运行有效。
- `codesign_17250825`：最后一次 Critic API 返回 504 后回退到规则版，并输出 acceptance gates passed。这个停止不能当作 LLM 认定收敛的证据。

**当前源码仍存在的关键缺口**

1. 主实验旁路：`fast/agents/rediscovery.py::DynaXRediscovery` 没有 Critic 依赖；`scripts/refine_rediscovery.py::FeedbackLLM` 直接把频率失败交给 proposer。应统一为“评估 → Critic 的结构化干预 → 执行 → 同候选验证 → 结果反馈”。
2. 旧校准表仍写死在 `fast/agents/llm_critic.py` 的 prompt：2.230 ns 执行阵列、2.528 ns 队列、固定 SRAM 面积范围，并把时钟限制写成 queue/divider。新实验的预测阵列高扇出和 SRAM 独立 bank 成本没有自动进入该事实集合。Critic 应消费带 candidate_id、参数、scope、数据来源和保真度的实际观测；未知项保持未知。
3. `UArchAgent.mutate()` 未接收当前完整 plan，通用别名可能落到固定测试目标。应把 rows/PE/M/queue 等尺寸连同 source hash 绑定到干预与验收，复用已有精确候选验证入口。
4. Critique.evidence 的解析只检查有非空字段字符串，尚不是对真实字段和值、来源、候选身份的完整解析校验。
5. 规则 Critic 的 planner-model recalibrate 可以产生 area/power/cycles 缩放建议，但现有计划执行器主要支持维度约束和时钟限制，并非通用模型重标定器；evaluator 重入也没有自动修改保真度的完整动作实现。可表达动作应限制为执行器真实支持的动作，不能把“重入”当成已完成干预。

**怎样判定它有效**

每条干预记录：观测证据、可证伪机制假设、具体动作、固定变量、当前候选身份、预计影响、所需工具、接受标准。执行结果应区分：未执行、约束修复、目标改善、Pareto 新取舍、被支配、失败、不可判定。约束修复有价值，但不是自动等于能耗下降。

在同一候选空间、相同初始观测和预算下比较三个分支：①只给原始工具反馈的 proposer；②规则 Critic；③LLM Critic。三者保留相同质量/功能/面积/时序门，控制额外提议机会，并分别报告有效评估预算和总成本。至少跟踪干预执行率、被独立验证的约束修复率、Pareto 新点数/固定参考 hypervolume 和发现可行点的成本。没有这个比较，现有结果只能说明可运行、能提出建议，无法隔离 Critic 的增量收益。

审计没有修改优化器或重新运行昂贵实验，保留了原始记录、路径和 SHA256。现有工程有接入和验证基础；当前最需要完成的是把 Critic 接回实际实验入口，并建立候选一致的干预验收。
