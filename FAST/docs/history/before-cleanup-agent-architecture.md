# FAST 框架导读

> 新增主线请先读 [参考库驱动的完整系统生成](fullstack-generation.md)。下文保留历史调用链和实验口径，不能将它们自动视为新系统生成流程的证据。

补充阅读入口（2026-09-13）：[快速代码路线](quick-reading-20260913.md)、[PPT 汇报提纲](presentation-outline-20260913.md)、[最新 Critic 消融](results/critic_ablation_20260911/RESULTS.md)。

主体更新于 2026-09-11。本页是当前结构的阅读入口；按日期保存的实验报告记录当时的实现和结果。

## 先建立整体认识

FAST 把算法候选、硬件计划和工具证据串起来。算法的实际稀疏分布影响硬件成本；硬件约束和验证失败再决定下一轮搜索方向。`Agent` 在这里是职责接口，具体提议或决策可以由规则、随机方法或 LLM 实现。

研究目标是约束下的 latency–energy Pareto 搜索。每个点必须对应**同一完成任务**，算法质量、面积和目标频率分别设门限。`energy_j` 目前只覆盖部分组件，计算它的旧功耗锚点尚未按新活动率流程重标定。

先记住两条实际调用链：

```text
A. 联合参数重搜索
   config → run_dynax_rediscovery.py → DynaXRediscovery.run
              ├─ kernel proposer → DynaX adapter → 质量门
              └─ CoOptimizer → hardware proposer → L1 约束与前沿
                    ↑                 ↓
                    └─ Critic 分析与参数干预（占原预算）
                        └──────── 硬件反馈给下一批 kernel proposer
   导出设计 → 可选调度器 RTL/STA 验证 → Critic 复核
   失败时 refine_rediscovery：Critic → 新配置 → 验证 → 再分析

B. Critic 闭环
   已有 kernel search JSON → run_codesign.py → FiveAgentFlow.run_loop
       KernelResult → Compiler → UArch → Evaluator → Critic
                          ↑         ↑                 │
                          └── _LoopState 分层重入 ────┘
                          也可换到另一个已测算法候选
```

A 会重新提议算法参数，B 从已测候选集合出发。两条入口现在都调用 `CriticAgent` / `LLMCriticAgent`：A 使用 `review_search` 分析搜索和子系统验证证据，B 使用 `run` 分析五阶段报告。A 支持算法候选和硬件字段干预，B 另有 RTL 修改路径。A 的 `--critic off` 可做等预算消融。

## 20 分钟阅读顺序

| 顺序 | 打开文件 | 重点看什么 |
|---|---|---|
| 1，3 分钟 | [schemas/models.py](../fast/schemas/models.py)、[contract.py](../fast/schemas/contract.py) | `ExperimentSpec`、`KernelMeasurement`、`CompilerSchedule`、`HardwareCandidate`、`EvaluationResult`；标签怎么保留 M、N1/N2、T0/T1 |
| 2，3 分钟 | [rediscovery.py](../fast/agents/rediscovery.py) | `DynaXRediscovery.run`：提议 → 质量门 → 硬件搜索 → 反馈；这是当前联合重搜索最短主线 |
| 3，4 分钟 | [cooptimizer.py](../fast/agents/cooptimizer.py)、[codesign.py](../fast/agents/codesign.py) | `CoOptimizer.run` 是循环；`CoDesignPoint/Space` 是变量；`violations` 是约束；`estimate` 是模型 |
| 4，4 分钟 | [orchestrator/flow.py](../fast/orchestrator/flow.py) | 先看 `FiveAgentFlow.run_loop` 和 `_round`，再回看 `_LoopState.apply`；不要从全部辅助函数开始读 |
| 5，3 分钟 | [critic.py](../fast/agents/critic.py)、[rediscovery_critic.py](../fast/agents/rediscovery_critic.py) | `review_search` 产出 Critique；`CriticGuidedProposer` 验证并执行动作，`observe` 回写结果；LLM 实现在 llm_critic.py |
| 6，3 分钟 | [attention_tile_system.scala](../hardware/chisel/src/main/scala/attention_tile_system.scala)、[system testbench](../hardware/tb/tb_attention_tile_system.cpp) | IO、FSM、取数反压、计数器；最后看 testbench 的实际通过条件 |

读完后再按需要追 `adapters` 和模板表。`templates.py` 很长，因为它还承载历史组件标定，初读不必逐行看。

## 数据怎样跨层传递

```text
ExperimentSpec + 参数域 + ArchSpecs + Budget
    ↓
KernelMeasurement / KernelSearchReport
    ↓ schemas.conversions.kernel_result_from_measurement
KernelResult + SparseAlgorithmContract
    ↓ CompilerAgent.plan / CoOptimizer.run
CoDesignPoint → codesign.to_schedule → CompilerSchedule
    ↓ UArchAgent.run
HardwareCandidate → EvaluatorAgent.run → EvaluationResult
    ↓ Critic 分析与经过校验的动作（具体接口由入口决定）
下一轮决策 + 阶段记录 + 设计身份 + 验证产物
```

`N1` 是硬件需要容纳的最大保留数，`N2` 是另一档实际保留数；平均稀疏率不能替代容量约束。参数标签示例：`xm:16:8:32:0.75:0.05`。

[conversions.py](../fast/schemas/conversions.py) 只做数据形状转换。调用方先检查测量成功和 `quality_loss <= epsilon`，转换函数不替代质量门。没有完整搜索报告时，转换保留测量身份，并明确缺少搜索上下文。

`codesign.to_schedule` 统一导出硬件与调度参数；Compiler 在此基础上附加搜索预测。注意 `working_set_bytes` 是 tile 驻留容量，而最终计划的 `predicted_bytes` 是任务 DRAM 总流量，二者用途不同。

## 文件按职责分组

| 层 | 核心文件 | 负责什么 |
|---|---|---|
| 协议 | `schemas/models.py`、`contract.py`、`conversions.py` | 输入输出结构、参数身份、跨层转换 |
| 算法 | `agents/kernel.py`、`proposers.py`、`adapters/dynax.py` | 提议稀疏参数、真实质量评估、分布画像和候选集合 |
| 规划 | `agents/compiler.py`、`cooptimizer.py`、`codesign.py`、`plan_proposers.py` | 联合选择 tile、阵列、queue、bank、SRAM、divider；预算、可行性和前沿 |
| 硬件实现 | `agents/uarch.py`、`templates.py`、`rtl_gate.py`、`rtl_mutation.py`、`module_dialogue.py` | 模板来源与验证范围、参数实现、可选 RTL 修改和验证门 |
| 评价 | `agents/evaluator.py`、`adapters/analytical.py`、`verilator.py`、`synthesis.py`、`timing.py` | 区分模型预测、功能仿真、面积、时序、功耗估计 |
| 反馈控制 | `agents/critic.py`、`llm_critic.py`、`rediscovery_critic.py`、`orchestrator/flow.py` | 归因、动作、分层重入、干预结果与前沿停滞判断 |
| 联合重搜索 | `agents/rediscovery.py` | 组织算法–硬件双层搜索，收集跨层反馈 |
| 记录 | `storage/experiment_db.py`、`sqlite.py`、`manifest.py` | 实验阶段记录、缓存、源代码和产物追溯 |
| 运行环境 | `runtime/chia_nodes.py`、`runtime_env.py`、`../slurm/` | 工具执行位置与资源调度 |

依赖方向应是：入口/编排 → Agent → 协议与工具适配。Agent 不应为了通用数据转换而导入编排器。旧转换函数名在 flow 中仅作为兼容别名保留。

## 三层硬件各自用于什么

| 模块 | 当前作用 | 阅读时注意 |
|---|---|---|
| [AttentionTile](../hardware/chisel/src/main/scala/attention_tile.scala) | 组合预测、选择、调度和执行部件，暴露底层控制接口 | 用于数据通路和接口验证 |
| [AttentionTileTop](../hardware/chisel/src/main/scala/attention_tile_top.scala) | 将 QK → exp → AV → norm 的控制放入 FSM | 外部给索引和数据；用于控制与数值路径验证 |
| [AttentionTileSystem](../hardware/chisel/src/main/scala/attention_tile_system.scala) | 加入 BlockTierSelect、硬件 TopK 索引锁存、KeyFeeder 和反压计数 | 单 query 行；分数和 block mass 仍由外部提供 |

它们是不同验证层级，保留有助于定位新系统的失配来源。System 实际先锁存 TopK 输出，再送给调度接口；文件开头的 `sched_from_topk=true` 描述不是当前接线方式，以实现为准。

## 你这轮修复已经接到哪里

| 修复 | 当前接入状态 | 仍需闭合的部分 |
|---|---|---|
| 动态三档选择 | `block_tier.scala` 选择 `{0,N2,N1}`，裁剪 TopK 有效秩；System 已使用 | 当前系统测试强制高档，尚未验证三档与软件完整注意力输出逐维一致；裁剪有效秩不等于省去 TopK 计算 |
| 阈值换算 | `schemas/tier_thresholds.py` 处理 `M/token_len` 尺度 | softmax 概率与未归一化 exp 质量还差整行归一化；默认 `hardware_is_exact()` 为 False |
| 取数与反压 | System 接 KeyFeeder，暴露总周期、停顿、busy/conflict/requests | 当前逐维装载；完整 head 的存储组织和多行并发仍需集成 |
| 广播扇出修复 | PrePE 广播结构与综合保留标记已修改 | 预布局 STA 仍受缓冲、布线假设影响，不能直接当作布局后频率 |
| VCD 活动率 | `adapters/vcd_activity.py` 统计 RTL 平均位翻转率 | 尚不是门级逐网活动标注，也未自动校准每个搜索候选 |
| OpenSTA 功耗 | `timing.py` 改用 `-global`，默认 α=0.0213 | 默认值来自单一 tile 工作负载；`templates.py` 的旧 3.11 mW/lane 仍参与 `energy_j` |

已有 `fast-sys-verify_17383893` 日志中，4/8/16/32 banks 的小用例均完成，均为 92 周期。这个用例没有展示 bank 数带来周期收益；不能据此声称存储优化有效。testbench 当前的 `PASSED` 检查 TopK 集合一致和运行完成，没有最终 attention 输出数值断言。

## 如何读一个“结果”

| 证据 | 可以回答 | 不能单独回答 |
|---|---|---|
| L0 deterministic | 控制流、记录与接口是否能运行 | 模型质量或硬件性能 |
| DynaX 测量 | 给定模型/窗口的 perplexity 与稀疏分布 | 定点硬件输出是否保真 |
| L1 analytical | 模型假设下的预算、候选比较和部分能耗前沿 | 独立验证或整机实测收益 |
| Verilator | 所运行 testbench 覆盖的功能与周期 | 未覆盖的整层任务、面积或功耗 |
| Yosys + OpenSTA | 对应网表和约束下的标准单元面积、预布局时序与功耗估计 | 布局布线后 PPA、完整 SRAM 活动和整机能效 |

不仅看一个总 `fidelity` 标签，还要看**每个指标的来源和覆盖范围**。组件功能通过时，任务 cycles/power 仍可能是 L1。目标频率接受条件要看该目标周期下的 setup slack，而不是只取数据到达时间的倒数。

阅读既有 [最终实验报告](results/final_experiment_20260911/RESULTS.md) 时，注意其功耗记录早于新 `-global` 流程。新旧结果不能无标注混用。Critic 的历史作用见 [审计报告](results/critic_audit_20260911/REVIEW.md)。

## 接下来改代码，从哪里入手

1. 做自主联合搜索：改 `configs/experiments/dynax_rediscovery.json` 的参数域和预算，沿 A 路径追踪每轮算法–硬件反馈。
2. 证明 Critic 有效：A 使用 `--critic off` 做等预算对照，检查 `critic_reviews` 的动作与 outcome；B 还可验证 RTL 修改。参数确实改变、模型前沿扩展、独立约束恢复和整机能效改善是不同结论。
3. 补全当前硬件：从 System testbench 的最终输出断言、三档分支和冲突用例开始，再接预测与归一化。
4. 更新能耗目标：把新流程的组件活动率与功耗锚点接入模型，记录覆盖范围，再重跑对照与 Pareto 搜索。

实际命令入口见 [脚本索引](../scripts/README.md)；本次整理细节见 [整理记录](cleanup-2026-09-11.md)。
