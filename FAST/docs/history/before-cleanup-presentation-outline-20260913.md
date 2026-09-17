# FAST 汇报提纲：8 页、约 10 分钟

> 最新完整系统生成结果：[参考测试、Hammer 物理实现与 Critic 对照](results/fullstack_extensions_20260913/RESULTS.md)；[20 分钟阅读与新 PPT 思路](results/fullstack_extensions_20260913/READING.md)。下文为较早参数搜索/反馈修正路径的历史记录，数字与结论不能代替本轮生成实验。

按 10 分钟技术汇报准备，若只有 5 分钟，将第 2/3 页和第 6/7 页分别合并。这里给的是可直接制作 PPT 的内容与讲法，不是已生成的 .pptx。代码阅读见 [快速指南](quick-reading-20260913.md)。

## 汇报主线

> 动态稀疏配置改变工作量，也改变硬件瓶颈。FAST 用结构化决策和独立工具反馈连接这些层。我们实现了可追溯修复，并通过消融发现：反馈能提高短预算搜索效率，但已知故障上规则与 LLM 同样有效，LLM 的额外价值需要更困难的外推任务证明。

开场保留研究问题：**Can agentic full-stack co-design replace algorithm-specific manual optimization for dynamic sparse-attention acceleration?** 将它呈现为待验证的问题，不作为已经得出的结论。

可用标题：**FAST: Verifiable Agentic Co-design for Dynamic Sparse Attention**。

## 第 1 页：为什么需要可适配的协同设计？（45 秒）

**页面结论：相同的平均稀疏率，不代表相同的硬件执行效率。**

画两组行长度分布：一组均匀、一组长短悬殊，旁边画等最慢行的 PE。图明确标为示意，不编造实验数字。

讲法：动态稀疏带来不规则的保留列数和访存；算法设置影响负载，阵列与缓冲决定这些负载如何执行，因此只优化一个层的指标可能得不到可用硬件。

## 第 2 页：研究问题与本次成功标准（60 秒）

**页面结论：目标是约束下的同任务能量–延迟前沿，当前里程碑是可验证适配。**

展示概念目标：

`minimize (latency, energy_per_task)`

`subject to quality_loss ≤ ε, area ≤ budget, Fmax ≥ target, functional correctness`

固定任务下，降低 energy/task 等价于提高 tasks/J。强调每个指标要带来源和覆盖范围；当前 L1 能量与 scheduler power proxy 不能替代完整任务能量。

本次成功标准写三条：候选动作自主执行；独立工具可以推翻模型预测；同预算对照可以检查收益。不要把“存在五个 Agent 类”当作成功标准。

## 第 3 页：系统怎样形成反馈闭环？（90 秒）

**页面结论：Agent 提议，工具验证，结构化证据决定下一轮。**

画 `Kernel measurement → Compiler/µArch proposal → RTL/measurement → Critic → next candidate`。箭头上写数据：sparse profile、parameter point、metrics + provenance、validated mutation。

同时列出本轮实际工具：PyTorch/DynaX、Chisel、Verilator、Yosys、OpenSTA。将 proposal 的 FireSim/Hammer 放在“计划中的高保真扩展”，不要画成已完成的这次实验步骤。底部标注最近消融覆盖“固定算法后的 scheduler 修正路径”。

将两件事说清：参数联合搜索入口已经存在；这次最完整的因果对照聚焦硬件反馈，未重新消融算法搜索。

## 第 4 页：展示一次真实失败→修复（90 秒）

**页面结论：功能通过不代表硬件满足频率约束；反馈确实改变了下一轮。**

主图用这三个状态，固定算法和 32×8 scheduler：

| 状态 | queue | STA Fmax | 350 MHz 门 |
|---|---:|---:|---|
| 初始输入 | 4 | 324.071 MHz | 失败 |
| Critic 第 1 轮 | 2 | 341.618 MHz | 失败 |
| Critic 第 2 轮 | 0 | 396.929 MHz | 通过 |

右侧放一条真实动作 `{field: queue_depth, operation: set, value: 0}` 与对应验证字段，不堆整页 JSON。证据来自 [main32_llm_s0](results/critic_ablation_20260911/raw/runs/main32_llm_s0/refinement.json)。

解释 queue=0：每行仍有 1 个工作条目槽，但行间按 tile 锁步。缓冲变小有利于面积和控制时序，同时会增加等待。修复成功不是因为减少了 attention 工作量或放宽频率门。

底部列最终组件结果：251 cycles @350 MHz；0.717143 µs；13,940.262 µm²；2.799779 mW（uniform activity α=0.0213）。醒目标注 **BlockScheduler only; pre-layout; estimated power**。

## 第 5 页：为什么相信这个过程？（60 秒）

**页面结论：每个动作和结论都能追到输入、工具与结果。**

用 `context → mutation → executed point → validation → incumbent` 一条证据链。

列出四条机制：质量/合法域/预算门；非法动作与证据路径拒绝；trace、design、source SHA 与完整工作量检查；保存最优已验证方案，探索失败不会覆盖它。

展示规模：24 次运行×5轮，120 个候选，112 次独立验证，90 次 Critic 分析。注明 8 次候选被 L1 拒绝；112 次都功能通过，其中 62 次通过时序。它们是证据覆盖规模，不是性能提升倍数。

## 第 6 页：Critic 到底贡献了什么？（120 秒）

**页面结论：在随机基线上有搜索收益，但 LLM 没有超过规则版。**

主图用 [quality_cost.png](results/critic_ablation_20260911/quality_cost.png)，展示质量与搜索成本两部分。主表只放三行：

| 随机 proposer 主实验 | 每次最优 scheduler 延迟均值 | 平均运行耗时 |
|---|---:|---:|
| 无 Critic | 1.069524 µs | 94.1 s |
| 规则 Critic | 0.717143 µs | 107.3 s |
| LLM Critic | 0.717143 µs | 336.1 s |

讲法：最优延迟均值低 32.95%；但是 LLM 与规则找到同一最优点，搜索耗时约 3.13 倍。所有组均有 3/3 恢复率，不能说只有 Critic 才能成功。

页面下方或备份页解释额外三组：shadow 候选与 off 完全一致；隐藏独立反馈后首次通过从 2/2/2 推迟到 3/4/4；单字段随机干预恢复 2/3，隔离局部修改本身的价值。等候选预算不等于相同实际工具次数；n=3，不宣称统计显著。

## 第 7 页：换一个条件，结论还能成立吗？（75 秒）

**页面结论：对更强 proposer，收益主要是更早恢复，最终最优延迟没有提升。**

用 [recovery.png](results/critic_ablation_20260911/recovery.png) 的 confirm16 部分，或表格：off 首次通过 1/2/2，Critic 为 1/1/1；最终双方都为 1.194286 µs。

必须说明当前角色限制：batch=1 时 Critic 直接占满候选槽，on 组 proposer 实际没有 API 调用；这属于提议策略比较，不是已经证明两个 LLM 协作的增量收益。确认实验还同时更换了起点与 proposer，不能据此单独归因到某一因素。

列出三项未完成：完整 attention 数值/多行集成验证；工作负载驱动的全系统能量；未见算法/分布上的外推与人工专家基线。

## 第 8 页：贡献、经验与下一步（60 秒）

**页面结论：已交付可验证反馈闭环，下一步要检验跨层迁移能力。**

已交付：参数契约、真实测量与独立验证串联；可执行 Critic 动作、回退与完整轨迹；包含规则/随机/shadow/盲化的消融。

下一步按优先级：

1. 改成 proposer 先提案，Critic 再审查；显式传递剩余 loop 预算。
2. 建立参数→实际 RTL→可观测指标映射，避免反复测同一硬件；保留已验证前沿。
3. 规则能解决的故障先用规则；用新的 M、sequence length、layer/分布与跨模块约束检验 LLM 的额外价值，算法变化重新过质量门。
4. 闭合完整 attention 与存储系统后，再验证真正的 energy–latency Pareto。

收尾可以说：“我们已经能让系统根据可追溯工具证据进行修复；接下来要回答的是，它能否在未见过的跨层问题上，比固定规则和人工流程更高效。”

## 演示与答辩准备

建议演示一次已记录运行：显示 context 中失败的 slack → 展开 mutation → 打开对应 validation → 展示 incumbent。现场回放明确标注“记录回放”；真实 LLM/综合耗时长且依赖环境，可作为可选演示，不以现场 API 成功作为全部证据。

| 常见问题 | 回答重点 |
|---|---|
| 为什么需要 LLM？规则不是一样好吗？ | 本轮已知 queue 故障确实规则足够。LLM 的价值需要在未见故障与跨层适配上检验，这是消融给出的设计方向 |
| 32.95% 是整机加速吗？ | 不是，是随机 proposer 主实验中，每次最优已验证 scheduler 延迟的均值降低；三次重复，固定任务与 350 MHz |
| queue=0 是否绕过了工作？ | 没有，仍发出相同捕获任务的保留列工作，严格 tile 锁步并通过功能检查；每行保留 1 条缓冲 |
| 2.80 mW 是实测芯片功耗吗？ | 不是，是综合网表在统一活动率下的 OpenSTA 组件估计 |
| 参数改了为什么测量不变？ | 当前 gate 只覆盖 scheduler，一些字段影响其他模块或模型；这正是参数到测量范围映射需要改进的原因 |
| 已完成五 Agent 全栈闭环吗？ | 有多条入口与相应闭环代码；当前最新消融覆盖参数修正与 scheduler 验证，不能替代所有路径/模块的端到端验证 |

备份页可放：全部六组主实验表、软件算法配置与质量证据、16-row 的局部能量 proxy–latency 取舍、实际支持的参数表、验证范围、后续正交实验设计。不要用代码目录截图充当架构图，也不要用 LLM 长段文字代替动作与实测结果。

全部数值来自 [消融报告](results/critic_ablation_20260911/RESULTS.md)；详细改进见 [IMPROVEMENTS.md](results/critic_ablation_20260911/IMPROVEMENTS.md)。
