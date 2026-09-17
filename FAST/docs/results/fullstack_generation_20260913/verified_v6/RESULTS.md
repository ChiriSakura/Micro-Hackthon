# 完整系统生成：Chisel / Verilog 集成验证

这是新主线的 bring-up 记录，不是 Critic 消融，也不是两种 HDL 的公平性能比较。

算法为 4-bit threshold-attention：QK 阈值筛选、加权求和、整数归一化。它不等于 DynaX 或 softmax attention。每轮使用独立 Python 参考驱动的 100 个全系统数值用例。

面积为完整生成顶层的 Nangate45 综合单元面积；功耗为 OpenSTA 全局活动率预布局估计，能量为该估计功耗乘以实测周期对应的延迟。没有布局布线或逐网工作负载活动标注。

| 运行 | 轮次 | 语言 | threshold | 验证 | 面积 µm² | 功耗 mW | 延迟 ns | 能量 nJ | slack ns | 可行 |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---|
| fullstack_17591809 | 1 | chisel | 64 | 通过 | 7191.31 | 0.64496 | 190 | 0.122542 | 8.4961 | 是 |
| fullstack_17591809 | 2 | chisel | 64 | 通过 | 5120.77 | 0.410456 | 80 | 0.0328365 | 7.9591 | 是 |

## fullstack_17591809

状态：`budget_exhausted`；参考库完整性：`True`；保留的 Pareto 轮次：`[2]`。

约束与预算：`{"algorithm": "threshold_attention", "prompt": "Design a complete threshold-sparse attention accelerator from q/k/v inputs to normalized output. Analyze the allowed threshold configurations, then co-design the complete datapath and control. Prefer reusable modules; explore energy-latency tradeoffs within measured quality, area and clock constraints.", "constraints": {"max_quality_loss": 0.15, "max_area_um2": 30000, "frequency_mhz": 100}, "max_loops": 2, "compiler_attempts": 3, "module_attempts": 3, "seed": 17, "kernel_profile_budget": 16, "activity": 0.1, "hdl": "chisel", "template_read_budget": 2}`

LLM 调用次数：`{"kernel": 1, "compiler": 6, "uarch": 9, "critic": 2}`。

### 轮次 1

重入：`kernel`；状态：`evaluated`。

可信 Kernel 分析：`{"config": {"threshold": 64}, "quality_loss": 0.07025641025641026, "quality_metric": "mean absolute output error / 15 vs threshold=0", "quality_scope": "260 deterministic synthetic profiling queries; not model perplexity", "sparsity": 0.31634615384615383, "active_keys_histogram": {"0": 20, "1": 27, "2": 47, "3": 74, "4": 92}, "samples": 260, "seed": 17}`。

完整顶层：`ThresholdAttention`。Compiler 保留的接口/拓扑计划（实现文字可能仍为初始版本；最终流水深度以本轮源码和实测周期为准）：

The design implements the threshold_attention algorithm using a 4-stage, feed-forward pipeline to meet the 100 MHz frequency target while maintaining low latency. The architecture is modular, promoting reuse and clarity. Stage 1, managed by the top module's state machine, latches inputs. Stage 2 consists of four parallel 'ScoreUnit' modules, each a single-cycle pipelined MAC, to compute dot-product scores concurrently. Stage 3 is a two-cycle 'AggregationUnit' that thresholds scores, computes weighted values, and sums them using a pipelined adder tree to manage the critical path. Stage 4 employs a pipelined 'UnsignedDivider' for the final normalization, adapted from a reference template. This divider is configured with 15 stages for maximum throughput, resulting in a 15-cycle latency. The total design latency is approximately 19 cycles, which is well within the 128-cycle budget specified in the contract. The fixed threshold from the configuration is hardwired.

| 新生成模块 | 依赖 | Compiler 分配的参考 | 职责 |
|---|---|---|---|
| ScoreUnit |  | — | Computes the dot product score for a single query-key pair: score = q[0]*k[0] + q[1]*k[1]. |
| AggregationUnit |  | — | Thresholds four scores, computes weighted values, and calculates their respective sums ('weight_sum' and 'weighted_value_sum'). |
| UnsignedDivider |  | pipelined_divider | Performs pipelined unsigned integer division: floor(numerator / denominator). |
| ThresholdAttention | ScoreUnit, AggregationUnit, UnsignedDivider | — | Top-level module that orchestrates the attention computation, manages I/O, and controls the overall pipeline flow. |

Critic → `uarch`；有下一轮执行：`True`。

归因（模型分析，因果结论仍需对照）：The design is significantly over-pipelined, resulting in excessive latency and energy consumption that is not justified by the timing constraints. The 15-stage UnsignedDivider is the primary cause of the 19-cycle latency. With a measured slack of 8.5ns on a 10ns clock, the pipeline depth can be drastically reduced to improve latency and energy without violating the frequency target.

具体干预：Modify the UnsignedDivider module to reduce its pipeline depth from 15 stages to 4. The radix-2 algorithm can be grouped to perform multiple bit-steps per stage. This change is expected to reduce latency by approximately 11 cycles and lower both area and energy due to fewer pipeline registers, while the abundant timing slack will ensure the 100 MHz clock constraint is still easily met.

引用字段：`['evaluation.verification.mean_cycles', 'evaluation.timing.slack_ns', 'evaluation.max_frequency_mhz', 'evaluation.area_um2']`。

### 轮次 2

重入：`uarch`；状态：`evaluated`。

可信 Kernel 分析：`{"config": {"threshold": 64}, "quality_loss": 0.07025641025641026, "quality_metric": "mean absolute output error / 15 vs threshold=0", "quality_scope": "260 deterministic synthetic profiling queries; not model perplexity", "sparsity": 0.31634615384615383, "active_keys_histogram": {"0": 20, "1": 27, "2": 47, "3": 74, "4": 92}, "samples": 260, "seed": 17}`。

完整顶层：`ThresholdAttention`。Compiler 保留的接口/拓扑计划（实现文字可能仍为初始版本；最终流水深度以本轮源码和实测周期为准）：

The design implements the threshold_attention algorithm using a 4-stage, feed-forward pipeline to meet the 100 MHz frequency target while maintaining low latency. The architecture is modular, promoting reuse and clarity. Stage 1, managed by the top module's state machine, latches inputs. Stage 2 consists of four parallel 'ScoreUnit' modules, each a single-cycle pipelined MAC, to compute dot-product scores concurrently. Stage 3 is a two-cycle 'AggregationUnit' that thresholds scores, computes weighted values, and sums them using a pipelined adder tree to manage the critical path. Stage 4 employs a pipelined 'UnsignedDivider' for the final normalization, adapted from a reference template. This divider is configured with 15 stages for maximum throughput, resulting in a 15-cycle latency. The total design latency is approximately 19 cycles, which is well within the 128-cycle budget specified in the contract. The fixed threshold from the configuration is hardwired.

| 新生成模块 | 依赖 | Compiler 分配的参考 | 职责 |
|---|---|---|---|
| ScoreUnit |  | — | Computes the dot product score for a single query-key pair: score = q[0]*k[0] + q[1]*k[1]. |
| AggregationUnit |  | — | Thresholds four scores, computes weighted values, and calculates their respective sums ('weight_sum' and 'weighted_value_sum'). |
| UnsignedDivider |  | pipelined_divider | Performs pipelined unsigned integer division: floor(numerator / denominator). |
| ThresholdAttention | ScoreUnit, AggregationUnit, UnsignedDivider | — | Top-level module that orchestrates the attention computation, manages I/O, and controls the overall pipeline flow. |

Critic → `uarch`；有下一轮执行：`False`。

归因（模型分析，因果结论仍需对照）：The previous uarch optimization was highly effective, reducing latency from 19 to 8 cycles and energy by 73%. However, the resulting design is still massively over-pipelined, as shown by the 7.9ns of timing slack on a 10ns clock. The critical path is only 2ns. This indicates that more pipeline stages can be collapsed to further improve the latency-energy Pareto point without violating the timing constraint.

具体干预：Further reduce the pipeline depth of the datapath. Specifically, modify the UnsignedDivider to have 2 pipeline stages instead of the current 4, and modify the AggregationUnit to be a single combinational stage instead of 2. The enormous timing slack will easily accommodate the increased logic delay per stage. This change is expected to reduce latency by 3 cycles and correspondingly lower energy and area due to fewer pipeline registers.

引用字段：`['evaluation.timing.slack_ns', 'evaluation.timing.critical_path_ns', 'evaluation.latency_ns', 'evaluation.energy_nj', 'evaluation.area_um2']`。

[完整结果](raw/fullstack_17591809/summary.json) · [事件与反馈](raw/fullstack_17591809/events.json)

## 证据使用边界

本记录证明的是指定契约下的系统生成、验证、测量和角色重入。单次变好或变差都不足以证明 Critic 相比无 Critic / 规则 Critic 更有效。下一步应冻结工作负载、初始设计和预算，做多 seed 的有/无 Critic 对照，并增加真实 DynaX 契约和工作负载活动标注。

raw 保留原日志中的绝对路径；它们对应运行时的 scratch 目录。归档的相对目录保持原层次。source 是执行时的冻结源码快照；当前工作区可能有后续兼容性修复，不能反向归算为本次运行的行为。
