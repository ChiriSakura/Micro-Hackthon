# RQ1 软件配置与生成硬件

## rq1_dynax_xm / 参考库使用审计

已读取：['attention_tile_system_reference', 'bitonic_sort_network', 'topk_selection', 'verified_rq1_normalization', 'verified_rq1_score_exp']。

已分配（包含失败的计划）：['bitonic_sort_network', 'topk_selection', 'verified_rq1_normalization', 'verified_rq1_score_exp']。

请求原生链接：['verified_rq1_normalization', 'verified_rq1_score_exp']。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_dynax_xm / round 1

软件配置：`{"n1": 8, "n2": 7, "t0_quarters": 2, "t1_quarters": 0}`。

校准＋选参验证集最差 RMSE：0.00236381；最终留出集独立评估，不反馈搜索。

语言：chisel；顶层：`rq1_dynax_xm_Top`。

The system is decomposed into three main pipelined modules corresponding to the major algorithmic steps: Score/Exponential calculation, dynamic X:M Selection, and Normalization. This decomposition leverages two existing, verified hardware modules from the catalog ('verified_rq1_score_exp' and 'verified_rq1_normalization') for the first and third steps, which significantly reduces design effort and risk. These verified modules are instantiated within thin, generated adapter modules ('ScoreAndExpUnit_Adapter', 'NormalizationUnit_Adapter') using 'linked_reference_ids' for native compilation. The core new logic is encapsulated in the 'SelectionUnit' module, which implements the dynamic X:M block-based selection. This unit calculates block-wise exponential sums, determines the number of keys to keep per block (n1=8 or n2=7) based on the specified thresholds (t0_quarters=2, t1_quarters=0), and performs the selection using two parallel, pipelined bitonic sorters. A bitonic sorting network is chosen for its regular, non-data-dependent structure, which is well-suited for a fixed-latency hardware pipeline. The top-level module, 'rq1_dynax_xm_Top', acts as a pipeline controller, instantiating the three units and managing the data flow and valid signal propagation between them. The total system latency is the sum of the latencies of the three pipeline stages. This plan repairs the previous attempt by fixing invalid behavior contracts for the 'ScoreAndExpUnit_Adapter' (by un-nesting the 'max' function calls) and the 'SelectionUnit' (by replacing the overly complex sorter model with a rank-based calculation that fits within the expression language limits).

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreAndExpUnit_Adapter | A thin adapter to instantiate and connect to the verified 'ScoreAndExpUnit' native Chisel module. |  | verified_rq1_score_exp |
| SelectionUnit | Implements the DynaX X:M selection logic. It computes block-wise exponential sums, determines the number of keys to keep for each of two blocks, performs Top-K selection on scores for each block using internal bitonic sorters, and generates the final keep_mask. |  |  |
| NormalizationUnit_Adapter | A thin adapter to instantiate and connect to the verified 'NormalizationUnit' native Chisel module. |  | verified_rq1_normalization |
| rq1_dynax_xm_Top | Top-level wrapper for the sparse softmax system, integrating the score/exp, selection, and normalization units into a single pipeline. | ScoreAndExpUnit_Adapter, SelectionUnit, NormalizationUnit_Adapter |  |

Critic 原始结构化建议：

```json
{
  "layer": "uarch",
  "reason": "The initial design is feasible and meets all constraints, establishing a valid Pareto point. It has a total latency of 60 cycles and a positive timing slack of 0.32ns. The largest latency contributor is the immutable NormalizationUnit (41 cycles). The second largest is the generated SelectionUnit (12 cycles). To improve energy efficiency, this intervention targets a reduction in the SelectionUnit's latency by creating a more aggressive pipeline. The existing timing slack suggests that combining logic stages within the SelectionUnit is likely to succeed while still meeting the 300MHz clock target, directly reducing overall latency and energy per query.",
  "evidence": [
    "evaluation.latency_ns",
    "evaluation.slack_ns",
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.area_um2"
  ],
  "instructions": "Re-implement the 'SelectionUnit' module with a reduced pipeline depth. The current implementation uses a 12-stage pipeline, including a 6-stage bitonic sorter. Reduce the sorter's pipeline depth to 3 stages by combining comparator logic into fewer, more complex combinational stages. The target latency for the entire SelectionUnit should be 9 cycles (4 for sums + 3 for sort + 2 for mask/output). This is expected to reduce total system latency from 60 to 57 cycles, improving energy_efficiency_queries_per_joule. A minor area increase is acceptable given the current headroom.",
  "target_modules": [
    "SelectionUnit"
  ]
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

## rq1_dynax_xm / round 2

软件配置：`{"n1": 8, "n2": 7, "t0_quarters": 2, "t1_quarters": 0}`。

校准＋选参验证集最差 RMSE：0.00236381；最终留出集独立评估，不反馈搜索。

语言：chisel；顶层：`rq1_dynax_xm_Top`。

The system is decomposed into three main pipelined modules corresponding to the major algorithmic steps: Score/Exponential calculation, dynamic X:M Selection, and Normalization. This decomposition leverages two existing, verified hardware modules from the catalog ('verified_rq1_score_exp' and 'verified_rq1_normalization') for the first and third steps, which significantly reduces design effort and risk. These verified modules are instantiated within thin, generated adapter modules ('ScoreAndExpUnit_Adapter', 'NormalizationUnit_Adapter') using 'linked_reference_ids' for native compilation. The core new logic is encapsulated in the 'SelectionUnit' module, which implements the dynamic X:M block-based selection. This unit calculates block-wise exponential sums, determines the number of keys to keep per block (n1=8 or n2=7) based on the specified thresholds (t0_quarters=2, t1_quarters=0), and performs the selection using two parallel, pipelined bitonic sorters. A bitonic sorting network is chosen for its regular, non-data-dependent structure, which is well-suited for a fixed-latency hardware pipeline. The top-level module, 'rq1_dynax_xm_Top', acts as a pipeline controller, instantiating the three units and managing the data flow and valid signal propagation between them. The total system latency is the sum of the latencies of the three pipeline stages. This plan repairs the previous attempt by fixing invalid behavior contracts for the 'ScoreAndExpUnit_Adapter' (by un-nesting the 'max' function calls) and the 'SelectionUnit' (by replacing the overly complex sorter model with a rank-based calculation that fits within the expression language limits).

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreAndExpUnit_Adapter | A thin adapter to instantiate and connect to the verified 'ScoreAndExpUnit' native Chisel module. |  | verified_rq1_score_exp |
| SelectionUnit | Implements the DynaX X:M selection logic. It computes block-wise exponential sums, determines the number of keys to keep for each of two blocks, performs Top-K selection on scores for each block using internal bitonic sorters, and generates the final keep_mask. |  |  |
| NormalizationUnit_Adapter | A thin adapter to instantiate and connect to the verified 'NormalizationUnit' native Chisel module. |  | verified_rq1_normalization |
| rq1_dynax_xm_Top | Top-level wrapper for the sparse softmax system, integrating the score/exp, selection, and normalization units into a single pipeline. | ScoreAndExpUnit_Adapter, SelectionUnit, NormalizationUnit_Adapter |  |

Critic 原始结构化建议：

```json
{
  "layer": "kernel",
  "reason": "The current design is infeasible, failing to meet the 300MHz timing constraint (slack: -0.073ns). This regression occurred after a microarchitectural change intended to reduce latency. Instead of attempting another risky, targeted uarch change, this intervention proposes a cross-layer optimization at the kernel level. The current configuration (n1=8, n2=7) provides extremely high quality (0.24% loss) but very low sparsity (1.6%). There is significant quality margin available to trade for PPA improvements. By selecting a pre-profiled configuration with higher sparsity, we anticipate a reduction in switching activity and power, particularly in the large NormalizationUnit. This power reduction can also alleviate routing congestion and timing pressure, likely resolving the timing failure and leading to a new, feasible, and more energy-efficient Pareto point.",
  "evidence": [
    "evaluation.feasible",
    "evaluation.slack_ns",
    "profile.selection_quality_loss",
    "profile.sparsity"
  ],
  "instructions": "Change the kernel configuration to n1=7, n2=4, t0_quarters=2, t1_quarters=0. This configuration has a measured quality loss of 3.8%, which is well within the 5% constraint. Its measured sparsity of 17.4% is over 10x higher than the current configuration's, which is expected to reduce overall power consumption and help achieve timing closure.",
  "proposed_config": {
    "n1": 7,
    "n2": 4,
    "t0_quarters": 2,
    "t1_quarters": 0
  }
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

## rq1_dynax_xm / round 3

软件配置：`{"n1": 7, "n2": 4, "t0_quarters": 2, "t1_quarters": 0}`。

失败记录：Compiler/UArch build budget exhausted; see compiler_feedback.json

校准＋选参验证集最差 RMSE：0.038341；最终留出集独立评估，不反馈搜索。

本候选失败，恢复 R1；Critic 测量证据来自 R1，不是本轮新 PPA。


Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The previous attempt (design_attempt 3) to change the kernel configuration failed due to repeated build failures within the `SelectionUnit` module, as detailed in the `failed_candidate` feedback. The root cause is a defective compiler plan for this module, involving incorrect sorter logic and conflicting tie-breaking rules. The system has rolled back to the feasible but less efficient Round 1 design. To unblock further optimization and fix this latent bug, the most effective intervention is to instruct the compiler to correct its internal plan for the `SelectionUnit` module, while preserving the definitions of the other verified modules.",
  "evidence": [
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.quality_loss",
    "evaluation.slack_ns"
  ],
  "instructions": "Regenerate the system plan. The definition for the 'SelectionUnit' module must be corrected to fix the internal sorter implementation. The sorter must be a correctly pipelined network where each stage's logic only depends on the registered output of the immediately preceding stage. The tie-breaking logic must be fixed to select the SMALLER original index on a score tie, as per the algorithm specification. The definitions for 'ScoreAndExpUnit_Adapter' and 'NormalizationUnit_Adapter' must be preserved exactly as they are."
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

## rq1_dynax_xm / round 4

软件配置：`{"n1": 8, "n2": 7, "t0_quarters": 2, "t1_quarters": 0}`。

校准＋选参验证集最差 RMSE：0.00236381；最终留出集独立评估，不反馈搜索。

语言：chisel；顶层：`rq1_dynax_xm_Top`。

This plan repairs the previously rejected design by addressing two key issues. First, the behavior contract for `ScoreAndExpUnit_Adapter` is corrected by un-nesting the deeply nested `max` function calls into a pipelined reduction tree within the `let` block, resolving the expression parser error. Second, and more critically, the `SelectionUnit` module is redesigned to be correct and verifiable. The previous plan's behavior contract for this module was overly complex and contained logical errors in the tie-breaking implementation. The new `SelectionUnit` has a clear, declarative behavior contract based on a correct rank calculation that strictly adheres to the algorithm's tie-breaking rule (smaller original index wins). The implementation prompt for `SelectionUnit` now explicitly requires a correctly pipelined bitonic sorting network, addressing the implementation flaws noted in previous failed attempts. The verified `ScoreAndExpUnit` and `NormalizationUnit` modules are preserved via thin adapters as instructed. The top-level module integrates these components, adjusting pipeline delays to accommodate the corrected `SelectionUnit` latency, resulting in a robust and verifiable system plan.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreAndExpUnit_Adapter | A thin adapter to instantiate and connect to the verified 'ScoreAndExpUnit' native Chisel module. |  | verified_rq1_score_exp |
| SelectionUnit | Implements the DynaX X:M selection logic. It computes block-wise exponential sums, determines the number of keys to keep for each of two blocks, performs Top-K selection on scores for each block using internal sorters, and generates the final keep_mask. |  |  |
| NormalizationUnit_Adapter | A thin adapter to instantiate and connect to the verified 'NormalizationUnit' native Chisel module. |  | verified_rq1_normalization |
| rq1_dynax_xm_Top | Top-level wrapper for the sparse softmax system, integrating the score/exp, selection, and normalization units into a single pipeline. | ScoreAndExpUnit_Adapter, SelectionUnit, NormalizationUnit_Adapter |  |

Critic 原始结构化建议：

```json
{
  "layer": "kernel",
  "reason": "The current design is a feasible baseline with very high quality (0.24% loss) and low sparsity (1.6%). A previously attempted kernel change to improve efficiency failed due to a now-fixed compiler bug in the `SelectionUnit`. We can now retry a kernel change to trade the significant available quality margin for better energy efficiency. The proposed configuration increases sparsity by over 10x, which is expected to substantially reduce dynamic power in the normalization stage and improve the energy_efficiency_queries_per_joule Pareto point.",
  "evidence": [
    "profile.quality_loss",
    "profile.sparsity",
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.slack_ns"
  ],
  "instructions": "Change the kernel configuration to n1=7, n2=4, t0_quarters=2, t1_quarters=0. This configuration has a measured quality loss of ~3.8%, which is well within the 5% constraint. The significantly higher sparsity (17.4%) is expected to reduce overall power consumption and improve energy efficiency, establishing a new Pareto-optimal design.",
  "proposed_config": {
    "n1": 7,
    "n2": 4,
    "t0_quarters": 2,
    "t1_quarters": 0
  }
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_dynax_xm / round 5

软件配置：`{"n1": 7, "n2": 4, "t0_quarters": 2, "t1_quarters": 0}`。

校准＋选参验证集最差 RMSE：0.038341；最终留出集独立评估，不反馈搜索。

语言：chisel；顶层：`Rq1DynaXm`。

This plan corrects the `rejected_plan` by addressing the root causes of failure identified in `failed_design_candidates` and `response_errors`. The primary issue was in the `DynaX_SelectionUnit`, which had a functionally incorrect sorting network and a behavior contract that violated the 256-expression limit. This plan replaces the defective sorter with a standard, correctly implemented 6-stage pipelined odd-even merge sort network for each 8-key block. The new `behavior` contract for this module accurately models this correct sorter, respects the 'smaller index wins' tie-breaking rule from the algorithm spec, and stays within the expression limit. Additionally, the invalid nested `max` function in the `ScoreAndExpUnit_rq1` behavior contract is replaced with a valid tree of 2-input `max` calls, modeling the hardware correctly. The overall three-stage pipeline architecture, leveraging the verified native modules `verified_rq1_score_exp` and `verified_rq1_normalization`, is preserved to ensure a robust and synthesizable system.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreAndExpUnit_rq1 | Adapter for the verified native `ScoreAndExpUnit` module. This module computes attention scores and their corresponding exponentials. |  | verified_rq1_score_exp |
| DynaX_SelectionUnit | Implements the DynaX X:M selection logic. It computes block mass, applies thresholds to determine how many keys to keep (n1=7 or n2=4), and sorts the scores within each block to select the top candidates, generating a final keep_mask. This module corrects the tie-breaking and sorter implementation defects from previous attempts. |  |  |
| NormalizationUnit_rq1 | Adapter for the verified native `NormalizationUnit` module. This module performs the final normalization step. |  | verified_rq1_normalization |
| Rq1DynaXm | Top-level wrapper for the sparse softmax system, integrating score/exponentiation, selection, and normalization modules. It manages the overall pipeline, data alignment, and I/O protocol. | ScoreAndExpUnit_rq1, DynaX_SelectionUnit, NormalizationUnit_rq1 |  |

Critic 原始结构化建议：

```json
{
  "layer": "uarch",
  "reason": "The current design is feasible with a healthy timing slack of 0.406 ns and represents a new Pareto-optimal point. The `DynaX_SelectionUnit` contributes 7 cycles to the total 56-cycle latency. To further improve energy efficiency, this intervention targets reducing the latency of this module. By combining logic from adjacent pipeline stages, we can attempt to reduce its latency to 6 cycles. This would decrease the total system latency to 55 cycles, directly improving both latency and energy_efficiency_queries_per_joule. This is a bounded microarchitectural change that preserves the module's interface and functionality.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.latency_ns",
    "evaluation.energy_efficiency_queries_per_joule"
  ],
  "instructions": "Re-implement the `DynaX_SelectionUnit` module with a reduced pipeline depth of 6 cycles, down from 7. Combine logic from adjacent stages in the sorter and/or thresholding paths to reduce the number of registers. The existing timing slack of 0.406ns suggests this more aggressive pipeline has a reasonable chance of meeting the 300MHz clock constraint. This change is expected to reduce overall system latency and improve energy efficiency.",
  "target_modules": [
    "DynaX_SelectionUnit"
  ]
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

## rq1_block_nm / 参考库使用审计

已读取：['attention_tile_system_reference', 'dynax_exp_reference', 'execution_pe', 'pipelined_divider', 'topk_selection']。

已分配（包含失败的计划）：['pipelined_divider']。

请求原生链接：['pipelined_divider']。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_block_nm / round 1

软件配置：`{"n": 7}`。

语言：chisel；顶层：`Rq1BlockNmTop`。

The design implements the rq1_block_nm algorithm using a pipelined, state-machine-driven architecture. The algorithm is decomposed into sequential stages: score calculation, max-score/delta/exponentiation, key selection, accumulation, and final division. This sequential flow is managed by a single finite state machine in the top module, which is area and energy-efficient for this non-streaming, single-query task. The total latency is dominated by the sequential processing of 16 keys for score calculation and accumulation, and the pipelined division, staying well within the 1024-cycle budget.

Key components are:
1.  **Score Calculation:** A MAC unit computes one signed 9-bit score per cycle for 16 cycles. The scores are stored in a register file.
2.  **Max/Exp/Select:** A parallel, combinational stage finds the maximum score, calculates deltas, looks up 16 exponential values from a ROM, and computes the `keep_mask`.
3.  **Sparsity:** The `keep_mask` is generated by two instances of a custom combinational `FindMin8` module. This module identifies the single score to discard from each 8-key block, correctly implementing the 7-of-8 selection with the specified tie-breaking rule (discarding the element with the larger index in case of a tie). This is more area-efficient than a generic sorter.
4.  **Accumulation:** A pipelined accumulator calculates the numerator `N` (s28) and denominator `D` (u20) over 16 cycles, based on the `keep_mask`.
5.  **Division:** A `DividerWrapper` module adapts the provided `pipelined_divider` library component. It is configured to perform the final `trunc_toward_zero((N*16)/D)` operation as a `s32 / u20 -> s16` division with a latency of 33 cycles.

Numeric widths are chosen based on the algorithm's `numeric_bounds` to ensure no overflow occurs during intermediate calculations while minimizing area. The modular approach promotes reuse and isolates complex logic. This plan corrects errors from a previous attempt, specifically by moving test vectors into the behavior contract and refining the divider wrapper's implementation to correctly match the required arithmetic operation.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| FindMin8 | Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard. |  |  |
| DividerWrapper | A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result. |  | pipelined_divider |
| Rq1BlockNmTop | Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation. | FindMin8, DividerWrapper |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The current design is functionally correct and meets area constraints, but fails timing with a large negative slack of -3.1 ns at the target 300 MHz frequency. The root cause is an excessively long combinational path in the `FINALIZE_EXP` state of the `Rq1BlockNmTop` module. This single cycle attempts to find the max score across 16 values, calculate 16 deltas, perform 16 parallel table lookups, and compute the keep mask using two `FindMin8` comparator trees. This logic is too complex to execute in a single 3.33 ns cycle.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.feasible",
    "evaluation.area_um2"
  ],
  "instructions": "Revise the system plan for `Rq1BlockNmTop`. The logic in the current single-cycle `FINALIZE_EXP` state must be pipelined across multiple clock cycles. A potential schedule is: Stage 1: Find max score `h`. Stage 2: Calculate deltas `h-s[i]` and perform EXP table lookups. Stage 3: Compute the `keep_mask` using the `FindMin8` modules. This will break the critical path and allow the design to meet timing, at the cost of a small, acceptable increase in total latency. The `FindMin8` and `DividerWrapper` module definitions can be reused as-is."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_block_nm / round 2

软件配置：`{"n": 7}`。

语言：chisel；顶层：`Rq1BlockNmTop`。

The design addresses the timing failure reported by the critic by pipelining the previously long combinational logic for max-score finding, exponentiation, and mask generation. The original single-cycle `FINALIZE_EXP` state is replaced with a two-stage pipeline (`PIPE_S1_MAX_MASK` and `PIPE_S2_EXP`) within the top-level FSM. Stage 1 computes the max score and the keep mask in parallel. Stage 2 computes the deltas and performs the exponential lookups. This change breaks the critical path, allowing the design to meet the 300 MHz frequency target with a minimal and acceptable increase in latency. The overall architecture remains a state-machine-driven, sequential pipeline, which is area- and energy-efficient for the single-query task. The `FindMin8` and `DividerWrapper` modules from the previous plan are preserved unchanged as they are functionally correct and not on the critical path.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| FindMin8 | Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard. |  |  |
| DividerWrapper | A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result. |  | pipelined_divider |
| Rq1BlockNmTop | Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation. | FindMin8, DividerWrapper |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The current design is functionally correct and meets area/quality constraints, but fails the 300 MHz timing constraint with a negative slack of -1.816 ns. The previous compiler intervention successfully pipelined the design and improved slack from -3.1 ns, but it was insufficient. The remaining critical path is likely within the `Rq1BlockNmTop` module's `PIPE_S1_MAX_MASK` state, which computes the 16-input max score and the 16-bit keep_mask in parallel. This concentration of deep combinational logic still violates the timing budget.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.feasible",
    "evaluation.area_um2",
    "evaluation.power_mw"
  ],
  "instructions": "Revise the system plan for `Rq1BlockNmTop` to further decompose the logic currently in the `PIPE_S1_MAX_MASK` and `PIPE_S2_EXP` states. Split this into three sequential single-cycle stages: 1. A `PIPE_S1_MAX` stage to find the max score `h`. 2. A `PIPE_S2_MASK` stage to compute the `keep_mask`. 3. A `PIPE_S3_EXP` stage to calculate deltas `h - s[i]` and perform exponential lookups. This will increase latency by two cycles but isolates the complex combinational paths for max-finding, mask generation, and exponentiation, and is expected to resolve the timing failure. Preserve the `FindMin8` and `DividerWrapper` module definitions."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_block_nm / round 3

软件配置：`{"n": 7}`。

语言：chisel；顶层：`Rq1BlockNmTop`。

The design addresses the timing failure reported by the critic by further pipelining the top-level FSM. The previous plan's single `PIPE_S1_MAX_MASK` stage, which computed the max score and keep mask in parallel, and the subsequent `PIPE_S2_EXP` stage, still contained too much combinational logic to meet the 300 MHz target. Following the critic's instruction, this logic is now split into three sequential single-cycle stages: `PIPE_S1_MAX` (finds max score `h`), `PIPE_S2_MASK` (computes `keep_mask`), and `PIPE_S3_EXP` (computes deltas and performs exponential lookups). This decomposition breaks the critical path by isolating the max-finding, mask generation, and exponentiation logic into separate pipeline stages, each with a shallower combinational depth. This change increases the total latency by one cycle to approximately 70 cycles, which is an acceptable trade-off to resolve the timing violation. The `FindMin8` and `DividerWrapper` modules from the previous plan are preserved unchanged as they are functionally correct and were not on the critical path.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| FindMin8 | Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard. |  |  |
| DividerWrapper | A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result. |  | pipelined_divider |
| Rq1BlockNmTop | Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, which is pipelined to meet timing constraints, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation. | FindMin8, DividerWrapper |  |

Critic 原始结构化建议：

```json
{
  "layer": "uarch",
  "reason": "The design is functionally correct but fails the 300 MHz timing constraint with a slack of -1.804 ns. Pipelining interventions in rounds 2 and 3 improved slack from an initial -3.1 ns but have now stalled, indicating the critical path has moved. The current bottleneck is likely the single-cycle multiplication (`16-bit * 8-bit`) and 28-bit accumulation within the `ACCUMULATE` state of the `Rq1BlockNmTop` module.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.feasible",
    "evaluation.area_um2",
    "evaluation.power_mw"
  ],
  "instructions": "Revise the microarchitecture of the `Rq1BlockNmTop` module. The logic within the 16-cycle `ACCUMULATE` state must be pipelined. Split the operation into two stages: 1) Compute the product `e[i] * v[i]` and register the result. 2) Add the registered product to the numerator accumulator `N`. The denominator accumulation can be performed in stage 1. This will change the `ACCUMULATE` loop to take 32 cycles instead of 16, increasing total latency by ~16 cycles. This is an acceptable trade-off to fix the timing violation.",
  "target_modules": [
    "Rq1BlockNmTop"
  ]
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_block_nm / round 4

软件配置：`{"n": 7}`。

语言：chisel；顶层：`Rq1BlockNmTop`。

The design addresses the timing failure reported by the critic by further pipelining the top-level FSM. The previous plan's single `PIPE_S1_MAX_MASK` stage, which computed the max score and keep mask in parallel, and the subsequent `PIPE_S2_EXP` stage, still contained too much combinational logic to meet the 300 MHz target. Following the critic's instruction, this logic is now split into three sequential single-cycle stages: `PIPE_S1_MAX` (finds max score `h`), `PIPE_S2_MASK` (computes `keep_mask`), and `PIPE_S3_EXP` (computes deltas and performs exponential lookups). This decomposition breaks the critical path by isolating the max-finding, mask generation, and exponentiation logic into separate pipeline stages, each with a shallower combinational depth. This change increases the total latency by one cycle to approximately 70 cycles, which is an acceptable trade-off to resolve the timing violation. The `FindMin8` and `DividerWrapper` modules from the previous plan are preserved unchanged as they are functionally correct and were not on the critical path.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| FindMin8 | Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard. |  |  |
| DividerWrapper | A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result. |  | pipelined_divider |
| Rq1BlockNmTop | Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, which is pipelined to meet timing constraints, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation. | FindMin8, DividerWrapper |  |

Critic 原始结构化建议：

```json
{
  "layer": "uarch",
  "reason": "The design fails timing with a large negative slack of -1.677 ns. The post-route timing report shows a critical path with over 50 logic levels, which is inconsistent with the heavily pipelined system plan. The path starts from logic associated with the `PIPE_S2_MASK` stage and ends at the `h_reg` register, which should be computed in the preceding `PIPE_S1_MAX` stage. This backward-in-pipeline combinational path indicates a severe flaw in the RTL implementation where the intended pipeline separation between these two stages is not present. Previous interventions have failed to address this root cause.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.timing_diagnosis.report_excerpt",
    "evaluation.timing_diagnosis.endpoint_mapping"
  ],
  "instructions": "Correct the microarchitecture of `Rq1BlockNmTop` to properly enforce the pipeline boundary between the `PIPE_S1_MAX` and `PIPE_S2_MASK` states. The logic for finding the max score (`h`) must be purely dependent on the score registers (`s_reg`) and must not have any combinational dependency on the logic that computes the `keep_mask`. Ensure that `h_reg` is registered at the end of the `PIPE_S1_MAX` cycle and that the `FindMin8` modules in the `PIPE_S2_MASK` cycle operate in a separate clock cycle without any combinational path back to the `h_reg` calculation. The current `system_plan` correctly describes this separation; the error is in the RTL implementation which must be fixed.",
  "target_modules": [
    "Rq1BlockNmTop"
  ]
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_block_nm / round 5

软件配置：`{"n": 7}`。

语言：chisel；顶层：`Rq1BlockNmTop`。

The design addresses the timing failure reported by the critic by further pipelining the top-level FSM. The previous plan's single `PIPE_S1_MAX_MASK` stage, which computed the max score and keep mask in parallel, and the subsequent `PIPE_S2_EXP` stage, still contained too much combinational logic to meet the 300 MHz target. Following the critic's instruction, this logic is now split into three sequential single-cycle stages: `PIPE_S1_MAX` (finds max score `h`), `PIPE_S2_MASK` (computes `keep_mask`), and `PIPE_S3_EXP` (computes deltas and performs exponential lookups). This decomposition breaks the critical path by isolating the max-finding, mask generation, and exponentiation logic into separate pipeline stages, each with a shallower combinational depth. This change increases the total latency by one cycle to approximately 70 cycles, which is an acceptable trade-off to resolve the timing violation. The `FindMin8` and `DividerWrapper` modules from the previous plan are preserved unchanged as they are functionally correct and were not on the critical path.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| FindMin8 | Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard. |  |  |
| DividerWrapper | A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result. |  | pipelined_divider |
| Rq1BlockNmTop | Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, which is pipelined to meet timing constraints, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation. | FindMin8, DividerWrapper |  |

Critic 原始结构化建议：

```json
{
  "layer": "uarch",
  "reason": "The design fails timing with a large negative slack of -1.853 ns. The post-route timing report shows a critical path with an extremely high number of logic levels. The path starts from a register related to the score inputs of the `FindMin8` module and ends at the `h_reg` (max score register). This indicates a combinational path exists between the logic for the `PIPE_S2_MASK` state and the `PIPE_S1_MAX` state, which violates the intended pipeline structure described in the system plan. This issue was identified in the previous round but has not been successfully fixed.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.timing_diagnosis.report_excerpt",
    "evaluation.timing_diagnosis.endpoint_mapping"
  ],
  "instructions": "Correct the microarchitecture of `Rq1BlockNmTop` to properly enforce the pipeline boundary between the `PIPE_S1_MAX` and `PIPE_S2_MASK` states. The logic for finding the max score (`h`) must be purely dependent on the score registers (`s_reg`) and must not have any combinational dependency on the logic that computes the `keep_mask`. Ensure that `h_reg` is registered at the end of the `PIPE_S1_MAX` cycle and that the `FindMin8` modules in the `PIPE_S2_MASK` cycle operate in a separate clock cycle without any combinational path back to the `h_reg` calculation. The current `system_plan` correctly describes this separation; the error is in the RTL implementation which must be fixed.",
  "target_modules": [
    "Rq1BlockNmTop"
  ]
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

## rq1_sanger_threshold / 参考库使用审计

已读取：['dynax_exp_reference', 'pipelined_divider', 'sanger_official_mask', 'sanger_official_pack', 'sanger_official_sparse_pe']。

已分配（包含失败的计划）：['dynax_exp_reference', 'pipelined_divider']。

请求原生链接：['pipelined_divider']。读取或分配不证明正确复用；成功设计的链接见逐轮计划。

## rq1_sanger_threshold / round 1

软件配置：`{"threshold_256": 3}`。

语言：chisel；顶层：`SangerThresholdTop`。

This plan repairs a previous design by addressing a contract error. The core architecture remains a 4-stage pipeline (Score, Max/Exp/Threshold, Accumulate, Normalize) to meet the 300 MHz frequency target by breaking down the algorithm into smaller, pipelined modules. The total latency is 22 cycles.

Key fixes from previous feedback cycles, which are preserved here, include:
1.  **Corrected Behavior Contracts:** The behavior contracts for all modules now use correct `spack`/`pack` conventions for signed/unsigned values and have guards for out-of-bounds operations (e.g., LUT lookups).
2.  **Consistent Packing:** The `keep_mask` packing convention is now consistent (LSB=index 0) across `MaxExpAndThreshold`, `Accumulator`, and the top-level port, resolving a previous ambiguity.
3.  **Numerical Correctness:** The `ScoreArray` implementation specifies widening addition (`+&`) to prevent overflow, a fix from a previous RTL bug.

The specific fix in this plan is for the `Normalizer` module:
*   The `tests` field has been removed, as it is redundant and was causing errors when a `behavior` contract is present. The runner will now correctly generate the test vectors from the `behavior` contract, which accurately models the `trunc_div` arithmetic. This resolves the previous conflict between the contract and incorrect, manually-specified test values.

The `Normalizer` module remains a thin adapter around the `pipelined_divider` library component, which is linked directly to ensure use of a verified, efficient hardware divider.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreArray | Calculates 16 parallel dot-product scores from the query and key vectors. |  |  |
| MaxExpAndThreshold | Finds the max score, computes exponentials via a LUT, and applies the Sanger threshold. |  |  |
| Accumulator | Accumulates the numerator (N) and denominator (D) for normalization based on the keep_mask. |  |  |
| Normalizer | Performs the final normalization division. |  | pipelined_divider |
| SangerThresholdTop | Top-level wrapper that integrates all sub-modules and manages the system's control flow and I/O. | ScoreArray, MaxExpAndThreshold, Accumulator, Normalizer |  |

Critic 原始结构化建议：

```json
{
  "layer": "kernel",
  "reason": "The first design is feasible and meets all constraints, establishing a baseline on the Pareto frontier. The next logical step is to explore a different point on the quality-energy tradeoff curve. The measured profile for a `threshold_256` of 2 shows a significant quality improvement (quality_loss from 0.038 to 0.024), while remaining well within the 0.05 constraint. This change will likely increase dynamic power and energy due to lower sparsity (from 0.38 to 0.32), but measuring this new point is critical for mapping the Pareto frontier.",
  "evidence": [
    "evaluation.quality_loss",
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.area_um2"
  ],
  "instructions": "Propose a new design with the kernel configuration `threshold_256: 2`. This is expected to improve quality by reducing the quality_loss metric. This will also decrease average sparsity, which is hypothesized to increase dynamic power consumption in the Accumulator module, leading to a potential decrease in energy efficiency. This exploration is necessary to map the trade-off between quality and energy efficiency.",
  "proposed_config": {
    "threshold_256": 2
  }
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_sanger_threshold / round 2

软件配置：`{"threshold_256": 2}`。

语言：chisel；顶层：`rq1_sanger_threshold`。

The system is decomposed into a linear, fully-pipelined datapath to meet the 300 MHz frequency target and simplify control. The five stages are: Score Generation, Exponential Calculation, Thresholding, Sparse Accumulation, and Normalization. Each stage is a dedicated module with a fixed, predictable latency. This plan repairs the previous attempt by correcting errors in behavior contracts and pipeline timing. Specifically, a test vector in the `Normalizer` contract is fixed to use correct syntax for negative numbers. The pipeline delay for the `keep_mask` in the top module is corrected from 37 to 36 cycles. For the `ScoreGen` module, which previously failed verification, the implementation hint is retained to promote a more robust coding style (decomposing wide inputs) to mitigate potential toolchain issues, while its behavior contract remains unchanged as it correctly reflects the algorithm's mathematics. The total latency is 42 cycles from start to done.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreGen | Computes 16 dot-product scores in parallel from the query vector q and key matrix k. |  |  |
| ExpStage | Finds the maximum score, calculates deltas h-s_i, and looks up the exponential values e_i from a ROM. |  |  |
| Threshold | Calculates the total sum of exponentials 'S' and determines the 'keep_mask' based on the Sanger threshold. |  |  |
| Accum | Accumulates sparse numerator 'N' and denominator 'D' based on the 'keep_mask'. |  |  |
| Normalizer | Performs the final normalization division result = trunc((N*16)/D). |  | pipelined_divider |
| rq1_sanger_threshold | Top-level module that integrates the full sparse softmax datapath and manages the I/O protocol according to the algorithm contract. | ScoreGen, ExpStage, Threshold, Accum, Normalizer |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The current design (Round 2) shows a severe regression in latency (42 vs 22 cycles) and energy efficiency (278M vs 585M queries/Joule) compared to the previous design (Round 1), despite an improvement in quality. The root cause is a change in the system pipeline structure, specifically the `Normalizer` module's latency increasing from 8 to 33 cycles. This makes the current design Pareto-dominated by the Round 1 design. The intervention aims to recover the superior PPA of the Round 1 architecture.",
  "evidence": [
    "evaluation.latency_ns",
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.area_um2"
  ],
  "instructions": "Revise the system plan to reduce the overall pipeline latency. The primary target for latency reduction is the `Normalizer` module, which increased from 8 cycles in Round 1 to 33 cycles in the current design. Propose a new pipeline schedule with a total latency closer to the 22 cycles achieved in Round 1, for example by configuring the `FixedPointDivPipelined` with fewer stages (e.g., 8 stages). This is expected to significantly improve latency and energy efficiency, restoring the PPA performance of the previous round's architecture."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_sanger_threshold / round 3

软件配置：`{"threshold_256": 2}`。

失败记录：RuntimeError: Compiler/UArch build budget exhausted; see compiler_feedback.json

本候选失败，恢复 R1；Critic 测量证据来自 R1，不是本轮新 PPA。


Critic 原始结构化建议：

```json
{
  "layer": "kernel",
  "reason": "The previous round's attempt to build a low-latency design for the `threshold_256: 2` configuration failed due to exhausting the module build budget. The failure analysis points to a persistent test vector issue in the `ExpStage` module, not a fundamental architectural flaw. To make forward progress and explore a different point on the Pareto frontier while the toolchain issue is implicitly addressed, this intervention proposes a new kernel configuration. According to `measured_config_profiles`, `threshold_256: 1` offers the highest quality (loss=0.0096) and is a valid, unexplored point. This allows the system to gather data on a new design point rather than retrying a build that has repeatedly failed due to non-RTL issues.",
  "evidence": [
    "evaluation.energy_efficiency_queries_per_joule",
    "evaluation.latency_ns",
    "profile.quality_loss"
  ],
  "instructions": "Propose a new design with the kernel configuration `threshold_256: 1`. This is expected to yield the highest quality design yet, at the cost of potentially higher energy due to lower sparsity. The compiler should reuse the efficient 22-cycle pipeline architecture from the successful Round 1 design to implement this new configuration, avoiding the high-latency architecture from Round 2.",
  "proposed_config": {
    "threshold_256": 1
  }
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_sanger_threshold / round 4

软件配置：`{"threshold_256": 1}`。

语言：chisel；顶层：`rq1_sanger_threshold_top`。

The system is designed as a deep pipeline to maximize throughput and clock frequency, breaking down the algorithm into four main stages: score calculation, softmax operations, key selection/accumulation, and final normalization. This decomposition allows each stage to be implemented as a specialized module with manageable complexity. The previous plan failed due to a subtle bug in the `SoftmaxUnit` pipeline implementation, causing data from different transactions to be mixed. This revised plan provides a more explicit and robust implementation description for the `SoftmaxUnit` pipeline stages and register enables to resolve the data hazard. The packing logic for both `ScoreCalculator` and `SoftmaxUnit` has also been clarified to ensure correct LSB-first ordering as specified by the behavior contract. The other modules, which were not implicated in the failure, are preserved from the previous plan.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Computes 16 parallel signed dot products (2-element vectors) to generate the initial attention scores. |  |  |
| SoftmaxUnit | Finds the maximum of 16 scores, computes `h-s_i`, looks up `e_i` from a table, and calculates the total sum of `e_i`. |  |  |
| SelectionAndAccumulation | Generates a selection mask based on a dynamic threshold and accumulates the selected weights (e_i) and weighted values (e_i * v_i). |  |  |
| Normalizer | Performs the final normalization division: `trunc_toward_zero((N*16)/D)`, producing the 16-bit final result. |  | pipelined_divider |
| rq1_sanger_threshold_top | Top-level module that integrates the pipeline stages (Score, Softmax, Selection/Accumulation, Normalization) and handles the system's I/O and control flow according to the specified protocol. | ScoreCalculator, SoftmaxUnit, SelectionAndAccumulation, Normalizer |  |

Critic 原始结构化建议：

```json
{
  "layer": "compiler",
  "reason": "The current design for config threshold_256=1 fails to meet the 300 MHz timing constraint, with a large negative slack of -2.59888577 ns. This is caused by an overly aggressive pipeline schedule with a total latency of only 14 cycles. This short latency, particularly the 3-cycle SoftmaxUnit and 2-cycle SelectionAndAccumulation modules, creates combinational paths that are too long. The goal is to achieve a feasible design for this high-quality configuration by relaxing the latency constraint.",
  "evidence": [
    "evaluation.slack_ns",
    "evaluation.latency_ns",
    "evaluation.feasible"
  ],
  "instructions": "Revise the system plan to increase the pipeline depth to resolve the timing violation. The current 14-cycle latency is too aggressive. Re-introduce pipeline stages, especially in the Softmax and Selection/Accumulation modules. Aim for a total latency closer to the 22 cycles of the successful Round 1 design, for example by increasing the latency of `SoftmaxUnit` to ~7 cycles and `SelectionAndAccumulation` to ~5 cycles. This will break up the critical path and is expected to achieve timing closure, trading a small increase in latency for a feasible design."
}
```

下一轮是否开始尝试该建议：True。这不单独证明建议正确或有效。

## rq1_sanger_threshold / round 5

软件配置：`{"threshold_256": 1}`。

历史PPA尝试曾回退至R1；同轮重测现已完成，上述数值来自当前测量。原记录保留历史回退标记。

语言：chisel；顶层：`rq1_sanger_threshold_top`。

The previous system plan with a 14-cycle latency failed to meet the 300 MHz timing constraint for the `threshold_256=1` configuration, as noted by the critic. The critical path was located in the `SoftmaxUnit` and `SelectionAndAccumulation` modules, which had aggressive 3-cycle and 2-cycle latencies, respectively. To address the timing violation, this revised plan increases the pipeline depth of these two modules, following the critic's instructions. The latency of `SoftmaxUnit` is increased to 7 cycles, and `SelectionAndAccumulation` to 5 cycles. This is achieved by breaking down the max-finding, summation, and multiplication/accumulation logic into smaller, explicitly registered stages. The `ScoreCalculator` and `Normalizer` modules remain unchanged. The new total system latency from `start` to `done` is 21 cycles. This deeper pipeline is expected to resolve the critical path and achieve timing closure at the target frequency, trading a modest increase in latency for a feasible implementation.

| 模块 | 职责 | 子模块 | 只读链接 |
|---|---|---|---|
| ScoreCalculator | Computes 16 parallel signed dot products (2-element vectors) to generate the initial attention scores. |  |  |
| SoftmaxUnit | Finds the maximum of 16 scores, computes `h-s_i`, looks up `e_i` from a table, and calculates the total sum of `e_i`. Pipelined for timing. |  |  |
| SelectionAndAccumulation | Generates a selection mask based on a dynamic threshold and accumulates the selected weights (e_i) and weighted values (e_i * v_i). |  |  |
| Normalizer | Performs the final normalization division: `trunc_toward_zero((N*16)/D)`, producing the 16-bit final result. |  | pipelined_divider |
| rq1_sanger_threshold_top | Top-level module that integrates the pipeline stages (Score, Softmax, Selection/Accumulation, Normalization) and handles the system's I/O and control flow according to the specified protocol. | ScoreCalculator, SoftmaxUnit, SelectionAndAccumulation, Normalizer |  |

Critic 原始结构化建议：

```json
{
  "layer": "stop",
  "reason": "The exploration has reached its `min_loops` budget of 5 rounds. The only feasible design found is from Round 1 (config threshold_256: 3), which establishes the current Pareto frontier. Subsequent attempts to improve quality by targeting lower thresholds (1 and 2) have consistently failed. Round 2 produced a Pareto-dominated point with excessive latency (140ns). Round 3 failed during module build. Round 4 failed timing (-2.6ns slack) with an aggressive pipeline. The most recent attempt (Round 5) fixed the timing issue by deepening the pipeline, but the initial P&R run crashed, and the recovery run produced a design with DRC violations, rendering it infeasible. Given the repeated failures and tool instability on higher-quality configurations, further attempts are unlikely to yield a Pareto-superior design.",
  "evidence": [
    "evaluation.feasible",
    "evaluation.quality_loss",
    "evaluation.energy_efficiency_queries_per_joule"
  ],
  "instructions": "Halt exploration. The design from Round 1 is the only feasible point on the Pareto frontier found within the budget. Attempts to improve quality have been unsuccessful due to timing and tool failures."
}
```

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

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

## rq1_block_nm / A1（诊断辅助修复）

独立验收：True；详情见[修复报告](../block_nm_timing_repair_20260917/RESULTS.md)。原五候选保持独立。

软件配置：`{"n": 7}`。

系统计划与末轮Critic：

```json
{
  "plan": {
    "top": "Rq1BlockNmTop",
    "modules": [
      {
        "name": "FindMin8",
        "purpose": "Finds the minimum of 8 signed scores, breaking ties by choosing the one with the largest original index. This is used to implement the 'keep top 7 of 8' selection by identifying the single element to discard.",
        "ports": [
          {
            "name": "scores_in",
            "direction": "input",
            "width": 72
          },
          {
            "name": "keep_mask_out",
            "direction": "output",
            "width": 8
          }
        ],
        "dependencies": [],
        "implementation": "This is a purely combinational module. It unpacks the 72-bit `scores_in` input into eight 9-bit signed scores. The original indices (0-7) are implicit. A three-stage comparator tree finds the minimum (score, index) pair. The custom comparator logic for two pairs (s_a, i_a) and (s_b, i_b) will select (s_a, i_a) if `s_a < s_b` or if `s_a == s_b and i_a > i_b`. The output of the tree is the 3-bit index of the single score to be discarded. This index is then used to generate an 8-bit mask where all bits are '1' except for the bit at the discarded index, which is '0'.",
        "reference_ids": [],
        "design_prompt": "Generate a combinational Chisel module `FindMin8` that takes an input `scores_in` of 72 bits and produces an 8-bit output `keep_mask_out`. The input represents eight packed signed 9-bit scores. The module must identify the single minimum score among the eight. For tie-breaking, if two scores are equal, the one with the larger original index (from 7 down to 0) is considered the minimum. The output `keep_mask_out` should have a '0' at the position of the minimum score and '1's elsewhere. The implementation should be a comparator tree. No registers are allowed.",
        "tests": [
          {
            "name": "behavior_combinational",
            "steps": [
              {
                "inputs": {
                  "scores_in": 739132885347721553930
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 254
                }
              },
              {
                "inputs": {
                  "scores_in": 92595066625405783120
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              },
              {
                "inputs": {
                  "scores_in": 92414216885903037450
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              },
              {
                "inputs": {
                  "scores_in": 369477777720651315250
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 251
                }
              },
              {
                "inputs": {
                  "scores_in": 462071084429515187300
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              },
              {
                "inputs": {
                  "scores_in": 923239686272253977650
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 191
                }
              },
              {
                "inputs": {
                  "scores_in": 3992475019210513963510
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              },
              {
                "inputs": {
                  "scores_in": 101277334762679703030
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 191
                }
              },
              {
                "inputs": {
                  "scores_in": 0
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              },
              {
                "inputs": {
                  "scores_in": 1060126600920943602371
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 223
                }
              },
              {
                "inputs": {
                  "scores_in": 1335412143605077507342
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 254
                }
              },
              {
                "inputs": {
                  "scores_in": 1310516986867474348721
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 251
                }
              },
              {
                "inputs": {
                  "scores_in": 2179235229780836392343
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 254
                }
              },
              {
                "inputs": {
                  "scores_in": 4237814304488080613597
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 239
                }
              },
              {
                "inputs": {
                  "scores_in": 1926071958509886143429
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 239
                }
              },
              {
                "inputs": {
                  "scores_in": 877937393498242179392
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 254
                }
              },
              {
                "inputs": {
                  "scores_in": 3816403882866522905527
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 247
                }
              },
              {
                "inputs": {
                  "scores_in": 1940569762814518802660
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 253
                }
              },
              {
                "inputs": {
                  "scores_in": 3438324408222823163989
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 251
                }
              },
              {
                "inputs": {
                  "scores_in": 2341908475532123281743
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 247
                }
              },
              {
                "inputs": {
                  "scores_in": 2060943562362716706306
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 251
                }
              },
              {
                "inputs": {
                  "scores_in": 2365803952279117758720
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              },
              {
                "inputs": {
                  "scores_in": 2356562530590527454975
                },
                "cycles": 0,
                "expected": {
                  "keep_mask_out": 127
                }
              }
            ]
          }
        ],
        "behavior": {
          "test_generation_version": 2,
          "latency": 0,
          "let": {
            "s0": "signed(lane(scores_in, 0, 9), 9)",
            "s1": "signed(lane(scores_in, 1, 9), 9)",
            "s2": "signed(lane(scores_in, 2, 9), 9)",
            "s3": "signed(lane(scores_in, 3, 9), 9)",
            "s4": "signed(lane(scores_in, 4, 9), 9)",
            "s5": "signed(lane(scores_in, 5, 9), 9)",
            "s6": "signed(lane(scores_in, 6, 9), 9)",
            "s7": "signed(lane(scores_in, 7, 9), 9)",
            "is_le_10": "1 if s1 < s0 or (s1 == s0 and 1 > 0) else 0",
            "min_s_10": "s1 if is_le_10 == 1 else s0",
            "min_i_10": "1 if is_le_10 == 1 else 0",
            "is_le_32": "1 if s3 < s2 or (s3 == s2 and 3 > 2) else 0",
            "min_s_32": "s3 if is_le_32 == 1 else s2",
            "min_i_32": "3 if is_le_32 == 1 else 2",
            "is_le_54": "1 if s5 < s4 or (s5 == s4 and 5 > 4) else 0",
            "min_s_54": "s5 if is_le_54 == 1 else s4",
            "min_i_54": "5 if is_le_54 == 1 else 4",
            "is_le_76": "1 if s7 < s6 or (s7 == s6 and 7 > 6) else 0",
            "min_s_76": "s7 if is_le_76 == 1 else s6",
            "min_i_76": "7 if is_le_76 == 1 else 6",
            "is_le_32_10": "1 if min_s_32 < min_s_10 or (min_s_32 == min_s_10 and min_i_32 > min_i_10) else 0",
            "min_s_32_10": "min_s_32 if is_le_32_10 == 1 else min_s_10",
            "min_i_32_10": "min_i_32 if is_le_32_10 == 1 else min_i_10",
            "is_le_76_54": "1 if min_s_76 < min_s_54 or (min_s_76 == min_s_54 and min_i_76 > min_i_54) else 0",
            "min_s_76_54": "min_s_76 if is_le_76_54 == 1 else min_s_54",
            "min_i_76_54": "min_i_76 if is_le_76_54 == 1 else min_i_54",
            "is_le_final": "1 if min_s_76_54 < min_s_32_10 or (min_s_76_54 == min_s_32_10 and min_i_76_54 > min_i_32_10) else 0",
            "min_idx": "min_i_76_54 if is_le_final == 1 else min_i_32_10"
          },
          "outputs": {
            "keep_mask_out": "255 - (1 << min_idx)"
          },
          "vectors": [
            {
              "scores_in": "spack(9, 10, 20, 30, 40, 50, 60, 70, 80)"
            },
            {
              "scores_in": "spack(9, 80, 70, 60, 50, 40, 30, 20, 10)"
            },
            {
              "scores_in": "spack(9, 10, 10, 10, 10, 10, 10, 10, 10)"
            },
            {
              "scores_in": "spack(9, 50, 60, 10, 80, 20, 70, 30, 40)"
            },
            {
              "scores_in": "spack(9, 100, 50, 50, 50, 50, 50, 50, 50)"
            },
            {
              "scores_in": "spack(9, 50, 50, 50, 50, 50, 50, 50, 100)"
            },
            {
              "scores_in": "spack(9, -10, -20, -30, -40, -50, -60, -70, -80)"
            },
            {
              "scores_in": "spack(9, -10, 10, -10, 10, -10, 10, -10, 10)"
            },
            {
              "scores_in": "spack(9, 0, 0, 0, 0, 0, 0, 0, 0)"
            }
          ]
        },
        "linked_reference_ids": []
      },
      {
        "name": "DividerWrapper",
        "purpose": "A wrapper for the library's pipelined divider, configured to perform the final division step of the algorithm: a signed 32-bit numerator divided by an unsigned 20-bit denominator, producing a signed 16-bit result.",
        "ports": [
          {
            "name": "clock",
            "direction": "input",
            "width": 1
          },
          {
            "name": "reset",
            "direction": "input",
            "width": 1
          },
          {
            "name": "valid_in",
            "direction": "input",
            "width": 1
          },
          {
            "name": "numer_in",
            "direction": "input",
            "width": 32
          },
          {
            "name": "denom_in",
            "direction": "input",
            "width": 20
          },
          {
            "name": "quotient_out",
            "direction": "output",
            "width": 16
          },
          {
            "name": "valid_out",
            "direction": "output",
            "width": 1
          }
        ],
        "dependencies": [],
        "implementation": "This module instantiates the `predict_unit.FixedPointDivPipelined` class from the `pipelined_divider` library reference. It is configured with `bitWidth=32`, `point=0`, and `stages=33`. This configuration performs a 32-bit integer division. The `numer_in` (s32) is connected to the divider's `numerator` input. The `denom_in` (u20) is zero-extended to 32 bits and connected to the `denominator` input; the divider treats this positive value correctly in its signed division. The `point=0` setting makes the divider perform integer division `numer/denom`. The `s33` result from the native divider's quotient port is then truncated to `s16` to produce the final `quotient_out`. The valid signal is passed through the pipeline, resulting in a latency of 33 cycles.",
        "reference_ids": [
          "pipelined_divider"
        ],
        "design_prompt": "Generate a Chisel module `DividerWrapper` that adapts the native `predict_unit.FixedPointDivPipelined` class. Your module must have the specified ports. Instantiate the native divider with `bitWidth=32`, `point=0`, and `stages=33`. Connect the inputs by casting `numer_in` (SInt) to the divider's `FixedPoint` numerator. The `denom_in` (UInt) must be zero-extended to 32 bits and then cast to a `FixedPoint` denominator. The divider's `FixedPoint` output should be converted back to a `SInt` and truncated to 16 bits to drive `quotient_out`. Propagate the valid signals correctly, accounting for the 33-cycle latency.",
        "tests": [
          {
            "name": "behavior_isolated_0",
            "steps": [
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 0,
                  "denom_in": 100
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              }
            ]
          },
          {
            "name": "behavior_isolated_1",
            "steps": [
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 1000,
                  "denom_in": 10
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 100
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              }
            ]
          },
          {
            "name": "behavior_isolated_2",
            "steps": [
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 1003,
                  "denom_in": 10
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 100
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              }
            ]
          },
          {
            "name": "behavior_stream",
            "steps": [
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 0,
                  "denom_in": 100
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 1000,
                  "denom_in": 10
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 1003,
                  "denom_in": 10
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 4294966293,
                  "denom_in": 10
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 1000,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2147483647,
                  "denom_in": 1
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2147483648,
                  "denom_in": 1
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2147483647,
                  "denom_in": 1048575
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2147483648,
                  "denom_in": 1048575
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 52734659,
                  "denom_in": 235717
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 3281255694,
                  "denom_in": 295394
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2937174705,
                  "denom_in": 290855
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 4081367803,
                  "denom_in": 486124
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 599541520,
                  "denom_in": 69448
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2843984136,
                  "denom_in": 286425
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 3145521415,
                  "denom_in": 865222
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 2547265503,
                  "denom_in": 247774
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 1730639091,
                  "denom_in": 416279
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 884452691,
                  "denom_in": 821957
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 4102178440,
                  "denom_in": 441098
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 1,
                  "numer_in": 3109446303,
                  "denom_in": 873123
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 100
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 100
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 65436
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 65535
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 2048
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 63488
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 223
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 62105
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 60868
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 65097
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 8632
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 60471
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 64208
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 58483
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 4157
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 1076
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 65099
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 1,
                  "quotient_out": 64179
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 0,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0
                }
              },
              {
                "inputs": {
                  "reset": 1,
                  "valid_in": 0,
                  "numer_in": 0,
                  "denom_in": 0
                },
                "cycles": 1,
                "expected": {
                  "valid_out": 0,
                  "quotient_out": 0
                }
              }
            ]
          }
        ],
        "behavior": {
          "test_generation_version": 2,
          "latency": 33,
          "reset": "reset",
          "valid_input": "valid_in",
          "valid_output": "valid_out",
          "let": {},
          "outputs": {
            "quotient_out": "trunc_div(signed(numer_in, 32), denom_in)"
          },
          "vectors": [
            {
              "numer_in": 0,
              "denom_in": 100
            },
            {
              "numer_in": 1000,
              "denom_in": 10
            },
            {
              "numer_in": 1003,
              "denom_in": 10
            },
            {
              "numer_in": "(-1003) & 0xffffffff",
              "denom_in": 10
            },
            {
              "numer_in": 1000,
              "denom_in": 0
            },
            {
              "numer_in": 2147483647,
              "denom_in": 1
            },
            {
              "numer_in": "(-2147483648) & 0xFFFFFFFF",
              "denom_in": 1
            },
            {
              "numer_in": 2147483647,
              "denom_in": 1048575
            },
            {
              "numer_in": "(-2147483648) & 0xFFFFFFFF",
              "denom_in": 1048575
            }
          ]
        },
        "linked_reference_ids": [
          "pipelined_divider"
        ]
      },
      {
        "name": "Rq1BlockNmTop",
        "purpose": "Top-level module that orchestrates the entire rq1_block_nm computation. It contains the main control FSM, which is pipelined to meet timing constraints, input/intermediate registers, and the primary datapath elements for score calculation, exponentiation, and accumulation.",
        "ports": [
          {
            "name": "clock",
            "direction": "input",
            "width": 1
          },
          {
            "name": "reset",
            "direction": "input",
            "width": 1
          },
          {
            "name": "start",
            "direction": "input",
            "width": 1
          },
          {
            "name": "q",
            "direction": "input",
            "width": 8
          },
          {
            "name": "k",
            "direction": "input",
            "width": 128
          },
          {
            "name": "v",
            "direction": "input",
            "width": 128
          },
          {
            "name": "done",
            "direction": "output",
            "width": 1
          },
          {
            "name": "result",
            "direction": "output",
            "width": 16
          },
          {
            "name": "keep_mask",
            "direction": "output",
            "width": 16
          }
        ],
        "dependencies": [
          "FindMin8",
          "DividerWrapper"
        ],
        "implementation": "The top module is built around a state machine with the following states: IDLE, CALC_SCORES, PIPE_S1_MAX, PIPE_S2_MASK, PIPE_S3_EXP, ACCUMULATE, DIV_START, DIV_WAIT, and DONE_PULSE. This FSM implements the critic's suggestion to break the critical path. On a `start` pulse, input `q`, `k`, and `v` are latched. The FSM then proceeds as follows:\n1. `CALC_SCORES` (16 cycles): A MAC unit computes one signed 9-bit score `s[i] = q[0]*k[i][0] + q[1]*k[i][1]` per cycle. The 16 scores are stored in a 16x9-bit register file `s_reg`.\n2. `PIPE_S1_MAX` (1 cycle): A 16-input comparator tree finds the maximum score `h` from `s_reg`. The result `h` is stored in `h_reg`.\n3. `PIPE_S2_MASK` (1 cycle): Two instantiated `FindMin8` modules operate in parallel on the two 8-key blocks in `s_reg` to compute the 16-bit `keep_mask`. The result is stored in `keep_mask_reg`.\n4. `PIPE_S3_EXP` (1 cycle): For each score `s[i]`, this stage calculates the delta `d[i] = h_reg - s_reg[i]` and uses `d[i]` to look up the 16-bit exponential value `e[i]` from a 256x16-bit ROM (initialized with `exp_table_packed_hex`). The 16 resulting `e[i]` values are stored in `e_reg`.\n5. `ACCUMULATE` (16 cycles): Over 16 cycles, the module iterates through the keys. If the corresponding bit in `keep_mask_reg` is set, it accumulates `e_reg[i]` into a 20-bit denominator `D` and `e_reg[i] * v_reg[i]` into a 28-bit signed numerator `N`.\n6. `DIV_START` (1 cycle): The final numerator `N_shifted = N << 4` (a 32-bit signed value) and denominator `D` (a 20-bit unsigned value) are passed to the `DividerWrapper` instance, and its `valid_in` is asserted.\n7. `DIV_WAIT` (32 cycles): The FSM waits for the pipelined divider to complete. The divider has a 33-cycle latency; this state waits for the cycle before the result is valid.\n8. `DONE_PULSE` (1 cycle): When the divider's `valid_out` is high, the 16-bit result is latched, `done` is asserted for one cycle, and the FSM returns to IDLE. Total latency is approximately 1+16+1+1+1+16+1+32+1 = 70 cycles.",
        "reference_ids": [],
        "design_prompt": "You are the top-level assembly UArch. The child modules FindMin8 and DividerWrapper are already complete and verified. Your task is to generate the Chisel code for the Rq1BlockNmTop module. This module must instantiate FindMin8 and DividerWrapper and connect them within a state-machine-controlled datapath that exactly implements the rq1_block_nm algorithm. The state machine and datapath must follow the pipelined implementation plan provided in the parent's `implementation` field, specifically using the states `IDLE`, `CALC_SCORES`, `PIPE_S1_MAX`, `PIPE_S2_MASK`, `PIPE_S3_EXP`, `ACCUMULATE`, `DIV_START`, `DIV_WAIT`, and `DONE_PULSE`. You must manage all intermediate data storage (registers for inputs, scores, max_score, keep_mask, exponential values, and accumulators) and generate the precise control signals for each component in each cycle. The exponential lookup table must be implemented as a ROM initialized from the `exp_table_packed_hex` in the algorithm contract. Ensure all port widths, signedness, and arithmetic operations (including the shifts for the final division) match the system plan precisely. The final `done` signal must be a single-cycle pulse. The total latency from `start` to `done` must be deterministic.",
        "tests": [],
        "behavior": null,
        "linked_reference_ids": []
      }
    ],
    "rationale": "The design addresses the timing failure reported by the critic by further pipelining the top-level FSM. The previous plan's single `PIPE_S1_MAX_MASK` stage, which computed the max score and keep mask in parallel, and the subsequent `PIPE_S2_EXP` stage, still contained too much combinational logic to meet the 300 MHz target. Following the critic's instruction, this logic is now split into three sequential single-cycle stages: `PIPE_S1_MAX` (finds max score `h`), `PIPE_S2_MASK` (computes `keep_mask`), and `PIPE_S3_EXP` (computes deltas and performs exponential lookups). This decomposition breaks the critical path by isolating the max-finding, mask generation, and exponentiation logic into separate pipeline stages, each with a shallower combinational depth. This change increases the total latency by one cycle to approximately 70 cycles, which is an acceptable trade-off to resolve the timing violation. The `FindMin8` and `DividerWrapper` modules from the previous plan are preserved unchanged as they are functionally correct and were not on the critical path.",
    "language": "chisel"
  },
  "critic": {
    "layer": "stop",
    "reason": "The assisted repair was successful. The design meets all constraints, including timing (slack +0.437 ns), area (41.8k um^2 < 200k um^2), and quality (0.0336 < 0.05). The critical path violation from the previous design, caused by a serial reduction chain, was resolved by implementing a balanced comparator tree for the max-score calculation. Since a feasible point has been established and the experiment's loop budget (max_loops=1) is exhausted, the process concludes.",
    "evidence": [
      "evaluation.feasible",
      "evaluation.slack_ns",
      "evaluation.area_um2",
      "evaluation.quality_loss"
    ],
    "instructions": "Stop. A feasible design point that meets all constraints has been successfully generated and measured. The timing violation has been fixed. No further action is required for this task."
  }
}
```

