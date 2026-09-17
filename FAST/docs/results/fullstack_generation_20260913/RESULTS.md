# 新主线：完整系统生成与 Critic 迭代

已完成真实 LLM → 新 Chisel 系统 → Verilator 数值验证 → 全顶层综合/STA → Critic → 新实现 → 再验证的两轮闭环。Compiler 实际检索只读硬件库，并为 UnsignedDivider 分配 `pipelined_divider` 参考代码。该次运行保留的第二轮设计已在不调用 LLM 的情况下独立重新编译、仿真和提取 PPA，结果一致。

这是 **threshold-attention 小型集成工作负载**的完整系统结果，不是 DynaX 全模型、softmax attention 或历史 scheduler 的结果，也不是 Critic 消融。

## 软件配置与实际硬件

- 算法：`threshold_attention`，threshold=64；1 个 query、4 个 key/value；Q/K 维度为 2、V 为标量；输入均为 unsigned 4-bit。
- Kernel 对 0/64/128/192 四个阈值执行分析。选中配置的归一化平均输出绝对误差为 0.0702564（相对 threshold=0），测得稀疏度约 31.63%。这是 260 个合成查询的指标，不是 perplexity。
- 顶层：`ThresholdAttention`；4 个并行 `ScoreUnit`、一个两级 `AggregationUnit`、一个 `UnsignedDivider`，包括数据通路、控制与握手。
- Compiler 将库里的有符号定点恢复除法参考适配为 15-bit 分子、11-bit 分母的无符号整数除法，输出 4-bit 商，除零返回零。
- 最终源码中除法器 `STAGES=4`，每级完成若干恢复除法位步骤；整个系统实测每查询 8 个周期。参考库哈希检查通过。

[最终新 Chisel 源码目录](verified_v6/raw/fullstack_17591809/round_02/build_01/) · [最终轮完整结果及源码哈希](verified_v6/raw/fullstack_17591809/round_02/result.json) · [Compiler 检索与分配记录](verified_v6/raw/fullstack_17591809/round_01/build_03/reference_bindings.json)

## 同一工作负载、100 MHz 下的结果

| 指标 | 初始设计 | Critic 建议后的设计 | 变化 |
|---|---:|---:|---:|
| 除法器流水级数 | 15 | 4 | 减少 11 级 |
| 全系统延迟 | 190 ns | 80 ns | −57.89% |
| 综合单元面积 | 7191.310 µm² | 5120.766 µm² | −28.79% |
| 估计功耗 | 0.644960 mW | 0.410456 mW | −36.36% |
| 估计每查询能量 | 0.122542 nJ | 0.0328365 nJ | −73.20% |
| 100 MHz 下 setup slack | +8.4961 ns | +7.9591 ns | 均满足 |
| 数值验证 | 100/100 | 100/100 | 同一组可信参考用例 |

约束为质量损失 ≤0.15、面积 ≤30000 µm²、频率 100 MHz。两轮都可行，第二轮在 energy–latency 上支配第一轮，保留 Pareto 轮次为 `[2]`。

面积覆盖完整生成顶层及其全部子模块；工艺为 Nangate45。功耗来自 OpenSTA 的 **全局活动率 0.1 预布局估计**，不是硅片或板级实测，也不是逐网工作负载活动标注。能量为估计功耗乘以仿真实测周期数对应的延迟；没有布局布线或 SRAM 宏集成。

## Critic 确实做了什么

第一轮 Critic 引用了真实周期、slack、面积等字段，指出除法器 15 级流水与 100 MHz 目标之间有大量时序余量，要求 UArch 把流水深度降到 4。第二轮源码与周期结果验证了这项改变；第一轮 `critique_applied=true`。第二轮提出继续减少流水级的建议，但两轮预算已用完，`critique_applied=false`，不算已执行收益。

早期 v4 的最终设计有更低的绝对能量和延迟，但其参考输入方式与初始设计不同；这里没有把 v6 称为跨版本的全局最优，也不从版本间差异推断检索策略的因果收益。

本轮 UArch 重入仍会重生成整套模块，不能把全部 PPA 差异严格归因于单独一行参数或 Critic 的因果贡献。尚未做这个新流程的有/无 Critic、规则 Critic、多个 seed 对照。这里能够成立的结论是：**分析产生了具体干预，干预进入了设计，新的完整系统经过独立验证后改善了目标指标。**

## 记录、复验与代码版本

- [两轮详细报告](verified_v6/RESULTS.md)：原始角色调用、模块实现、检索分配、工具日志、网表和阶段事件。
- [本次保留设计的零 LLM 复验](revalidation_best/revalidation.json)：面积、功耗、延迟和能量与原运行一致。
- [另一套 Chisel 闭环记录](verified_v4/RESULTS.md)：早期先完成的模板整体传入版本；不把它作为按模块检索的证据。
- [开发失败与修复过程](DEVELOPMENT.md)：保留解析器错误、时钟/位宽错误、数值失败和超时，无失败样本删除。
- [当前 Compiler 检索协议检查](compiler_protocol_check/phase_check.json)：最新代码用两次真实 LLM 调用完成先选参考、再输出计划，验证了结构化协议；此项只检查 Compiler，没有自行声称新的 RTL/PPA 结果。
- `verified_v6/source` 是物理实验执行时的冻结代码。当前工作区后续增加了 Compiler 的分阶段提示/响应修复，以及逐模块实现说明记录。差异见 `current_source_delta.json`，不反向改写旧实验。
- 保留的 Compiler 计划是接口/拓扑蓝图；UArch 重入后，其文字可能仍写着最初的 15 级。最终实现由该轮源码的 `STAGES=4` 和实际 8 周期决定，不能只读旧计划中的文字。

复验入口：

```bash
python scripts/revalidate_generated_design.py \
  --run docs/results/fullstack_generation_20260913/verified_v6/raw/fullstack_17591809 \
  --round 2 \
  --catalog docs/results/fullstack_generation_20260913/verified_v6/source/libraries/catalog.json \
  --output /scratch/<user>/fast-best-recheck \
  --tool-root <包含 containers、pdk、tools 的目录>
```

## 下一步

1. 为完整 DynaX 补齐 Q/K/V 到归一化输出的可信量化语义、质量测量和 testbench，再把它注册为新的算法契约。不能拿现有 scheduler/选择事件验证代替数值契约。
2. 给 Critic 增加显式模块 targets，使 UArch 只改受影响模块，并重新检查依赖；减少调用成本，也让归因更清楚。
3. 冻结起始设计与预算，做新主线的多 seed 对照；补充更大/更多工作负载及逐网活动率功耗分析。
