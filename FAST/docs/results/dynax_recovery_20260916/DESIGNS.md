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

下一轮是否开始尝试该建议：False。这不单独证明建议正确或有效。

