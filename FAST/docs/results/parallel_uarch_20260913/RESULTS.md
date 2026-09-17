# Compiler 并行派发与独立 UArch 组装

编排改造已完成，最终代码 **473 项测试通过**。真实 Chisel 运行证明了三个模块 UArch 的并发调用、模块功能验证、局部重试和失败屏障；**本次没有通过全部模块验收，没有进入组装、端到端验证、PPA 或 Critic**。不能将旧串行版本的结果算作本次成功。

## 实现与阅读

- [flow.py](current_source/fast/fullstack/flow.py)：Kernel、Compiler、构建、PPA、Critic 外层闭环。
- [dispatch.py](current_source/fast/fullstack/dispatch.py)：派发前准备所有模块任务；按真实依赖就绪状态并行启动独立 UArch 会话；每模块独立 prompt、参考、目录和修复预算。
- 所有非顶层模块通过后，冻结源码及哈希，由独立 `uarch_assembly` 只实现顶层连接和控制；系统验证失败先修复组装，必要时交回 Compiler。
- [tools.py](current_source/fast/fullstack/tools.py)：Chisel elaboration / Verilog lint → Compiler 冻结功能向量仿真 → 算法库独立端到端验证 → 完整顶层综合与 STA。

默认 `module_workers=3`、`module_attempts=3`、`assembly_attempts=3`。父模块等待真实子模块验收，不使用 stub 代替验收。组装者不能修改已验收子模块；源码哈希变化会拒绝结果。当前重规划会重新生成模块，尚无跨 build 的选择性缓存。

## 证据

| 检查 | 结果与范围 |
|---|---|
| [最终测试](parallel_release_validation.log) | 473 passed，123.68 秒。包含并发重叠、依赖等待、独立会话、局部修复、组装修复、不可变子模块及失败屏障。工具替身不算硬件测量。 |
| [真实 Verilator 回归](module_gates/raw/summary.json) | 错误算术模块在 lint 后被功能仿真拒绝，修复后通过；同步复位/寄存器场景通过。手写夹具，LLM 调用 0，不是自主生成。 |
| [真实 Chisel 生成](live_v2/raw/parallel_17597493/summary.json) | 失败；峰值 3 个模块 UArch API 调用并发。没有新的全系统 PPA。 |

真实运行使用 gemini-2.5-pro、threshold-attention 小型集成工作负载、threshold=64。外层预算 1 轮、Compiler 构建预算 2、每模块尝试预算 3，运行约 19.34 分钟。调用次数：Kernel 1、Compiler 5、模块 UArch 14、组装 UArch 0、Critic 0。发生一次 API 429。原始参考库及快照完整性检查通过。详见 [执行分析](execution_analysis.json)。

这是 4-bit Q/K/V、4 个 key 的阈值筛选、加权求和与整数归一化，不是完整 DynaX 或 softmax attention。100 MHz、面积上限 30000 µm²、质量损失上限 0.15 是任务约束；本次未经过系统验收，因此不报告硬件面积、功耗、延迟或能量。

## 实验过程与失败原因

1. [v1](development_v1/RESULTS.md)：Compiler 提供越过端口位宽的测试输入，以及未初始化 reset 的场景，计划在派发前被拒绝。没有调用 UArch。随后加入保留参考代码的计划局部重试、多模块契约错误反馈和测试协议示例。
2. v2 / build 1：三个模块实际并行。ScoreCalculator 的三个场景通过；其他模块的测试在持续送入多笔有效事务后，仅撤销输入 valid 一拍就要求输出 valid 清零，与多级流水线冲突，功能仿真拒绝。
3. v2 / build 2：Compiler 修正流水线排空等待周期，NormalizationUnit 的三个场景通过。新的 Score 测试却要求 q=81 (0x51)、k=133 (0x85) 输出 53，正确点积为 `1×5 + 5×8 = 45`。
4. 聚合测试的输入 7759404092 按四个 9-bit lane 解包为 `[60,398,415,57]`，threshold=64 时权重和应为 813，测试却要求 240；value lanes 为 `[5,6,7,8]`，加权和应为 5293，而测试要求 1700。
5. Score 与 Normalization 的成功来自不同 build，不能合并声称所有模块已验收。模块失败后没有组装、PPA 或 Critic，Pareto 集为空。

主要瓶颈是 **Compiler 手写局部测试 expected 不可靠**，不能直接把这些失败归因为硬件实现错误。模块测试是 Compiler 定义的有限契约测试，不是独立算法 golden；最终算法正确性仍需可信库参考把关。

## 已补上的改进与证据边界

最终代码比 v2 冻结源码增加了以下改进，已通过测试，但不倒算为 v2 的运行行为：

- 同一功能断言连续失败两次，提前交回 Compiler 检查设计和测试；不会自动判定哪一方正确。
- UArch 明确发现数学/时序矛盾时返回 replan_reason，避免明知会失败仍重复生成。
- Compiler 收到最后一次结构化诊断和当前源码；全部尝试保留在模块日志里，错误摘要不重复嵌入所有源码。
- 写事件时深拷贝数据，避免调度器修改列表后改变历史事件。v2 的 module_dispatch.modules 因此日志缺陷显示为空；三路并发证据来自独立 API 审计时间及 uarch 事件，不依赖该字段。

[源码差异](current_source_delta.json) · [最终源码](current_source/) · [完整运行](live_v2/raw/parallel_17597493/)

## 后续优先级

1. 局部 golden 应由可执行、可审查的模块行为契约计算；Compiler 规划接口、数据流和测试场景，避免凭空填写 packed 数值及 expected。先解决这个问题，再重复完整生成/PPA 实验。
2. 为已验收模块增加缓存；复用键覆盖行为契约、接口、测试、源码、算法配置及依赖哈希，不能仅按模块名复用。
3. 再比较新编排与顺序执行的成功率、时间和调用成本。一次并发重叠不等于性能提升，也不是 Critic 消融证据。

本目录保留了冻结源码、原始 API/工具日志、失败设计和测试结果，排除了编译缓存及 core dump。项目 home 配额不足，大目录保存在 scratch，并提供可移植压缩归档；这些结果不改写历史实验。
