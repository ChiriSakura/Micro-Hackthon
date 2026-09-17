# FAST：逐模块实现、独立组装与完整 E2E/PPA 验证

2026-09-13。本轮已完成真实 LLM 生成 → Chisel elaboration → Verilator 数值验证 → 完整顶层综合/STA → Critic 分析，并从生成源码重新编译复验成功。实际执行 `module_workers=1`；模块任务、参考绑定和依赖调度保持独立，全部验收后才交给另一个 UArch 会话组装。

这证明了新生成流程在一个可信的 threshold-attention 集成任务上跑通。它不是完整 DynaX，不构成 Critic 性能收益、全模型精度或超越人工优化的证据。

## 最终配置与硬件

| 项目 | 本轮实际配置 |
|---|---|
| 算法 | 4-key threshold-attention，二维 Q/K，4-bit 非负整数输入；阈值筛选、加权求和、整数除法归一化 |
| Kernel 选择 | threshold=64；seed=17；260 条确定性合成 profiling queries |
| 质量损失 | 0.0702564：相对 threshold=0 的平均输出绝对误差 / 15；约束 ≤0.15 |
| 稀疏率 | profiling 中 31.6346%；不等于实测计算跳过率或能耗降幅 |
| 时钟与面积约束 | 100 MHz；完整顶层综合面积 ≤30,000 µm² |
| 实现语言 / 模型 | Chisel / Gemini 2.5 Pro |
| 预算 | max_loops=1；compiler_attempts=3；module_attempts=4；assembly_attempts=4 |
| 模块执行 | module_workers=1，逐模块实现、验证，然后独立组装 |
| PPA 设置 | Nangate45 typical；OpenSTA 全局 activity=0.1；预布局 |

| 新生成源码 | 结构与职责 | Compiler 分配的参考 |
|---|---|---|
| [ScoreAndWeightUnit.scala](design/ScoreAndWeightUnit.scala) | 2 级流水；计算两项 QK 乘积之和、阈值权重及 weighted-V；顶层实例化 4 份 | chisel_carry_and_clock |
| [UnsignedDivider.scala](design/UnsignedDivider.scala) | 15 级 restoring divider；15-bit 分子、11-bit 分母、4-bit 商；分母为零输出零 | pipelined_divider |
| [ThresholdAttention.scala](design/ThresholdAttention.scala) | 独立组装会话生成；输入寄存器、4 路 Score 单元、两级求和、Divider、输出及 valid 控制 | 已验收子模块及系统计划 |

顶层总延迟为 1 + 2 + 2 + 15 + 1 = **21 拍**。归约树和控制在顶层实现，并非所有逻辑都拆成单独模块。该实现仍固定执行四路计算；阈值会筛掉权重，但尚未证明跳过计算能带来收益。

直接阅读 [最终系统计划](design/system_plan.json)、[完整生成 RTL](design/whole_system.v)、[综合网表](design/mapped.v) 和 [源码来源及哈希](design/provenance.json)。算法库和硬件参考库在本轮运行前后完整性检查通过。

## 实测验证与 PPA

| 指标 | 生成运行 | 从源码重新编译复验 |
|---|---:|---:|
| 基础独立 E2E | 100/100 通过 | 100/100 通过 |
| 额外算法 seed 检查 | — | 101、211、307、401、503，各 100/100 通过 |
| 延迟 | 21 拍 / 210 ns | 相同 |
| 完整顶层综合单元面积 | 7,585.256 µm² | 相同 |
| 估算功耗 | 0.6898801 mW | 相同 |
| 估算能量 | 0.144874821 nJ/query | 相同 |
| 100 MHz 下 slack | +8.6215 ns | 相同 |
| PPA complete / feasible | true / true | true / true |

能量按估算功耗 × 单次测得延迟计算。面积是综合单元面积，不是芯片版图面积；功耗使用统一活动率，不是实际工作负载逐网翻转或芯片实测功耗。没有布局布线。两次 elaboration 的 RTL 文件哈希不同，源码生成的路径等文本可随工作目录变化；归档分别保留两版 RTL，以上数值一致不代表文件字节一致。

E2E 使用算法库提供的独立 Python 整数参考，涵盖阈值边界、零/最大输入、重复事务和运行中复位。复验共 600 次检查，其中 500 次来自新 seed；边界输入可能重复，不能称作 600 个互不重复样本，也不是形式化等价证明。

- [真实生成完整结果](live/raw/behavior_17692082/summary.json)
- [源码重编译及额外 seed 结果](holdout/summary.json)
- [原始独立 E2E 日志](design/e2e_sim.log) · [可信向量](design/trusted_vectors.json)
- [完整 Python 回归日志](validation/behavior_final_tests.log)：**484 passed in 113.01s**。
- [真实模块 gate 回归](module_gates/summary.json)：错误算术被拒绝、正确算术通过、同步寄存器通过、正确三拍流水通过、两拍实现违反三拍契约时被拒绝。这里是手写测试夹具，不计入自主生成证据。

## 真实执行中发生了什么

生成作业 `17692082` 完成，退出码 0，用时 21 分 52 秒；复验作业 `17692477` 完成，退出码 0，用时 59 秒，复验不调用 LLM。

1. Kernel 实测候选配置并选择 threshold=64。
2. 第一版 Compiler 计划出现 packed 向量越界，校验器拒绝；保留完整 rejected_plan 后，让 Compiler 针对原计划修正。
3. 第一版 Divider 数学契约仅处理了 15-bit 分子的最高 4 位。模块 UArch 指出 `27000 / 1800 = 15`，该契约却会产生 0，主动请求 Compiler 重规划；没有将错误模块验收。
4. 第二版计划将数学行为写成完整除法，明确 15 拍时序。Score 模块验收通过。
5. Divider 第一次实现复位输出不正确；第二次实现 valid 提前一拍；第三次实现通过冻结的行为测试。
6. 独立组装 UArch 收集全部已验收模块，第一次组装即通过完整 100 条数值 E2E，随后提取同一完整顶层的 PPA。
7. Critic 读取真实结果并给出后续优化建议。源码重新编译、基础及额外 seed 验证成功。

真实调用次数：Kernel 1、Compiler 6（含检索/修复）、模块 UArch 6、组装 UArch 1、Critic 1。详细顺序和原始反馈见 [events.json](live/raw/behavior_17692082/events.json) 与同目录 `agent_calls/`。

`summary.status=budget_exhausted` 表示已用完设置的 **1 轮**预算；本次 `error=null`、验证通过、PPA complete/feasible=true，Pareto 保留轮次 `[1]`。它不是硬件失败，也不表示已找到全局最优点。

开发中此前作业 `17691858` 因 API 超时和计划契约错误，在尚未生成硬件时被人工取消以修复框架。它不计为完整成功/失败实验；[中断标注](development_v3/raw/interruption.json) 和原始调用均保留。

## 框架修复与证据边界

- 新增 `fast/fullstack/behavior.py`：Compiler 声明有界整数表达式和固定延迟协议，确定性解释器计算期望值、随机合法输入、复位与流水排空测试。避免让模型手算全部 golden 和 packed 数字。
- 保留被拒绝的完整 Compiler 计划及具体错误，支持针对性修复；每个模块仍有独立小循环，契约问题返回 Compiler。
- 默认逐模块执行；显式增加 workers 仍可并发。并发调度有回归测试，本轮真实成功证据来自 workers=1。
- 组装只接收已验收模块，不能改写它们；模块通过后仍必须通过独立算法 E2E 才能进入 PPA。

行为契约自身由 Compiler 提出，因此仍可能数学错误；它是模块验证规范，不是可信算法 oracle。当前可执行时序契约支持组合逻辑或固定延迟、II=1 流水；任意状态机、可变延迟、ready/valid 反压协议尚未通用建模。

执行时冻结源码在 [live/source](live/source)。当前生产代码与执行快照仅 `fast/fullstack/agents.py` 有差异：后续补充了“数学行为与微架构分开，用完整除法表达式”的提示，见 [差异](source_delta/agents.patch)。该提示改善尚未经过另一轮真实生成，不能倒算为本次运行行为。当前源码及相关回归测试另存 `current_source/`。

## Critic 做了什么，下一步如何改进

Critic 确实在 E2E/PPA 完成后调用了一次，指出 15 级 Divider 的寄存器开销和较大时序裕量，建议采用迭代复用实现。`critique_applied=false`：本轮预算为 1，**建议未执行、性能收益未测量**。模型关于“非 Pareto 最优”或“必然降低延迟”的判断只是待验证假设。

合理的后续实验是冻结当前设计作为基线，让 Compiler 重新规划 Divider 的延迟/吞吐协议，对比减少流水级、组合实现与迭代复用，并记录相同输入、约束、预算下的完整 E2E/PPA。迭代除法器通常改变 II=1 接口假设，需要协议契约扩展与 Compiler 重规划，不能简单归为保留现有契约的 UArch 修改。

在主张稀疏加速收益前，还应加入利用稀疏性减少工作或切换活动的硬件，并用工作负载活动测能耗。要回答研究问题，还需要同预算无 Critic / 规则 Critic / LLM Critic 对照、多个生成 seed，以及真实 DynaX 算法契约与质量评估。本报告仅确立一个可复用、可验证的完整生成基线。

## 阅读与复现

最快阅读顺序：本报告 → `design/ThresholdAttention.scala` → `design/system_plan.json` → 主仓库 `fast/fullstack/flow.py` → `dispatch.py` → `behavior.py` → `tools.py`。流程说明见主仓库 `docs/fullstack-generation.md`。

原始集群命令和资源配置在 `reproduce/*.slurm`，复验脚本也一并归档。复验需可用的 Java、Scala CLI、Verilator、Yosys、OpenSTA 和 Nangate45 库；工具镜像不包含在报告压缩包内。主仓库中可执行：

```bash
python scripts/verify_generated_holdout.py \
  --run /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/behavior_17692082 \
  --catalog /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/fullstack_behavior_v4/libraries/catalog.json \
  --output /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/my_new_holdout \
  --tool-root /scratch/gz2522/gz2522/tmp/micro-hackthon
```

输出目录必须不存在。原始日志保留执行时绝对路径；迁移机器时需调整工具与路径配置。归档保留完整源码、角色原始回复、失败尝试、RTL、测试及 PPA 日志，排除编译缓存和可执行仿真器。主仓库目录中的大产物链接到 scratch；同目录 `artifacts.tar.gz` 包含真实文件，便于脱离这些链接保存。
