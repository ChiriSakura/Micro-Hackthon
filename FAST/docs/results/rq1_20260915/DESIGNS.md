# RQ1 软件配置与生成硬件

## rq1_dynax_xm / 参考库使用审计

已读取：['attention_tile_system_reference', 'low_precision_predictor', 'pipelined_divider', 'topk_selection']。

已分配（包含失败的计划）：['attention_tile_system_reference', 'pipelined_divider', 'topk_selection']。

请求原生链接：[]。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_dynax_xm / round 1

软件配置：`{"n1": 7, "n2": 6, "t0_quarters": 4, "t1_quarters": 0}`。

语言：chisel；顶层：`rq1_dynax_xm_top`。

The system is decomposed into a three-stage pipeline to meet the 300 MHz frequency target, isolating distinct computational steps: score/exponent calculation, dynamic key selection, and final normalization. This modular approach, orchestrated by a top-level controller, allows for clear pipelining and verification. The `ScoreAndExpUnit` computes all 16 scores and their corresponding exponentials in a fixed-latency parallel pipeline. The `SelectionUnit` performs the dynamic X:M selection by first calculating block-level exponential sums to determine the number of keys to retain (k) per block. It then uses a pipelined sorting network, guided by the `topk_selection` reference, to find the top-k scores within each block, correctly implementing the tie-breaking rule. The behavior contract for this module has been corrected to reflect top-k selection as per the UArch feedback. The `NormalizationUnit` computes the final weighted sum and performs the normalization division using a pipelined divider adapted from the `pipelined_divider` library reference to manage its critical path. Numeric widths for all datapaths are derived from the algorithm's `numeric_bounds` to prevent overflow. The overall pipeline latency is 60 cycles, well within the 1024-cycle budget.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreAndExpUnit | Computes all 16 attention scores from Q and K vectors, finds the maximum score, and then calculates the exponential for each key based on the delta from the max. |  |  |
| SelectionUnit | Performs dynamic X:M selection. It computes block-level and total exponential sums, determines the number of keys to keep (k) for each block, and then uses two parallel 8-input sorting networks to find the top-k scores and generate the final 16-bit keep_mask. |  |  |
| NormalizationUnit | Computes the final normalized result. It calculates the denominator D (sum of selected exponentials) and numerator N (sum of selected weighted values), then performs the final scaled division (N*16)/D. |  |  |
| rq1_dynax_xm_top | Top-level wrapper that instantiates and connects the pipeline stages, and manages the overall control flow with a simple FSM based on 'start' and 'done' signals. | ScoreAndExpUnit, SelectionUnit, NormalizationUnit |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The current design's energy efficiency is limited by its high latency of 60 cycles. The physical evaluation shows a cell area of 125.7k um^2, which is only 63% of the 200k um^2 constraint, leaving substantial area budget. The majority of the latency (41 of 60 cycles) is in the NormalizationUnit, due to a conservative 33-cycle pipelined divider. A compiler-level change to enforce a much shorter latency contract on this module will force a trade-off of the available area budget for a significant reduction in latency, leading to a direct and substantial improvement in energy efficiency (queries/Joule).",
  "evidence": [
    "evaluation.verification.mean_cycles",
    "evaluation.area_um2",
    "evaluation.energy_efficiency_queries_per_joule"
  ],
  "instructions": "Revise the system plan to reduce the latency of the `NormalizationUnit` module from 41 cycles to 20 cycles or less. This will require the uarch stage to implement a faster divider, utilizing the available area budget. The expected effect is a reduction in total system latency to ~40 cycles, a proportional decrease in energy per query, and a significant increase in `energy_efficiency_queries_per_joule`."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_dynax_xm / round 2

软件配置：`{"n1": 7, "n2": 6, "t0_quarters": 4, "t1_quarters": 0}`。

## rq1_block_nm / 参考库使用审计

已读取：['attention_tile_system_reference', 'low_precision_predictor', 'pipelined_divider', 'topk_selection']。

已分配（包含失败的计划）：['attention_tile_system_reference', 'pipelined_divider', 'topk_selection']。

请求原生链接：['pipelined_divider', 'topk_selection']。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_block_nm / round 1

软件配置：`{"n": 7}`。

## rq1_global_topk / 参考库使用审计

已读取：['attention_tile_system_reference', 'dynax_exp_reference', 'partial_softmax', 'pipelined_divider', 'topk_selection']。

已分配（包含失败的计划）：['dynax_exp_reference', 'pipelined_divider', 'topk_selection']。

请求原生链接：[]。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_global_topk / round 1

软件配置：`{"k": 14}`。

语言：chisel；顶层：`Rq1GlobalTopk`。

The system is decomposed into a top-level controller and three simple, independently verifiable compute modules. This design addresses previous feedback by localizing complex control flow (state transitions, Top-K selection, and accumulation) into the top module, which does not have a behavior contract. This avoids overly complex behavior expressions that previously exhausted the compiler's budget. The child modules have simple, verifiable contracts.

1.  **`ScoreCalculator`**: A purely combinational MAC unit. The top module serially computes the 16 scores, which is area-efficient and sufficient given that high throughput is not required. The behavior contract vectors are corrected to use `spack` for signed values.

2.  **`ExpAndProd`**: A 2-cycle pipelined module that encapsulates the exponential lookup and the `e*v` product. This isolates the large EXP table ROM. The behavior contract vectors are corrected to properly encode negative integer values.

3.  **`Normalizer`**: A pipelined divider based on the `pipelined_divider` reference, adapted for the specific 32-bit signed numerator and 20-bit unsigned denominator. A 33-cycle latency is chosen to ensure it can meet the 300 MHz frequency target while handling the required bit widths.

4.  **`Rq1GlobalTopk` (Top Module)**: A finite state machine orchestrates the entire process:
    a.  **Score Calculation (16 cycles)**: Calls `ScoreCalculator` for each key and stores the 16 scores in a register file.
    b.  **Selection (17 cycles)**: Finds the maximum score `h` and the indices of the two smallest scores by iterating through the score register file. This implements the Top-k (k=14) selection with correct tie-breaking (smaller index wins for kept items, which means larger index is discarded for tied minimums).
    c.  **Accumulation (18 cycles)**: Iterates through the scores, using `ExpAndProd` to get the exponential `e` and product `e*v`. It accumulates results for the 14 selected keys into `N` and `D` registers, handling the pipeline latency.
    d.  **Normalization (~34 cycles)**: Starts the `Normalizer` with the final `N*16` and `D` values and waits for the result.

This sequential, resource-sharing approach minimizes area and fits comfortably within the 1024-cycle latency budget.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Calculates the dot product score for a single key: s = q[0]*k[0] + q[1]*k[1]. |  |  |
| ExpAndProd | Calculates the exponential of a score delta, and the product of the exponential with a value. |  |  |
| Normalizer | Performs the final division: result = trunc_div(N_shifted, D). |  |  |
| Rq1GlobalTopk | Top-level module that orchestrates the sparse softmax calculation through a state machine, controlling data flow between the compute units. | ScoreCalculator, ExpAndProd, Normalizer |  |

Critic 原始结构化建议：

```json
{
  "layer": "kernel",
  "reason": "The current design with k=14 is feasible and meets all constraints, including a quality_loss of 0.0288 which is well below the 0.05 maximum. However, the measured configuration profiles show that k=15 provides even better quality (quality_loss of 0.0184) while still being comfortably within the constraint. The architectural change to support k=15 (finding one minimum score to discard instead of two) simplifies the selection logic in the top-level FSM. This simplification is expected to yield a small reduction in cell area and power. Since the overall latency is dominated by fixed-latency loops and the divider, it is expected to remain at 85 cycles. A reduction in power at the same latency will directly improve energy efficiency, pushing this design to a better Pareto point.",
  "evidence": [
    "evaluation.quality_loss",
    "evaluation.area_um2",
    "evaluation.energy_efficiency_queries_per_joule"
  ],
  "instructions": "Change the kernel configuration from k=14 to k=15. The compiler must then regenerate the top-level FSM to find and discard only the single minimum score, instead of two. This is expected to improve quality_loss to ~0.0184 and may slightly reduce area and power, thereby increasing energy_efficiency_queries_per_joule.",
  "proposed_config": {
    "k": 15
  }
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_global_topk / round 2

软件配置：`{"k": 15}`。

语言：chisel；顶层：`rq1_global_topk`。

The design implements the rq1_global_topk algorithm using a sequential, multi-pass architecture controlled by a central finite state machine in the top module. This approach prioritizes resource efficiency and simplicity, which is suitable given the task does not require single-cycle throughput. The latency is dominated by sequential processing loops and a pipelined divider, staying well within the 1024-cycle budget. The algorithm is decomposed into three core computational modules: a combinational `ScoreCalculator` for the dot products, a ROM-based `ExpLut`, and a pipelined `FinalDivider`. The Top-K selection for k=15 is implemented within the top-level FSM by finding the single 'loser' key. Numeric widths are chosen based on `numeric_bounds`. This plan corrects a previous attempt by changing the `FinalDivider` implementation strategy. Instead of adapting a native library class, which caused a dependency declaration issue, the divider logic will be inlined into the module, following guidance from the `pipelined_divider` reference. This resolves the UArch feedback.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Calculates the dot product of two 2-element 4-bit signed vectors. |  |  |
| ExpLut | Implements the exponential lookup table. |  |  |
| FinalDivider | Performs the final normalization division: result = trunc_toward_zero((N*16)/D). |  |  |
| rq1_global_topk | Top-level module for the sparse softmax decode-row algorithm. It orchestrates the computation of scores, exponentials, top-k selection, and normalization through a state machine and child modules. | ScoreCalculator, ExpLut, FinalDivider |  |

Critic 原始结构化建议：

```json
{
  "layer": "uarch",
  "reason": "The current design is Pareto-optimal for the explored kernel configurations, but its latency of 83 cycles is dominated by the 32-cycle radix-2 divider. The area (24090 um2) and power (8.46 mW) are very low, leaving significant budget. A microarchitectural change to the divider can trade some of this budget for a large latency reduction. This explores a different point on the energy-latency-area Pareto frontier.",
  "evidence": [
    "evaluation.verification.mean_cycles",
    "evaluation.latency_ns",
    "evaluation.area_um2",
    "evaluation.power_mw"
  ],
  "instructions": "In the `FinalDivider` module, replace the current 32-stage radix-2 restoring divider with a pipelined radix-4 restoring divider. This should approximately halve the divider's latency to ~16-18 cycles, reducing total system latency from 83 to ~67 cycles. This change will increase the divider's area and complexity, but the significant latency reduction is expected to improve the design's position on the energy-latency Pareto front."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_global_topk / round 3

软件配置：`{"k": 15}`。

语言：chisel；顶层：`rq1_global_topk`。

The design implements the rq1_global_topk algorithm using a sequential, multi-pass architecture controlled by a central finite state machine in the top module. This approach prioritizes resource efficiency and simplicity, which is suitable given the task does not require single-cycle throughput. The latency is dominated by sequential processing loops and a pipelined divider, staying well within the 1024-cycle budget. The algorithm is decomposed into three core computational modules: a combinational `ScoreCalculator` for the dot products, a ROM-based `ExpLut`, and a pipelined `FinalDivider`. The Top-K selection for k=15 is implemented within the top-level FSM by finding the single 'loser' key. Numeric widths are chosen based on `numeric_bounds`. This plan corrects a previous attempt by changing the `FinalDivider` implementation strategy. Instead of adapting a native library class, which caused a dependency declaration issue, the divider logic will be inlined into the module, following guidance from the `pipelined_divider` reference. This resolves the UArch feedback.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Calculates the dot product of two 2-element 4-bit signed vectors. |  |  |
| ExpLut | Implements the exponential lookup table. |  |  |
| FinalDivider | Performs the final normalization division: result = trunc_toward_zero((N*16)/D). |  |  |
| rq1_global_topk | Top-level module for the sparse softmax decode-row algorithm. It orchestrates the computation of scores, exponentials, top-k selection, and normalization through a state machine and child modules. | ScoreCalculator, ExpLut, FinalDivider |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The current design's latency of 83 cycles is dominated by the 32-cycle, radix-2 `FinalDivider`. A previous attempt to replace this with a faster divider at the uarch layer was correctly blocked because the compiler's contract for that module specifies a fixed 32-cycle latency. To achieve a latency reduction, the compiler must first be instructed to change this contract. The design has ample area (24108.91 um2 vs 200000 um2 max) and power budget, which can be traded for a significant latency reduction, thus improving the energy-latency Pareto point.",
  "evidence": [
    "evaluation.verification.mean_cycles",
    "evaluation.area_um2",
    "evaluation.power_mw",
    "evaluation.slack_ns"
  ],
  "instructions": "Revise the system plan to target a lower-latency divider. Change the contract for the `FinalDivider` module to specify a latency of approximately 16-18 cycles, which will allow the uarch agent to implement a faster radix-4 divider. The top-level FSM schedule must be updated to accommodate the new divider latency. This is expected to reduce total system latency from 83 cycles to ~67 cycles, improving energy_efficiency_queries_per_joule by reducing the energy-per-query."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_global_topk / round 4

软件配置：`{"k": 15}`。

语言：chisel；顶层：`rq1_global_topk`。

The design addresses the critic's feedback by reducing the system latency. The previous plan's 32-cycle radix-2 divider was identified as the primary latency bottleneck. This revised plan replaces it with a 16-cycle radix-4 divider in the `FinalDivider` module, which is feasible within the given area constraints. The top-level FSM in `rq1_global_topk` is adjusted to accommodate the new 16-cycle latency, reducing the overall system latency from approximately 83 cycles to 67 cycles. This improves the energy-latency Pareto point as requested. The overall architecture remains a sequential, multi-pass FSM-driven design, which is area-efficient and appropriate for the task's throughput requirements. The system is decomposed into three main computational sub-modules: `ScoreCalculator` for dot-products, `ExpLut` for the exponential table, and the newly specified faster `FinalDivider`. Numeric widths are derived from the algorithm's `numeric_bounds` to ensure correctness. This plan is preserved from the `plan_awaiting_reference_review` as it is a sound and compact implementation suitable for the contract, and the newly provided complex reference code (`attention_tile_system_reference`) represents an alternative high-performance architecture that is not required and would be a significant, unnecessary redesign.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Calculates the dot product of two 2-element 4-bit signed vectors. |  |  |
| ExpLut | Implements the exponential lookup table. |  |  |
| FinalDivider | Performs the final normalization division: result = trunc_toward_zero((N*16)/D). |  |  |
| rq1_global_topk | Top-level module for the sparse softmax decode-row algorithm. It orchestrates the computation of scores, exponentials, top-k selection, and normalization through a state machine and child modules. | ScoreCalculator, ExpLut, FinalDivider |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The previous compiler change successfully reduced latency from 83 to 67 cycles by specifying a faster 16-cycle radix-4 divider, yielding a 45% improvement in energy efficiency. However, the resulting physical design is infeasible due to 2 routing DRC violations. This suggests the new, more complex divider logic, while meeting timing, creates minor routability issues. The best intervention is to slightly relax the divider's latency constraint, giving the physical design tools more flexibility to resolve the DRCs and secure a new, feasible Pareto point.",
  "evidence": [
    "evaluation.route_drc_violations",
    "evaluation.verification.mean_cycles",
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.slack_ns"
  ],
  "instructions": "Revise the system plan to change the contract for the `FinalDivider` module, increasing its latency from 16 to 18 cycles. The top-level FSM schedule must be updated to accommodate this. This small increase in total latency (from 67 to 69 cycles) is a deliberate trade-off expected to resolve the DRC violations and yield a feasible design that is significantly more energy-efficient than the last feasible point from Round 3."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_global_topk / round 5

软件配置：`{"k": 15}`。

语言：chisel；顶层：`rq1_global_topk`。

The design addresses the critic's feedback by relaxing the latency constraint on the final divider to improve routability. The previous plan's 16-cycle radix-4 divider, while fast, resulted in DRC violations. This revised plan changes the `FinalDivider` to an 18-cycle pipelined radix-2 implementation. This is expected to resolve the physical design issues. The top-level FSM in `rq1_global_topk` is adjusted to accommodate the new 18-cycle latency, increasing the overall system latency slightly from 67 to 69 cycles. This is a deliberate trade-off to achieve a feasible design, while still representing a significant improvement over the original 83-cycle baseline. The rest of the architecture, a sequential, multi-pass FSM-driven design, remains unchanged as it is area-efficient and appropriate for the task.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Calculates the dot product of two 2-element 4-bit signed vectors. |  |  |
| ExpLut | Implements the exponential lookup table. |  |  |
| FinalDivider | Performs the final normalization division: result = trunc_toward_zero((N*16)/D). |  |  |
| rq1_global_topk | Top-level module for the sparse softmax decode-row algorithm. It orchestrates the computation of scores, exponentials, top-k selection, and normalization through a state machine and child modules. | ScoreCalculator, ExpLut, FinalDivider |  |

Critic 原始结构化建议：

```json
{
  "layer": "stop",
  "reason": "The current design from Round 5 is the best feasible point achieved, establishing a new Pareto-optimal result with an energy efficiency of 697 M queries/Joule. It successfully resolved the DRC violations from the previous round by slightly increasing divider latency (16 to 18 cycles), which also led to unexpected but beneficial reductions in area (19155 um2) and power (6.23 mW). The quality_loss (0.0184) is excellent for the optimal kernel configuration (k=15). With no remaining rounds, further aggressive architectural changes are high-risk and unnecessary. The current design is a successful conclusion to the optimization process.",
  "evidence": [
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.feasible",
    "evaluation.area_um2",
    "evaluation.quality_loss",
    "evaluation.verification.mean_cycles"
  ],
  "instructions": "Halt optimization. The design from Round 5 is the final recommended design, as it represents the best feasible Pareto point discovered, balancing latency, energy efficiency, and area under all constraints."
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

## rq1_sanger_threshold / 参考库使用审计

已读取：['attention_tile_system_reference', 'dynax_exp_reference', 'partial_softmax', 'pipelined_divider']。

已分配（包含失败的计划）：['pipelined_divider']。

请求原生链接：['pipelined_divider']。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_sanger_threshold / round 1

软件配置：`{"threshold_256": 3}`。

