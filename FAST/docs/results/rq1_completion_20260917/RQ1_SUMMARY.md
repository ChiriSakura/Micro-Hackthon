# RQ1：四种动态稀疏注意力机制的全栈适配实验

> Can FAST generalize across diverse dynamic sparse-attention algorithms and automatically derive effective full-stack designs without algorithm-specific manual optimization?

更新时间：2026-09-17T20:35:59.180202+00:00。以下只使用已保存证据；运行/验收未结束的项目保持未完成。

本报告汇总原实验、恢复和后续诊断辅助修复。原四算法各5候选、共20条记录保持不变；辅助修复单列为A1，不伪装成原实验R6或自主成功。这些结果不是同一框架版本从零运行的公平cohort。

## 当前完成情况

| 算法 | 搜索状态 | 尝试轮次 | 完成PPA轮次 | 独立合格轮次 |
|---|---|---|---|---|
| DynaX X:M | budget_exhausted_with_failures | [1, 2, 3, 4, 5] | [1, 2, 4, 5] | [1, 4, 5] |
| Block N:M | budget_exhausted | [1, 2, 3, 4, 5] | [1, 2, 3, 4, 5] | [] |
| Sanger 概率阈值 | critic_stopped | [1, 2, 3, 4, 5] | [1, 2, 4, 5] | [1] |
| Global Top-K | critic_stopped | [1, 2, 3, 4, 5] | [1, 2, 3, 4, 5] | [5] |

原五候选轨迹中已有独立合格点的算法：**3/4**；计入单列后续修复后，工程上有合格设计的算法：**4/4**。两者都不是统一随机实验的成功率。

当前可以支持：FAST在给定算法语义、可信golden/testbench和只读参考库后，能够完成多种稀疏机制的模块实现/组装、数值验证、真实物理提取和Critic反馈。仍不能证明：任意新算法都能成功、优于人工专家，或在真实模型规模下取得加速。以下把可行性、优化收益与泛化证据分开报告。

## 当前最佳已验收设计

每算法选择独立合格点中能效最高的一点。R1–R5来自原轨迹；A1为外部诊断辅助修复，不能并入原轨迹的自主成功率或Critic收益。

| 算法/轮次 | 软件配置 | 留出RMSE | 留出稀疏率 | 频率MHz | 单元面积µm² | 功耗mW | 延迟ns | 能量nJ/query | 能效Gqueries/J |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Global Top-K/R5 | `{"k": 15}` | 2.00188% | 6.25% | 300 | 19154.9 | 6.23409 | 230 | 1.43384 | 0.697427 |
| Sanger 概率阈值/R1 | `{"threshold_256": 3}` | 3.86827% | 37.4794% | 300 | 74779.5 | 23.3001 | 73.3333 | 1.70867 | 0.58525 |
| DynaX X:M/R5 | `{"n1": 7, "n2": 4, "t0_quarters": 2, "t1_quarters": 0}` | 3.6813% | 17.4141% | 300 | 117719 | 41.4466 | 186.667 | 7.73669 | 0.129254 |
| Block N:M/A1 | `{"n": 7}` | 3.33208% | 12.5% | 300 | 41780.9 | 13.4159 | 233.333 | 3.13038 | 0.31945 |

最终测试统一seed=2026091801、8192随机样本。RMSE由软件定点golden输出对浮点dense-softmax参考计算，包含稀疏化和定点近似误差，不是模型任务准确率。独立RTL检查另含重建及5×100次额外执行（边界向量可能重复），布线后网表再进行100次零延时功能检查；8192不表示8192次RTL仿真。

PPA为Hammer/Yosys/OpenROAD布线后提取，Nangate45 TT；功耗使用统一activity=0.1，非芯片实测。能量定义为工具平均功耗×单query延迟；能效为其倒数。面积是单元面积，非die面积。

## 软件配置与硬件方案

### Global Top-K / R5

顶层 `rq1_global_topk`，语言 `chisel`，配置 `{"k": 15}`。

| 模块 | 契约延迟/拍 | 原生链接库 | 职责 |
|---|---:|---|---|
| ScoreCalculator | 0 | 无 | Calculates the dot product of two 2-element 4-bit signed vectors. |
| ExpLut | 0 | 无 | Implements the exponential lookup table. |
| FinalDivider | 18 | 无 | Performs the final normalization division: result = trunc_toward_zero((N*16)/D). |
| rq1_global_topk | — | 无 | Top-level module for the sparse softmax decode-row algorithm. It orchestrates the computation of scores, exponentials, top-k selection, and normalization through a state machine and child modules. |

### Sanger 概率阈值 / R1

顶层 `SangerThresholdTop`，语言 `chisel`，配置 `{"threshold_256": 3}`。

| 模块 | 契约延迟/拍 | 原生链接库 | 职责 |
|---|---:|---|---|
| ScoreArray | 1 | 无 | Calculates 16 parallel dot-product scores from the query and key vectors. |
| MaxExpAndThreshold | 7 | 无 | Finds the max score, computes exponentials via a LUT, and applies the Sanger threshold. |
| Accumulator | 5 | 无 | Accumulates the numerator (N) and denominator (D) for normalization based on the keep_mask. |
| Normalizer | 8 | pipelined_divider | Performs the final normalization division. |
| SangerThresholdTop | — | 无 | Top-level wrapper that integrates all sub-modules and manages the system's control flow and I/O. |

### DynaX X:M / R5

顶层 `Rq1DynaXm`，语言 `chisel`，配置 `{"n1": 7, "n2": 4, "t0_quarters": 2, "t1_quarters": 0}`。

| 模块 | 契约延迟/拍 | 原生链接库 | 职责 |
|---|---:|---|---|
| ScoreAndExpUnit_rq1 | 7 | verified_rq1_score_exp | Adapter for the verified native `ScoreAndExpUnit` module. This module computes attention scores and their corresponding exponentials. |
| DynaX_SelectionUnit | 7 | 无 | Implements the DynaX X:M selection logic. It computes block mass, applies thresholds to determine how many keys to keep (n1=7 or n2=4), and sorts the scores within each block to select the top candidates, generating a final keep_mask. This module corrects the tie-breaking and sorter implementation defects from previous attempts. |
| NormalizationUnit_rq1 | 41 | verified_rq1_normalization | Adapter for the verified native `NormalizationUnit` module. This module performs the final normalization step. |
| Rq1DynaXm | — | 无 | Top-level wrapper for the sparse softmax system, integrating score/exponentiation, selection, and normalization modules. It manages the overall pipeline, data alignment, and I/O protocol. |

### Block N:M / A1

顶层 `Rq1BlockNmTop`，语言 `chisel`，配置 `{"n": 7}`。

| 模块 | 契约延迟/拍 | 原生链接库 | 职责 |
|---|---:|---|---|
| FindMin8 | 0 | 无 | Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard. |
| DividerWrapper | 33 | pipelined_divider | A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result. |
| Rq1BlockNmTop | — | 无 | Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, which is pipelined to meet timing constraints, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation. |

## 后续诊断辅助修复（独立候选）

| 算法/编号 | 独立验收 | Setup/ns | Hold/ns | DRC | 延迟ns | 能效Gqueries/J |
|---|---|---:|---:|---:|---:|---:|
| Block N:M/A1 | 通过 | 0.43733 | 0.00664113 | 0 | 233.333 | 0.31945 |

详细证据：[修复报告](../block_nm_timing_repair_20260917/RESULTS.md)。

Block N:M：外部诊断将score→h_reg的15级串行比较定位为瓶颈；FAST组装UArch一次生成4层平衡树。n=7、系统计划、FindMin8和DividerWrapper、70拍调度均不变。setup从−1.85258663 ns变为+0.43733039 ns，hold转正且DRC=0；独立RTL和布线后网表验证通过。Critic随后收到新源码与测量并选择停止。

这是错误归因纠正后的工程修复证据，不证明原Critic自主发现了正确修复。原R5时序失败，不能以其名义能效计算有效性能加速比。

## 原五候选轨迹：全部外层轮次

| 算法/轮次 | 状态 | 搜索可行 | 独立验收 | 延迟ns | 能量nJ | 能效Gqueries/J | Critic层 | 回退至 |
|---|---|---|---|---:|---:|---:|---|---|
| DynaX X:M/R1 | evaluated | True | 通过 | 200 | 9.53311 | 0.104898 | uarch | — |
| DynaX X:M/R2 | evaluated | False | 未选入验收 | 200 | 9.61229 | 0.104033 | kernel | — |
| DynaX X:M/R3 | candidate_failed | None | 未选入验收 | — | — | — | compiler | 1 |
| DynaX X:M/R4 | evaluated | True | 通过 | 200 | 9.53311 | 0.104898 | kernel | — |
| DynaX X:M/R5 | evaluated | True | 通过 | 186.667 | 7.73669 | 0.129254 | uarch | — |
| Block N:M/R1 | evaluated | False | 未选入验收 | 226.667 | 3.24437 | 0.308226 | compiler | — |
| Block N:M/R2 | evaluated | False | 未选入验收 | 230 | 3.13229 | 0.319256 | compiler | — |
| Block N:M/R3 | evaluated | False | 未选入验收 | 233.333 | 3.23034 | 0.309565 | uarch | — |
| Block N:M/R4 | evaluated | False | 未选入验收 | 286.667 | 3.97733 | 0.251425 | uarch | — |
| Block N:M/R5 | evaluated | False | 未选入验收 | 233.333 | 3.1981 | 0.312685 | uarch | — |
| Sanger 概率阈值/R1 | evaluated | True | 通过 | 73.3333 | 1.70867 | 0.58525 | kernel | — |
| Sanger 概率阈值/R2 | evaluated | True | 未选入验收 | 140 | 3.59463 | 0.278192 | compiler | — |
| Sanger 概率阈值/R3 | failed | None | 未选入验收 | — | — | — | kernel | 1 |
| Sanger 概率阈值/R4 | evaluated | False | 未选入验收 | 46.6667 | 0.824895 | 1.21228 | compiler | — |
| Sanger 概率阈值/R5 | evaluated | False | 未选入验收 | 70 | 1.80673 | 0.553487 | stop | — |
| Global Top-K/R1 | evaluated | True | 未选入验收 | 283.333 | 2.45309 | 0.407649 | kernel | — |
| Global Top-K/R2 | evaluated | True | 未选入验收 | 276.667 | 2.34034 | 0.427288 | uarch | — |
| Global Top-K/R3 | evaluated | True | 未选入验收 | 276.667 | 2.3371 | 0.427881 | compiler | — |
| Global Top-K/R4 | evaluated | False | 未选入验收 | 223.333 | 1.61083 | 0.620796 | compiler | — |
| Global Top-K/R5 | evaluated | True | 通过 | 230 | 1.43384 | 0.697427 | stop | — |

独立验收只覆盖搜索Pareto及按哈希确认未改变的已验收基线；待完成和未选入验收都不等于功能失败。

### 未通过约束的完整物理测量

以下点保留用于诊断，不进入有效Pareto；负slack下按目标频率计算的延迟/能效不能作为可运行性能。

| 算法/轮次 | 单元面积µm² | 模型功耗mW | Setup slack/ns | Hold slack/ns | DRC数 |
|---|---:|---:|---:|---:|---:|
| DynaX X:M/R2 | 133226 | 48.0615 | -0.0729401 | 0.00615974 | 0 |
| Block N:M/R1 | 45186 | 14.3134 | -3.10007 | 0.00693209 | 5 |
| Block N:M/R2 | 42246.9 | 13.6186 | -1.81639 | 0.00819245 | 1 |
| Block N:M/R3 | 42167.1 | 13.8443 | -1.80368 | 0.00337705 | 0 |
| Block N:M/R4 | 42514.2 | 13.8744 | -1.67741 | 0.0080512 | 1 |
| Block N:M/R5 | 42292.9 | 13.7062 | -1.85259 | -2.837e-05 | 0 |
| Sanger 概率阈值/R4 | 64421.2 | 17.6763 | -2.59889 | 0.00906766 | 3 |
| Sanger 概率阈值/R5 | 82930.3 | 25.8104 | 0.00701195 | 0.00723388 | 2 |
| Global Top-K/R4 | 22738.2 | 7.21269 | 0.063588 | 0.0085397 | 2 |

## Agent执行开销

| 算法 | 累计调用 | 累计已记录tokens | 本次恢复新增调用 | 新增已记录tokens | 新增缺usage调用 |
|---|---:|---:|---:|---:|---:|
| DynaX X:M | 106 | 12504773 | 1 | 355005 | 0 |
| Block N:M | 42 | 3183463 | 6 | 786626 | 0 |
| Sanger 概率阈值 | 144 | 10532272 | 1 | 305876 | 0 |
| Global Top-K | 74 | 4292457 | 0 | 0 | 0 |
| Block N:M/A1（辅助，单列） | 2 | 101320 | 2 | 101320 | 0 |

tokens按服务返回的total_token_count求和；缺失usage的调用不估算。Top-K本次只做工具补验，新增Agent调用为0。

## 原五候选轨迹的Critic效果与可支持的结论

- Global Top-K：首个物理可行点R1；最高能效R5，相对该起点1.711×；最低延迟R5，相对该起点加速1.232×。独立验收状态另见表。
- Sanger 概率阈值：首个物理可行点R1；最高能效R1，相对该起点1.000×；最低延迟R1，相对该起点加速1.000×。独立验收状态另见表。
- DynaX X:M：首个物理可行点R1；最高能效R5，相对该起点1.232×；最低延迟R5，相对该起点加速1.071×。独立验收状态另见表。
- Block N:M：原五候选没有可行PPA；后续A1单列，不能计算原轨迹内的有效改善。

这些是单次流程轨迹，不是Critic因果消融；改善可能来自Kernel参数、Compiler规划或UArch实现。没有等预算Critic OFF、固定模板/仅参数搜索及人工优化对照，不能声称取代专家优化。

已核对的跨层变更见 `cross_layer_trace.json`：N:M R1→R2复用相同hash的FindMin8/DividerWrapper，将顶层同拍最大值/掩码/指数逻辑拆为两个状态；Sanger R4→R5保持threshold=1，将Softmax契约3→7拍、选择累加2→5拍并重新实现；DynaX R1→R5同时改变稀疏配置和Selection模块，因此不能把收益只归于某一个层。每个修改是否有效仍以对应PPA和独立验证为准。

## 修复与证据边界

- 已加入阶段保存、独立目录恢复、源文件/库hash核对、失败回退和PPA失败反馈。没有summary.json也可验收逐轮记录。
- Sanger R5的ODB-0445属于工具崩溃。CTS检查点重载探针保留默认全部优化动作后可继续；后端已加入精确错误匹配的一次自动恢复，恢复原IO约束及placement padding，保存原失败和重试日志。是否最终合格仍按布线后结果判断。限制clone/buffer的早期兼容试跑已取消并保留记录，不计新候选。
- Sanger原失败与默认策略重测的CTS前检查点逐字节hash相同；见`sanger_cts_checkpoint_comparison.json`。实际恢复Tcl的约束与完整物理步骤审计见`sanger_checkpoint_constraint_audit.json`。
- Sanger旧ExpStage误诊已经用到期交易的捕获时刻与数学计算复核：golden与契约一致；原始Agent把当前输入误当作流水线输出对应输入。诊断修复不改变测试答案。
- 原Sanger R3的ExpStage还存在具体LUT错误：声明256项但实际240项，索引188的数值也与契约不符；饱和索引255落入默认65535而不是0。详见sanger_lut_diagnosis.json。该只读诊断没有修改原RTL。
- 原Block N:M部分物理日志显示布线前setup slack约−3.142 ns，关键路径涉及score最大值/减法/指数查表。同拍组合逻辑过长的推断见block_nm_ppa_diagnosis.json，最终可行性仍以布线后测量为准。
- 补测的N:M R1与Sanger R4均完成物理流程但违反约束。只读重载布线数据库/SPEF精确重现slack −3.10006952 ns与−2.59888577 ns：N:M路径到exp寄存器，Sanger路径经过组合score及Softmax最大值/差值。证据在`ppa_diagnostics/`；这些外部复核未向运行中的Agent注入答案。
- N:M R2的布线后复核重现slack −1.81639135 ns，最差路径为score寄存器→最大值h_reg。把最大值与指数逻辑拆开已有改善，但若后续只分离并行的mask支路，并不会自动缩短最大值归约本身；需要用真实路径验证后续修复效果。证据见`ppa_diagnostics/block_nm_r2/`。
- N:M R3只改善至−1.80368257 ns，Critic随后猜测乘加器瓶颈。R4的86拍RTL已通过E2E后，受控停止旧作业并切换通用STA反馈版本v4：同一R4重新测量，把工具报告的关键路径和端点网名交给Critic，再用剩余R5预算迭代。没有人工改生成RTL，但有框架开发干预；不能算未干预的原版本Critic成功。
- R4新测量为slack −1.67740512 ns、DRC=1。Critic确实引用了新增路径数据，却把FindMin前缀当成了掩码阶段回传。实际展开RTL中，该网只是score寄存器拼接；h_reg来自串行最大值归约。详见`block_nm_r4_critic_attribution_audit.json`。
- N:M最终R5通过100/100 E2E，完成布线后DRC=0，但setup slack为−1.85258663 ns、hold slack为−0.00002837 ns，仍不可行。五轮预算已用完，未追加第六候选。末轮Critic仍重复网名误归因；其建议没有执行，也不算优化成果。
- 请求审计进一步发现，v4及更早的Critic只拿到实现说明/源码hash，没有已验收的实际代码。后续v5为`accepted_sources`提供经hash核对的当前源码，并提醒综合网名可能是别名。原v4五候选实验未使用此修复；N:M辅助修复后的末轮Critic使用了新上下文，但正确设计建议来自外部诊断，不能归因于v5自主诊断成功。见`critic_input_observability_audit.json`及`critic_source_context_tests.xml`。
- Critic仍有决策质量问题：DynaX R5的末轮建议试图在UArch层缩短固定契约延迟，应进入Compiler重新规划；该建议因预算结束未执行。Sanger的部分建议持续降低误差，但误差≤5%是约束，不能用更低误差代替延迟–能效收益。
- Sanger恢复后的R5完整PPA已修复setup/hold时序，但最终还有via1 Cut Spacing与metal1 Metal Spacing两项DRC，因此排除出有效前沿。末轮Critic把R1称为唯一可行设计并不精确：R2也物理可行，只是被R1支配。详见`sanger_r5_final_ppa_diagnosis.json`。
- 原始任务保留；恢复源目录与预算变更见PROTOCOL.md及recovery_origin.json。旧测量标记为继承证据，新PPA不能伪装成原作业正常完成。
- 四机制规模统一为16 keys、head_dim=2、value_dim=1。Sanger是概率阈值契约，不是完整论文架构；Block N:M的动态选择索引不等于动态保留数量。
- 无需人工修改生成RTL的证据，应连同库组件来源、链接/生成模块和开发期间的框架修正一起披露；不同版本累计成功不能称为无干预的一次性泛化。

Top-K轨迹也说明稀疏率不能代替PPA：k由14变15，删除的key更少，但最终设计能效更高。参数改变与重新生成的选择逻辑/调度同时发生，具体贡献仍需固定架构对照隔离。

## 优先改进项

1. 将Critic的契约修改请求结构化：延迟、吞吐率或接口改变必须由Compiler重新下发契约；不能只依靠自然语言提醒。
2. 通用后端已在v4加入真实关键路径及端点网名反馈；后续增加可靠的源代码映射和DRC类型归因，并验证诊断是否减少无效修改。布线前诊断可用于搜索，最终合格点仍完成布线、寄生提取和独立验证。
3. 对有限查表域补充边界及饱和索引测试；流水线失败诊断始终对齐实际捕获的交易，避免以修改golden掩盖RTL错误。
4. 将精度作为可行性约束，保留所有延迟–能效非支配点；只有同负载、同技术与功耗口径的测量才能用于改善判断。

5. 库源码只读不等于架构选择不可替换。DynaX已验收R5的归一化模块契约为41拍，选择模块为7拍；下一阶段应让Compiler评估替换归一化实现的方案并重新验证，不能只在较小的选择模块内反复压缩一拍。

6. 用同一真实工作负载的VCD/SAIF活动补充功耗分析。当前统一activity=0.1提供一致的物理建模口径，但没有测量不同稀疏模式的实际切换活动；不能据此推断数据相关门控的真实节能幅度。

## 后续正式RQ1实验

冻结同一框架、同一只读库和预算，四算法各至少3次Agent运行、每次最多5候选；最终留出集不反馈搜索。增加固定模板/仅参数搜索和同条件dense基线，另做等预算Critic ON/OFF。报告最终合格率、首次可行耗时、token成本、每算法latency–energy-efficiency Pareto，并增加较大规模或真实模型Q/K/V验证。

Critic OFF对照应让Compiler仍可看到相同的真实测量，并控制总调用/token预算；否则同时去掉反馈信息，无法单独判断Critic角色的价值。

建议再做一次“留出目标算法专属模板”的迁移测试：只保留通用算术、排序、归约、缓冲和接口参考，检验Agent是否仍能适配目标机制。当前DynaX直接链接已验证的专属Score/Exp与Normalization组件，因此“运行期间未手改RTL”和“从未依赖算法专属人工优化知识”是不同命题。算法契约/golden属于正确性规格，专属优化模板属于先验，两者应分别披露。

证据入口：[补完协议](PROTOCOL.md)、[调度任务](all_jobs.json)、[冻结源码](source_freeze.json)、[逐轮结构化汇总](RQ1_SUMMARY.json)、[Sanger失败复核](sanger_failure_witness.json)。
