**FAST 项目研究评审与深化方案（2026-09-09）**

研究问题：Can agentic full-stack co-design replace algorithm-specific manual optimization for dynamic sparse-attention acceleration?

**结论：项目已有可继续发展的实验平台和有价值的硬件案例，但当前证据不足以支持“替代人工优化”。最值得发展的方向，是在明确支持范围和资源预算下，证明结构化跨层反馈能减少针对新稀疏工作负载的人工适配，并用独立验证说明收益及失败边界。**

本评审阅读了两页 proposal、项目与硬件 README、实验计划、最新 agent-architecture 文档，以及搜索器、代价模型、编排器、Evaluator、RTL 与 testbench 的关键路径。评审对象是当前工作区，含未提交修改；基准 HEAD 为 `5b7f1c70cbb852b2502448330168a2d76e77672d`。本次在 FAST 目录运行现有测试，300 项全部通过，并执行了下文列出的局部诊断。没有重新运行集群上的模型评估、RTL 构建、综合或云端 LLM 实验；这些历史数字按“项目记录”引用，未当作本次独立复现。

**1. 研究价值与现有优势**

动态稀疏注意力适合研究跨层优化：保留元素少不必然更快，行间不均衡、PE 尾部空槽、索引冲突、预测开销、缓存与时钟会改变结论。你已经实际碰到了这些相互作用，选题基础成立。

现有工程的优势主要有四项：

- 有真实模型上的精度和稀疏结构画像，能把算法配置与硬件需求联系起来。
- 已重建并验证部分 DynaX 硬件，区分 upstream、patched、reconstruction，保留了基线来源边界。
- 有可替换的规则/LLM proposer、约束门、实验数据库和分层重入，适合做控制变量实验。
- 对失败有具体记录：错误的 bank 散列假设、门环境失败、验证契约漏洞、模型面积漏项等，能形成有信息量的失败分析。

模块时序优化、银行冲突测量和模型修正是有价值的工程结果。但必须逐项记录是人工发现、交互式 AI 辅助完成，还是 FAST 在冻结输入后自主完成。前两者不能直接归入 FAST 自主优化成绩。

**2. 把“replace”改成可以证伪的研究命题**

建议主问题改为：

> Under fixed accuracy and hardware constraints, can evidence-guided agentic co-design match expert-tuned implementations across unseen dynamic sparse-attention workloads with less algorithm-specific human intervention and a bounded optimization budget?

中文：在固定精度和硬件约束下，基于证据的 Agent 协同设计能否在未见过的动态稀疏注意力工作负载上，以较少的算法专用人工介入和受限优化预算，达到专家调优水平？

拆成三个独立问题：

| 子问题 | 必须提供的证据 |
|---|---|
| 优化效果 | 同一平台、同一工作负载与精度约束下，独立测得的 latency/energy/area |
| Agent 的额外价值 | 等预算下对比规则搜索、随机/贝叶斯搜索、no-Critic，以及必要时单 Agent |
| 替代人工与泛化 | 冻结框架后适配新工作负载，记录人工时间、干预次数、专用修改量、失败率 |

区分两种泛化：同一 X:M 算法内换模型/序列/稀疏配置，属于工作负载迁移；换 N:M、阈值剪枝或其他支持的算法族，属于算法族迁移。前者成功不能直接推出后者。算法作为每次实验的固定输入是合理的，跨算法比较发生在不同实验之间，无需让 Kernel 在一轮内替用户换算法。

“替代”宜预注册成非劣效标准。例如 Agent 的 latency 不超过专家的 1.05 倍、同时满足全部约束，并显著减少人工适配时间。1.05 只是可讨论的协议示例，必须在看最终测试结果前确定，并用置信区间与失败任务共同报告。

**3. 最优先修复的实现与证据问题**

以下问题影响实验结论，优先于增加模型数量、Agent 数量或工具后端。

| 优先级 | 检查结果 | 对研究结论的影响 | 修复方向 |
|---|---|---|---|
| P0 | `codesign.py:estimate()` 用 `sequence_length² × point.tile_d` 定义总 MAC 数，`tile_d` 又是可搜索的分块尺寸 | 缩小 tile 会被错误奖励为减少总工作量 | 独立传递真实 head dimension，完整计入所有 D 分块与阶段 |
| P0 | `flow.py:_round()` 调用 Compiler 时没有传候选的 block/keep 参数，Compiler 默认 `block_m=64, kept_per_block=16` | 软件评的是一种稀疏策略，硬件可能构建另一种 | 用类型化算法契约贯穿搜索、RTL、capture 和评估 |
| P0 | `run_codesign.py` 创建的自定义 `ArchSpecs` 用于 Critic/报告，但默认 `_round()` 规划路径未向 Compiler 传递它 | CLI 声明的约束与搜索实际采用的约束可能不同；后验拒绝不能代替约束内搜索 | 把同一不可变 specs 传给全部阶段，记录 hash |
| P0 | `AttentionTile` 控制和 K/V gather 位于外部；TB 逐 query reset，并将每条 query 送入硬件第 0 行 | 可证明局部数值路径，不能证明多行并行吞吐、存储停顿或完整执行时间 | 建独立控制/访存集成 harness，增加多行并发、反压与完成计数 |
| P0 | tile capture 的 reference 是固定 top-n；计划匹配只检查 kept/rows/head dimension，未检查算法、tileK、数据及量化身份 | 形状匹配不能证明同一实验的算法语义匹配 | capture 必须携带 workload/algorithm/config/content hash，逐项匹配 |
| P1 | `gather_slowdown()` 按算法名前缀查表，未知算法退回 xm | 人工标定的算法知识被固化；无法证明新算法适配能力 | 改成真实 index trace 驱动或与标签无关的结构特征模型 |
| P1 | Compiler/PLANNER_MODEL mutation 目前主要设置 `replan=True`，没有把动作值及重标定参数传入规划调用 | “重入某层”不等于执行了该层建议；规则重规划可能重复相同结果 | 引入 typed intervention、持久化反馈上下文和模型版本 |
| P1 | 内层 CoOptimizer 优化 EDP；外层收敛用 MAC/s；其他报告讨论 latency/power Pareto | 不同阶段对“变好”的定义不同；稀疏度收益可能被外层忽略 | 一个 ObjectiveSpec 统一提议、排序、收敛和最终报告 |
| P1 | `_objective_of_report()` 主要检查 L2 字符串，仍使用预测时钟/利用率，且未检查 `functional_passed` | L2 功能标签可能使模型性能被当成已验证进展，失败结果也可能参与计算 | 按每个指标的证据等级及验证范围决定是否可用于收敛 |
| P1 | 功耗模型只覆盖执行阵列和 SRAM 漏电；其余阶段与动态存储能耗缺失 | EDP 排序可能错误，特别是预测/选择较重的设计 | 先用独立 latency + area 作主结果，再补全阶段能耗 |

对应源码：[代价模型](../fast/agents/codesign.py)、[编排路径](../fast/orchestrator/flow.py)、[运行入口](../scripts/run_codesign.py)、[Compiler](../fast/agents/compiler.py)、[Verilator adapter](../fast/adapters/verilator.py)、[AttentionTile](../hardware/chisel/src/main/scala/attention_tile.scala)、[tile testbench](../hardware/tb/tb_attention_tile.cpp)、[capture](../../DynaX/capture_attention_tile.py)、[标定表](../fast/agents/templates.py)。

本次局部诊断，使用合成 KernelResult 隔离代码行为，**不作为加速器性能测量**：

```text
固定 sequence_length=512、稀疏度、阵列、bank、queue 等，仅修改 tile_d：
tile_d=64 -> cycles=119957.0944
tile_d=32 -> cycles= 59978.5472
cycle_ratio=0.5，EDP_ratio=0.25

相同 bank_count=8，仅改算法标签：
xm:32:4:64   -> slowdown=2.145
xm:64:32:128 -> slowdown=2.145
nm:16:64    -> slowdown=1.186
unseen      -> slowdown=2.145

Compiler 默认路径输入 sparse_method='xm:32:4:128'：
status=passed，block_m=64，kept_per_block=16
```

如果 `tile_d` 表示分块大小，完整工作量的 D 不应随它变化；如果表示真实 head dimension，比较的任务就变了，而且 RTL 的 `headDim` 又由独立参数传入。这两种解释都需要修正当前协议。

另一个单位问题：`power` 明确以 mW 表示，`energy=power*seconds` 得到 mJ，`edp=energy*seconds` 得到 mJ·s；代码注释却写 J·s。统一乘 `1e-3` 或更正单位字段。统一倍数通常不改变排序，但会破坏绝对值对比和阈值解释。

**4. 现有实测结果应如何表述**

[算法结果表](results/results.md)覆盖 TinyLlama-1.1B、BLOOM-560M，seq=512，各取 8 个评估窗口。这是 smoke/探索证据，尚不足以确认长期质量保持：

- TinyLlama 默认 xm 的相对 PPL 增长约 14.44%，不能称 negligible accuracy loss。
- `xm:32:16:64` 在该设置下相对 PPL 增长约 2.36%；能否接受由预先给定的 ε 决定。
- 表里的 CPU wall time 是软件路径运行时间，不能当 ASIC acceleration speedup；也不能由稀疏率直接推出加速比。
- 不同方法的稀疏率统计需统一分母。建议同时报告相对完整矩阵与相对 causal-valid 元素的 retained ratio，以及实际执行 MAC 数，避免把因果遮罩本身当成稀疏算法收益。

[最新架构记录](agent-architecture.md)比旧实验计划更接近当前实现，但里面仍混合历史与现状：

- 文档报告整设计面积预测与工具/宏组合估计相差约 1.3%，但模型刚按该实例修正过。它是合理的校准结果，不是 held-out accuracy。
- 文档记录 LLM 变异使模块 critical path 从 2.760 ns 到 2.736 ns，约 0.9%，且曾暴露 TB 契约漏洞。应在修复后的门上重验保存的 patch，再报告其有效收益。
- 对应变异门曾用 queue depth=4，而计划为 depth=2。模块改进数字必须与计划配置一致才能进入系统估计。
- 模块面积可以组合估计，但多个模块通过功能验证不推出完整系统正确，模块 STA 的最大值也不自动等于集成系统 Fmax。
- 未缓冲或时序不完整的网表报告既不能直接当物理可实现频率，也不能仅凭“伪影”判断就忽略；需要完整约束和可解释的实现流程确认。

已有 300 项单元/控制测试是工程优点。本次发现说明还需要“固定工作量守恒、参数传递一致、验证范围不升级、动作被实际执行”这类跨模块不变量测试。

**5. 最有研究深度的三个改进**

**A. 从算法标签查表改为稀疏结构契约。**

引入统一 `SparseWorkloadContract`，包含模型与数据身份、真实 D、Q/K 长度、causal 规则、算法参数、预测/量化语义，以及逐层/逐头的 index trace。结构特征至少覆盖 row-length 分布、PE 尾部浪费、tile 内相关性、bank 请求直方图、复用距离与热点列，而不只是平均 sparsity 和一个 imbalance。

X:M 的契约必须表达每块依据概率质量选择 `{0,n2,n1}`，不能仅用一个固定 kept 值替代。若某个硬件版本只支持固定 top-k，应显式限定 supported semantics，并把它作为子任务评估。

留出一个算法族测试时，冻结 proposer prompts、规则、模板与标定数据。允许接入声明式语义与 trace，但将任何新写的算法专用规则计入人工适配成本。可增加 label-blind 对照：移除算法名字，仅提供语义和结构画像，观察性能是否保持。这样才能区分“理解结构”与“记住方法标签”。

**B. 把 Critic 变成提出和验证干预假设的模块。**

目前真实数字引用不代表机制归因正确。建议每条 Critic 输出包含：目标模块/层、受影响指标、候选机制、固定变量、拟执行干预、预期变化方向、所需测量、验收阈值、不可判定条件。

例如“bank 冲突导致延迟”应在相同 trace/PE/clock 下只改 bank 组织，检查 memory-stall 和完成时间；“queue 限制时钟”则保持 workload 与 array 不变，只改实现，并在相同配置上重测 timing 和协议。失败信息应区分工具环境失败、功能失败、无收益和其他指标退化。

固定 workload 的单因素干预有助于归因，但不能替代跨层协同。为证明耦合，做一个小型 2×2 实验：原布局/新布局 × 原 bank 组织/新 bank 组织。对 latency 定义交互项 `I=y11-y10-y01+y00`。显著交互说明两者收益不能由独立优化相加解释，随后再研究 Agent 能否在等预算下找到联合配置。

可将已发现的工作守恒、drained 时序、bank 热点、除法器瓶颈作为受控故障/瓶颈任务集。用 held-out 任务衡量归因准确率、可执行动作比例、修复率、工具调用数和收益预测误差。生成与调试可见测试之外，还应有独立隐藏验证，避免循环逐渐适配已知测试。

**C. 多保真评估不仅标标签，还负责选择下一项最有价值的测量。**

每个数保存 `value/unit/source/config_hash/workload_hash/coverage/uncertainty`。模型预测与实测应分别保留，避免合并后只剩单个浮点数。功能、cycles、timing、area、power 是不同证据轴，不宜只用一个 L0/L1/L2 全序代表。

当两个候选的预测差异小于模型误差，优先追加能区分两者的独立评估；当 trace 结构超出标定范围，主动升级 trace simulation。衡量排名相关性、top-k 选优错误率、最终 regret 与高成本评估节省量。校准集和测试集按配置/模型/算法族分开，避免用标定点验证自己。

这能形成完整机制：结构画像提出瓶颈假设，干预验证假设，测量更新模型，再指导下一轮设计。

**6. 最小可信实验矩阵**

先固定一个 supported algorithm 和完整 attention 执行契约，在同一修复后的硬件起点上比较方法，再扩大到算法族迁移。

| 方法 | 作用 |
|---|---|
| 修复并冻结的 DynaX-derived 默认实现 | 共同有效起点；不是直接照抄论文 28nm 数字 |
| 专家调优实现 | 回答能否接近人工水平；记录时间、工具权限与已有经验 |
| 现有 GuidedProposer + 规则 Critic | 排除人工启发式本身带来的收益 |
| Random/Sobol 与一个 BO/TPE 搜索器 | 检验是否只是更多搜索预算 |
| FAST，无 Critic | 隔离反馈贡献，保留相同有效性门 |
| FAST，固定模型/无跨层重入 | 隔离在线修正与跨层动作贡献 |
| 完整 FAST | 主方法 |

如要主张“五角色分工”本身有效，再加入同模型、同工具、同 token 预算的单 Agent；否则不必把 Agent 数量作为论文贡献。

公平性必须分两层：

- 在共同参数空间比较所有搜索器；候选测量环境、初始化、缓存待遇一致。
- 若完整 FAST 允许改 RTL，参数型 BO 无法表达同样动作。应另设 RTL 变异空间对照，或把收益拆为“参数搜索收益”和“新增实现动作收益”，避免把动作权限优势说成搜索智能优势。

同时报告等独立评估次数与等总优化成本。模型调用、非法输出、工具失败、回退、重试、GPU profile、综合、准备基线的人工劳动都计入成本。重复采样确定性温度 0 的同一请求也不能假定回复必然一致。

建议先用现有两个模型，扩到支持上下文内的 512/2K 序列、多层多头和多个独立文本块；资源允许再增加一个未用于调试的模型或更长序列。初始每种搜索至少运行 5 个独立 seed，结果不稳定时增加重复。最终质量集与搜索/标定集分离，按文本块进行配对分析；报告 NLL/PPL、误差区间和完整任务数。

对于完整性能，优先完成 Verilator 中可复现的多行执行、队列与 bank-stall harness，再考虑 FireSim 系统扩展。FireSim 的价值取决于需要观察的系统接口与模型，不会自动补上缺失的控制器、存储或算法契约。

建议最少交付六类图表：

1. 独立验证的最佳可行 latency 随评估次数和总成本的曲线。
2. 精度约束下 latency-area 或 latency-energy Pareto，逐点标明证据来源。
3. 留出工作负载/算法族的适配成功率、人工时间和性能差距。
4. no-Critic、规则 Critic、完整 Critic 的消融结果。
5. 模型预测与独立测量的散点、排名误差及置信区间。
6. 一条完整成功轨迹和一条失败轨迹：证据→动作→RTL/config diff→验证→目标变化。

**7. 性能模型与硬件深化的具体路线**

总工作量应固定真实 Q/K 长度、head dimension、head 数和 batch。至少分别计算 prediction、selection、稀疏 QK、softmax、稀疏 AV、索引/控制、片上与片外搬运。QK 与 AV 均需计入；tile 改变的是分块次数、重用、尾部损耗和重叠，而不是任务本身的 D。

阶段重叠应用资源/依赖模型或 trace simulation 表达。`compute_cycles × 固定 bank slowdown` 可以作为待校准近似，但不能预设其在所有稀疏配置、regWidth 与 bank 数上成立。bank 数还应接入物理 SRAM 组织及端口宽度；当前面积路径主要按容量调用宏规划，不能据此认定所有 bank 配置的宏代价已覆盖。

先做一个能够输出正确结果且有可信总周期的集成版本：内部控制 FSM、反压、真实 K/V feeder、逐行 variable kept、跨 pass 与跨 tile 归一化状态、必要的流水排空。对长上下文增加数值稳定性验证；不能靠选取不溢出的短小输入替代稳定 softmax 设计。既验证固定点数值契约，也在模型质量端使用同一预测和量化语义。

功耗尚不完整时，以固定约束下 latency 为主目标、area 为约束，将 EDP 标成探索性预测。补全后统一 J、s、W 和电压/频率/活动率条件；改变 divider pipeline 后不能用固定功耗且只缩短周期的假设直接宣称系统级大幅 EDP 改善。

**8. 相关研究定位与 proposal 改写**

CHIA 已明确覆盖循环工作流、工具集成、隔离、可靠执行及 agentic 硬件研究案例。因此 FAST 的贡献应放在动态稀疏领域的契约、跨层反馈机制、测量选择与迁移结果，而非“五节点接入 CHIA”本身。[CHIA 原论文](https://arxiv.org/abs/2606.27350)

Sanger 本身研究可重构架构与稀疏注意力协同设计。因此 proposal 将既有 DSA 笼统说成“static”容易混淆设计过程与运行时适应性；建议具体说“专家针对算法和工作负载手工构建、验证与调优的设计流程”。[Sanger 作者版论文](https://liqianglu-zju.github.io/files/conference/2021/MICRO_2021_Sanger.pdf)

新版相关工作至少补充两条方向：NSA 体现硬件友好的动态稀疏算法；PADE（HPCA 2026）研究预测器消除与阶段融合。前者提示算法质量与硬件效率需要一致评估，后者提示当前固定 predictor→selector→executor 模板空间未必覆盖新的结构性优化。无需在 hackathon 内复现所有算法，但必须明确支持边界。[NSA](https://arxiv.org/abs/2502.11089)、[PADE](https://arxiv.org/abs/2512.14322)

proposal 建议作五处调整：

- 主问题采用“在限定范围达到专家水平、减少人工介入”，保留 replace 作为总愿景。
- 不声称组合已验证模块“保证”硬件有效性，改为用模块契约、集成测试和独立检查建立证据。
- 不笼统说稀疏化改变 O(N²) 渐近复杂度；固定比例保留或 dense prediction 仍可能是二次开销。区分操作数减少和复杂度阶数变化。
- 用独立最终评估和等预算对照作为成功条件，利用率只是解释指标。
- 将 FireSim/P&R 定为针对系统/物理主张的扩展验证；当前可交付范围以真正完成的工具路径为准。

**9. 建议执行顺序与完成条件**

| 阶段 | 交付物 | 完成条件 |
|---|---|---|
| 第一阶段：修正协议 | workload/algorithm/arch/objective/verification 的统一契约 | 固定工作量守恒；全部参数可追溯；错误 capture 拒绝；每项 mutation 确实执行或明确报不支持 |
| 第二阶段：可信性能 | 集成 trace/RTL harness 与独立结果文件 | 正确输出、多行并发、访存与控制成本可测；报告范围与实际覆盖一致 |
| 第三阶段：公平比较 | 固定空间下规则、随机/BO、no-Critic、FAST 的重复实验 | 等预算曲线、置信区间、失败与回退成本齐全 |
| 第四阶段：替代与迁移 | 冻结框架后的专家/Agent held-out 适配实验 | 能量化人工节省与性能差距；未成功任务同样保留 |
| 第五阶段：扩展主张 | 完整能耗、物理实现或系统验证 | 仅为确需这些证据的论点追加工具投入 |

建议用一份机器生成的现状表替代互相矛盾的历史叙述：每个 claim 对应 status、代码/配置版本、artifact URI、测量范围和最后复现时间。原始日志可以保存在集群，但目录内应有带校验值的轻量 manifest，避免论文数字只能在聊天记录或注释中找到。

项目当前最值得追求的成果，是一个能在受限预算下依据可验证反馈完成新稀疏工作负载适配、并清楚说明何时仍需要专家的协同设计方法。完成前三阶段即可形成可信的 hackathon 展示；完成第四阶段，才开始直接回答研究问题中的“replace”。
