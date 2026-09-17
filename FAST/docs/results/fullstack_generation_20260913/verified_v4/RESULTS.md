# 完整系统生成：Chisel / Verilog 集成验证

这是新主线的 bring-up 记录，不是 Critic 消融，也不是两种 HDL 的公平性能比较。

算法为 4-bit threshold-attention：QK 阈值筛选、加权求和、整数归一化。它不等于 DynaX 或 softmax attention。每轮使用独立 Python 参考驱动的 100 个全系统数值用例。

面积为完整生成顶层的 Nangate45 综合单元面积；功耗为 OpenSTA 全局活动率预布局估计，能量为该估计功耗乘以实测周期对应的延迟。没有布局布线或逐网工作负载活动标注。

| 运行 | 轮次 | 语言 | threshold | 验证 | 面积 µm² | 功耗 mW | 延迟 ns | 能量 nJ | slack ns | 可行 |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| fullstack_17590231 | 1 | chisel | 64 | 通过 | 1718.63 | 0.14797 | 205.6 | 0.0304227 | 8.0413 | 是 |
| fullstack_17590231 | 2 | chisel | 64 | 通过 | 3306.65 | 0.242857 | 69.1 | 0.0167814 | 3.407 | 是 |

## fullstack_17590231

状态：`budget_exhausted`；参考库完整性：`True`；保留的 Pareto 轮次：`[2]`。

约束与预算：`{"algorithm": "threshold_attention", "prompt": "Design a complete threshold-sparse attention accelerator from q/k/v inputs to normalized output. Analyze the allowed threshold configurations, then co-design the complete datapath and control. Prefer reusable modules; explore energy-latency tradeoffs within measured quality, area and clock constraints.", "constraints": {"max_quality_loss": 0.15, "max_area_um2": 30000, "frequency_mhz": 100}, "max_loops": 2, "compiler_attempts": 3, "module_attempts": 3, "seed": 17, "kernel_profile_budget": 16, "activity": 0.1, "hdl": "chisel"}`

LLM 调用次数：`{"kernel": 1, "compiler": 1, "uarch": 8, "critic": 2}`。

### 轮次 1

重入：`kernel`；状态：`evaluated`。

可信 Kernel 分析：`{"config": {"threshold": 64}, "quality_loss": 0.07025641025641026, "quality_metric": "mean absolute output error / 15 vs threshold=0", "quality_scope": "260 deterministic synthetic profiling queries; not model perplexity", "sparsity": 0.31634615384615383, "active_keys_histogram": {"0": 20, "1": 27, "2": 47, "3": 74, "4": 92}, "samples": 260, "seed": 17}`。

完整顶层：`ThresholdAttention`。Compiler 保留的接口/拓扑计划（实现文字可能仍为初始版本；最终流水深度以本轮源码和实测周期为准）：

The design adopts a sequential, iterative architecture to minimize area, which is a key constraint (`max_area_um2`: 30000). The computation is broken down into three main stages controlled by a central FSM: input latching, iterative score/weight calculation, and division. A single `ScoreAndWeightUnit` is instantiated and reused across the four keys, processing one key per cycle. This saves the area of three additional units compared to a fully parallel design. The accumulation of `weight_sum` and `weighted_value_sum` is performed within the top module's control logic. For the division `floor(weighted_value_sum / weight_sum)`, a dedicated iterative restoring divider module (`Divider15by11`) is used, offering a good trade-off between area and latency. It computes a 15-bit quotient from a 15-bit dividend and 11-bit divisor in 15 clock cycles. The total latency is approximately 22 cycles (1 for start, 4 for key processing, 1 for divider setup, 15 for division, 1 for final output), which is well within the 128-cycle budget. Numeric widths are chosen based on the `numeric_bounds` to prevent overflow while minimizing datapath size. The `threshold` value is hardcoded to 64 as specified in the profiling configuration.

| 新生成模块 | 依赖 | 职责 |
|---|---|---|
| ScoreAndWeightUnit |  | Calculates the score for a single key-query pair and applies a threshold to generate the corresponding weight. This is a purely combinational module. |
| Divider15by11 |  | Performs unsigned integer division of a 15-bit dividend by an 11-bit divisor, producing a 15-bit quotient. It uses an iterative restoring algorithm that completes in 15 cycles. |
| ThresholdAttention | ScoreAndWeightUnit, Divider15by11 | Top-level module that orchestrates the threshold attention algorithm. It controls the data flow through the ScoreAndWeightUnit and Divider, managing state and accumulating intermediate results. |

Critic → `uarch`；有下一轮执行：`True`。

归因（模型分析，因果结论仍需对照）：The current design is severely latency-limited by the 15-cycle iterative divider, resulting in a max latency of 22 cycles. However, the design has massive area and timing slack, using only 5.7% of the area budget (1718.626 um2 vs 30000 um2) and having a timing slack of 8.04ns on a 10ns clock. This presents a clear opportunity to trade a small amount of the unused area budget for a significant latency and energy reduction by implementing a faster divider.

具体干预：Replace the iterative restoring implementation of the `Divider15by11` module with a faster, multi-stage pipelined or fully combinational divider. A combinational implementation is likely feasible given the large timing slack and would reduce the division stage from 15 cycles to 1. This is expected to decrease the total system latency from 22 cycles to approximately 7 cycles, yielding a superior latency-energy Pareto point.

引用字段：`['evaluation.verification.max_cycles', 'evaluation.area_um2', 'evaluation.slack_ns']`。

### 轮次 2

重入：`uarch`；状态：`evaluated`。

可信 Kernel 分析：`{"config": {"threshold": 64}, "quality_loss": 0.07025641025641026, "quality_metric": "mean absolute output error / 15 vs threshold=0", "quality_scope": "260 deterministic synthetic profiling queries; not model perplexity", "sparsity": 0.31634615384615383, "active_keys_histogram": {"0": 20, "1": 27, "2": 47, "3": 74, "4": 92}, "samples": 260, "seed": 17}`。

完整顶层：`ThresholdAttention`。Compiler 保留的接口/拓扑计划（实现文字可能仍为初始版本；最终流水深度以本轮源码和实测周期为准）：

The design adopts a sequential, iterative architecture to minimize area, which is a key constraint (`max_area_um2`: 30000). The computation is broken down into three main stages controlled by a central FSM: input latching, iterative score/weight calculation, and division. A single `ScoreAndWeightUnit` is instantiated and reused across the four keys, processing one key per cycle. This saves the area of three additional units compared to a fully parallel design. The accumulation of `weight_sum` and `weighted_value_sum` is performed within the top module's control logic. For the division `floor(weighted_value_sum / weight_sum)`, a dedicated iterative restoring divider module (`Divider15by11`) is used, offering a good trade-off between area and latency. It computes a 15-bit quotient from a 15-bit dividend and 11-bit divisor in 15 clock cycles. The total latency is approximately 22 cycles (1 for start, 4 for key processing, 1 for divider setup, 15 for division, 1 for final output), which is well within the 128-cycle budget. Numeric widths are chosen based on the `numeric_bounds` to prevent overflow while minimizing datapath size. The `threshold` value is hardcoded to 64 as specified in the profiling configuration.

| 新生成模块 | 依赖 | 职责 |
|---|---|---|
| ScoreAndWeightUnit |  | Calculates the score for a single key-query pair and applies a threshold to generate the corresponding weight. This is a purely combinational module. |
| Divider15by11 |  | Performs unsigned integer division of a 15-bit dividend by an 11-bit divisor, producing a 15-bit quotient. It uses an iterative restoring algorithm that completes in 15 cycles. |
| ThresholdAttention | ScoreAndWeightUnit, Divider15by11 | Top-level module that orchestrates the threshold attention algorithm. It controls the data flow through the ScoreAndWeightUnit and Divider, managing state and accumulating intermediate results. |

Critic → `uarch`；有下一轮执行：`False`。

归因（模型分析，因果结论仍需对照）：The round 2 design successfully reduced latency from 22 to 7 cycles by parallelizing the divider, establishing a new Pareto-optimal point. However, measurement shows latency is now dominated by the 4-cycle sequential processing of key-query scores. The design has substantial remaining budget, with area usage at only 11% of the constraint (3306.646 um2 vs 30000 um2) and a healthy timing slack of 3.407 ns. This is a clear opportunity to trade abundant area for a significant latency reduction by parallelizing the score calculation.

具体干预：Modify the `ThresholdAttention` microarchitecture to instantiate four `ScoreAndWeightUnit`s. Process all four keys in parallel within a single cycle, replacing the current 4-cycle FSM loop. The outputs (`weight` and `weight*v`) from these four parallel units should be summed using adder trees before the division stage. This change is expected to reduce the computation stage from 4 cycles to 1, lowering the total latency from 7 to approximately 4 cycles and creating a superior latency-energy design point.

引用字段：`['evaluation.verification.max_cycles', 'evaluation.area_um2', 'evaluation.slack_ns']`。

[完整结果](raw/fullstack_17590231/summary.json) · [事件与反馈](raw/fullstack_17590231/events.json)

## 证据使用边界

本记录证明的是指定契约下的系统生成、验证、测量和角色重入。单次变好或变差都不足以证明 Critic 相比无 Critic / 规则 Critic 更有效。下一步应冻结工作负载、初始设计和预算，做多 seed 的有/无 Critic 对照，并增加真实 DynaX 契约和工作负载活动标注。

raw 保留原日志中的绝对路径；它们对应运行时的 scratch 目录。归档的相对目录保持原层次。source 是执行时的冻结源码快照；当前工作区可能有后续兼容性修复，不能反向归算为本次运行的行为。
