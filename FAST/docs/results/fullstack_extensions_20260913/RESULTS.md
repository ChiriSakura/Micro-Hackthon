# FAST：参考测试、真实物理实现与 Critic 生成对照

本轮已完成：硬件模板连同原 golden/testbench 分配给模块 UArch；完整 threshold-attention 顶层经过真实 Hammer/OpenROAD 布局、CTS、详细布线与 OpenRCX；一次相同起点的 Critic ON/OFF 对照产生经过独立验证的有效改进。DynaX 行级自主实验失败；另一次明确标记的外部诊断辅助修复通过独立 E2E、600 次重构建/额外检查和 Hammer 物理实现。完整结果及范围见第 7 节。

## 1. 最终硬件结果

同一 threshold-attention 任务，threshold=64，100 MHz，Nangate45 typical 1.1 V / 25 °C，固定活动率 0.1，质量损失 0.0702564 ≤ 0.15，逻辑/时钟/修复单元面积 ≤ 30,000 µm²。这里的质量损失是 260 条合成 query 对 threshold=0 的归一化输出误差，**不是模型精度或 perplexity**。

| 设计 | Latency ns ↓ | 单元面积 µm² | 功耗 mW | 能效 Gqueries/J ↑ | Dense-equiv TOPS/W ↑ | setup / hold slack ns |
|---|---:|---:|---:|---:|---:|---:|
| 共同起点 | 210 | 7811.622 | 0.982046 | 4.8490 | 0.116375 | 8.3033 / 0.0082 |
| 无 Critic 最优 R3 | 210 | 7681.016 | 0.964725 | 4.9360 | 0.118464 | 8.3118 / 0.0103 |
| Critic 最优 R2 | 90 | 5766.880 | 0.633893 | 17.5284 | 0.420681 | 7.3161 / 0.0094 |

全部五个有效候选通过独立算法 E2E、详细布线 DRC=0、setup/hold slack≥0。共同起点、两组最优的**布线后门级网表**又各自通过 100 次算法 E2E 检查；这是基于同一 Liberty 生成单元功能模型的零延迟仿真，时序证据来自独立 STA，并非 SDF 仿真。两组最优的 RTL 还各完成源码重新构建和 600 次检查（原 seed 100 次 + 五个额外 seed 各 100 次，边界用例会重复）。

相对无 Critic 最优设计，Critic R2 延迟减少 57.14%（2.33× 加速），每查询能效提高约 3.55×，单元面积减少约 24.92%。相对共同起点，能效提高约 3.615×。

所有候选使用同一冻结物理流程、同一 floorplan 策略。core 面积 57,067.64 µm²，die 面积 72,900 µm²；表中单元面积排除了 filler，包含 CTS 与布线修复单元。**面积约束是 cell area，不是 core/die area。**没有生成 GDS，也没有做多 PVT、LVS 或芯片测量。

功耗使用布线后提取的 RC 和统一活动率，经 OpenROAD 建模计算；这已经实际运行物理流程，但功耗本质仍是 EDA 估计。能量 = 平均建模功耗 × 单次 query 延迟。当前不是按饱和流水吞吐测得的能效，也不含芯片外 DRAM/主机搬运能量。

## 2. 最终软件配置与系统设计

软件配置保持 threshold=64；输入是 4 个 key、Q/K 维度 2、V 维度 1 的 unsigned 4-bit 集成任务。此任务是框架验证契约，不应写成完整 DynaX 或 softmax 模型加速结果。

Critic R2 生成的是新 Chisel 系统：输入寄存器 → 4 个并行的两级 ScoreAndWeightUnit → 两级加法树 → 三级 UnsignedDivider → 输出寄存器，总计 9 cycles。除法器每级处理 5 位，共完成 15-bit numerator 的 restoring division。基线除法器每级处理 1 位，共 15 级，系统总计 21 cycles。

Critic 正确识别出：除法器的深流水占据大部分端到端延迟，而 100 MHz 下有充足时序余量。Compiler 据此重规划流水，UArch 重新实现并通过模块/系统验证；最终减少的寄存器也降低了面积及功耗。**这里证明的是 Compiler/UArch 层的有效重设计；本轮有效候选没有改变稀疏配置。**

源码入口：[Critic R2 结果与源码清单](runs/critic_on_17693050/round_02/result.json)，[布线后网表](runs/physical_on_r2_17695367/hammer/par-rundir/routed.v)，[提取寄生参数](runs/physical_on_r2_17695367/hammer/par-rundir/ThresholdAttention.par.spef)。原始 Chisel：[ScoreAndWeightUnit](runs/critic_on_17693050/round_02/build_03/ScoreAndWeightUnit/ScoreAndWeightUnit.scala)、[UnsignedDivider](runs/critic_on_17693050/round_02/build_03/UnsignedDivider/UnsignedDivider.scala)、[ThresholdAttention](runs/critic_on_17693050/round_02/build_03/ThresholdAttention/ThresholdAttention.scala)。sha256 在结果的 sources/implementations 字段中。

## 3. Critic 对照与 Pareto 的证据边界

两组共用完全相同的起始源码，每组本次最多 **3 轮**：R1 为基线重新编译、验证、测量，R2/R3 为两次重新设计机会。历史 5-loop 参数修正消融是另一条路径，不混入本轮生成结果。两组均启用相同参考测试机制、Gemini 2.5 Pro、seed=17，模块顺序执行。

| 组 | R1 | R2 | R3 | 最终状态 |
|---|---|---|---|---|
| Critic ON | 共同起点 | 9-cycle 有效设计 | 错误 threshold 导致独立 E2E 拒绝，无 PPA | failed，保留有效 R2 |
| Critic OFF | 共同起点 | 21-cycle 小幅变化 | 21-cycle 小幅变化 | budget_exhausted，保留有效 R3 |

ON 调用：Kernel 1、Compiler 12、Critic 2、模块 UArch 12、组装 UArch 5；OFF：Kernel 0、Compiler 6、Critic 0、模块 UArch 6、组装 UArch 2。轮数预算相同，**实际 LLM 调用、token 和运行时间并不相同**。ON/OFF 的事件跨度分别约 34.88 / 20.90 分钟，LLM 调用耗时和约 31.97 / 18.06 分钟（串行设置）。后端未记录 token 用量，不能补造 token 成本；[调用成本记录](comparison/costs.json)。只有一次运行/组，不能据此声称多 seed 统计显著性或普遍优于手工优化。Critic 读取的是预布局 PPA，布线后结果是冻结候选的独立重测，不能称为本次在线 Hammer 引导的搜索。

目标已统一为 **Latency ↓ / Energy Efficiency ↑**。queries/J 使用固定任务；附列 dense-equivalent TOPS/W，每 query 固定 QK+AV 共 24 ops（每 MAC 两个操作），不随稀疏率缩小分子。该 dense-equivalent 指标不能当作实际执行操作数的 TOPS/W。

![Latency–Energy Efficiency](comparison/latency_energy_efficiency.png)

本轮每种 PPA 方法都只有 **Critic R2 一个非支配点**，它支配其他有效候选。图展示观察到的 Pareto 集合，尚未证明覆盖一条丰富的权衡前沿。无 Critic R2 在预布局略有改善，但布线后能量由基线 0.20623 nJ 增至 0.20806 nJ；这也说明小幅预布局收益不能自动当作物理实现收益。预布局点与布线后点分开计算；完整数据见 [逐轮表格](comparison/RESULTS.md)、[CSV](comparison/points.csv)、[JSON](comparison/comparison.json)。

R3 暴露了实际流程缺陷：Critic 提出 threshold=128；Kernel 实测质量超限，选择回 64；Compiler 仍跟随旧 Critic 文本生成 128，独立 golden 检查正确拒绝了输出。已修复为：Kernel 类建议必须携带可验证 proposed_config，先测质量再接收；Kernel 最终配置对下游具有约束力，旧建议只留作历史。新守卫有回归测试，**没有把新修复追算成本轮旧快照的成功**。

## 4. 参考 golden 如何进入设计流程

只读库 catalog 为 divider、exponential、Top-K、SRAM、KeyFeeder、RePE、低精度预测、block scheduler 等模板登记原始 C++ testbench / Python golden。Library 将源码、测试文件和 hash 一起冻结。Compiler 按模块检索模板及测试，把相关测试参考传给对应 UArch，并明确新接口、数值格式、时序和边界条件的适配要求。

旧测试是参考输入，不能未经适配就算作新模块验证通过。新模块通过 Compiler 声明的受限行为契约生成测试；最终 Q/K/V→输出的 E2E golden 来自独立算法插件，UArch 不能修改。Chisel/Verilog 均支持，默认逐模块实现，最后单独的组装 UArch 完成顶层。

同时修复了两类 DynaX 生成障碍：行为契约增加 bounded signed/spack/abs 支持；Compiler 在补读模板时保留已经验证的待确认计划，避免重新编写整套接口。参考测试是否提高首次成功率，尚没有独立 ON/OFF 消融证据。

## 5. Hammer 的可复现口径

冻结实现：[hammer_matched_v1](snapshots/hammer_matched_v1/fast/fullstack/physical.py)。Hammer 1.2、实际 OpenROAD 26Q1-2900-gdf79404cd8（官方容器经 Apptainer 执行），完整顶层 Yosys 综合 → placement → CTS → global/detail route → OpenRCX SPEF → post-route power/STA。PDK 为 Nangate45，固定 1 ns I/O delay、5 fF output load、0.1 ns clock uncertainty，额外 hold margin 0.01 ns。

物理后端缺工具、缺 SPEF、非有限指标、无法识别的 DRC 报告会拒绝完成状态，不回退填入分析估算。修复的兼容项包括 flop 映射、tie-cell/CTS 配置、PDN 网格、pin placement、fillers 插入顺序及新版 OpenROAD 参数。早期 bring-up 的失败记录保留；首次完整路由的旧报告曾将 filler 算进 cell area，最终统一重跑后才进入上表。

[Hammer 官方流程文档](https://docs.hammer-eda.org/en/latest/Examples/openroad-nangate45.html)；[OpenRCX 官方文档](https://openroad.readthedocs.io/en/latest/main/src/rcx/README.html)。

## 6. 建议的下一步实验

1. 先扩大可信 DynaX 契约：更长序列、更多 head dimensions、真实数据动态范围、明确 is_quant=True 预测路径，再谈完整模型质量。当前小契约的质量损失不可替代 perplexity。
2. 用相同总 token/工具时间预算做多 seed Critic ON/OFF；再拆成归因、建议、质量守卫三个消融因素，记录成功率、有效候选数、调用成本及超体积。
3. 让 Critic 显式寻找不同流水级数、并行度和频率点，保存所有可行非支配候选。目前只发现一个支配性改进，不足以展示全面 Pareto 探索能力。
4. 对 Pareto 候选追加基于相同代表工作负载 VCD/SAIF 的动态功耗；区分单 query 延迟、启动间隔和饱和吞吐，报告 queries/J 与固定工作量的 dense-equivalent TOPS/W。之后再加入 SRAM、片外访问和多 PVT 条件。
5. 把失败归因视为有效产物：局部测试冲突交回 Compiler 修正契约，系统 golden 不随生成代码修改；对失败建议和重试都保留完整证据。

PPT 可以围绕“相同输入与起点 → Critic 指出除法瓶颈 → Compiler 改流水 → UArch 验证新模块 → 完整系统及门级 E2E → 布线后能效提升”讲一个可追溯案例。结论是已经展示一次有效的自主硬件重设计；尚不能声称 agent 全面替代算法专用手工优化。

## 7. DynaX 算法契约审计

新增 `dynax_xm_row` 契约对应原 DynaX `is_quant=False` 的 X:M decode-row 路径：8 keys、Q/K 维度 2、V 维度 1；signed 4-bit Q/K（步长 1/4）、signed 8-bit V（步长 1/16），scale_factor=1。m=4、n1=2、n2=1 固定，本轮没有搜索这些维度；Kernel 从 t0∈{1.25,1.5}、t1∈{0.25,0.5} 中实测选 t0=1.25、t1=0.25，合成 profile 的归一化误差约 0.1057。

硬件契约从 Q/K/V 自己计算 score、指数查表、block mass、动态 X:M Top-K、重归一化输出；不是由软件预先输入 scores 或 block mass。指数采用 256×16-bit 固定 LUT，输出为 signed 16-bit Q*.8。等分数按较小 key index 优先，这是对原 torch.topk 未指定 tie 顺序的一种确定实现。

[实际 DynaX 软件审计](runs/dynax_contract_audit_v1/audit.json) 调用了上游 `gen_sparsity_mask_xm`，4 个配置各检查 276 条输入，共 1,104 次。没有发现非 tie 的选择语义差异。**在相同合法 mask 下**，LUT 和截断相对浮点 AV 的误差均 ≤ 2 个 Q*.8 ticks。原始 DynaX tie 选择可能改变输出，审计同时保留 original_dynax_float，不能把这个误差界误称为和原程序逐输出一致。

输入含 260 条合成案例和 16 条 TinyLlama 捕获数据的投影。投影只保留前 8 keys、前 2 个 Q/K 维度、首个 V 维度并重新量化；这 16 条投影在当前量化下实际退化成 **1 条独特输入，Q 全为零**。因此真实数据覆盖很弱，不能宣传为 16 条多样的真实工作负载通过，更不能替代全模型评估。

DynaX v1 因有符号契约表达受限而手动终止；v2 在补读模板后丢失已验证计划、反复重写并耗尽单次输出预算，因而手动终止修复；v3 把 v2 已验证的 LLM 计划明确放入 prompt 作为续跑参考，不复用任何 RTL。它不是一次全新、无历史帮助的独立实验。这些开发尝试和最终结果均保留，不把取消记录改写为成功。

阅读与汇报入口：[20 分钟代码路线与 PPT 思路](READING.md)。

DynaX 的另一路明确标记为 **外部 Codex 诊断辅助修复**：[诊断与复用来源](runs/dynax_assisted_17696538/repair_provenance.json)。复用第二次规划中已通过检查的三个子模块，重新构建并测试，向组装 UArch 指出 3-bit 计数器无法达到 8 的错误，并要求保留正确的 unsigned→signed 扩展。没有直接手工修改 RTL，也没有修改 golden。组装 UArch 第一次生成即通过 100 次独立 E2E，延迟固定 44 cycles。这是可用设计的实现证据，不能算成原自主 run 的成功。

辅助修复后的预布局结果：31,157.378 µm²、2.866837 mW、440 ns、1.26140828 nJ/query、0.792765 Gqueries/J、dense-equivalent 0.0380527 TOPS/W（固定 48 ops/query），100 MHz 下 slack=3.304 ns。合成 profile 误差 0.10570359 ≤ 0.15。此处只有一次可行性构建，**没有做 DynaX Critic ON/OFF 或 DynaX Pareto 搜索**；threshold 任务的 Critic 收益不外推到此算法。

辅助设计的源码重构建和额外 seed 检查已完成：[600 次检查记录](runs/dynax_assist_holdout_17696581/summary.json)，包括 seed 101、211、307、401、503 各 100 次独立 reference 检查，均通过。原 seed 和各 holdout 中的边界案例会重复。

目前 DynaX 失败过程还揭示了明确的测试改进方向：unsigned 指数与 signed V 相乘前补零；计数器在有效表示范围内比较终点；动态移位后在 Cat 前截取/赋值到明确 lane 位宽。第三次自主组装中，两个本应为 4-bit 的 mask 经动态移位扩成了更宽表达式，Cat 后出现 `mask=0x81` 而非 `0x11`。这些是实际失败源码中的宽度/控制错误，不应误归因为 DynaX 算法或 golden 错误。后续应让 Compiler 在失败后先诊断并保留已验模块，避免重新生成无关模块引入新错误。

DynaX v3 自主实验的最终状态是 **failed，无有效 Pareto 点，无 PPA**：[原始 summary](runs/dynax_generated_17695143/summary.json)。3 次 Compiler 系统规划、每次最多 4 次组装修复，约 54.70 分钟；实际调用 Kernel 1、Compiler 6、模块 UArch 12、组装 UArch 12、Critic 0，共 31 次。Critic 为 0 的原因是始终未通过独立 E2E，按既定验证顺序没有到达 PPA/Critic 阶段，并非关闭了 Critic。最后仍是 mask 打包位宽错误。v1/v2 的手动中断成本另计，不能把 v3 当作全项目总成本。

辅助修复仅调用组装 UArch 1 次，约 90.17 秒 LLM 时间，但其起点、已验子模块和外部诊断都来自前面的开发过程；**不能把这 1 次调用与自主实验的 31 次调用当成独立、公平的优化消融**。它说明把正确诊断和已验模块保留下来能完成当前实例，不证明框架已经具备同样可靠的自主诊断能力。

### DynaX 辅助设计的最终物理 PPA

[完整 Hammer 报告](runs/dynax_assist_physical_17696580/revalidation.json)，[布线网表](runs/dynax_assist_physical_17696580/hammer/par-rundir/routed.v)，[SPEF](runs/dynax_assist_physical_17696580/hammer/par-rundir/DynaXmRow.par.spef)。同一 100 MHz / Nangate45 TT / activity=0.1 条件，是真实完整顶层 placement/CTS/detail-route/OpenRCX 后的 EDA 建模 PPA。

| 单元面积 µm² | Core / Die µm² | 功耗 mW | Latency ns | Energy nJ/query | Gqueries/J ↑ | Dense-equiv TOPS/W ↑ | setup / hold slack ns | Route DRC |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 31342.248 | 395923.71 / 435600 | 3.61426361 | 440 | 1.59027599 | 0.628822 | 0.0301834 | 3.06287718 / 0.00570249 | 0 |

功能及质量契约、cell area ≤ 200,000 µm²、100 MHz 和路由 DRC 约束均满足。面积预算使用 cell area；较宽松预算带来较大的固定 floorplan，后续有必要把 floorplan 面积/利用率纳入物理设计优化。该点属于 DynaX 行级任务，不与 threshold-attention 的 24-op query 混在同一 Pareto 集合中。

DynaX 布线后 gate netlist 的 [100 次独立 E2E 检查](runs/dynax_assist_gate_17697013/summary.json) 也已通过，周期数仍为 44。四个接受门级检查的设计（threshold 基线、两组最优、DynaX 辅助设计）均通过，并与对应 RTL 周期测量一致。

## 8. 验证与归档

框架回归测试 **492 passed，0 failed，0 skipped**（152.053 秒）：[JUnit XML](validation/fullstack_extensions_final_v2.xml)、[完整测试日志](validation/fullstack_extensions_final_v2_tests.log)。另外执行了本报告所列的真实 Chisel 编译、Verilator 模块/算法验证、Hammer 路由/RC 提取及门级检查；这些硬件运行不是用 Python mock 测试代替的。

[门级与 RTL 周期一致性审计](validation/gate_latency_audit.json)。归档保留原始角色 prompt/response、失败重试、完整配置、只读库快照、最终源码、物理网表/DEF/ODB/SPEF、工具日志、验证记录和逐文件 SHA256。执行环境与外部依赖见归档中的 ENVIRONMENT.json 和 REPRODUCE.md。工具容器及完整 Python/Scala 安装不包含在证据包中，已记录版本与哈希。

最终判断：参考测试传递、完整顶层真实物理实现和一次有效 Critic 重设计均有证据；**DynaX 仅辅助修复版本完成了行级端到端，原 FAST 自主流程本轮失败，完整 DynaX 模型端到端尚未证明。**
