# DynaX 工程恢复实验（2026-09-16 UTC）

目标：在相同 16-key signed 精确 LUT 数学契约下，让 FAST 自主选参、规划、模块实现/复用、组装、E2E、Hammer PPA 和 Critic 迭代形成可验证的结果。要求 300 MHz、面积 ≤200000 µm²、最终相对输出 RMSE ≤5%。

## 与 RQ1 v1 分开统计

本次是工程恢复：可读取前次 FAST 生成且通过模块/E2E的 ScoreAndExpUnit、NormalizationUnit 原样源码和冻结契约，供 Compiler 自主选择参考或原生链接。未导入旧完整系统计划、选择模块或旧顶层；没有人工修改新生成 RTL。已验证模块的来源、SHA-256 和限制保存在 libraries/generated_verified/dynax_rq1_round1/PROVENANCE.json。旧完整设计的配置未通过独立精度，这不影响两个配置无关组件的功能证据，但也不能把它们说成完整合格系统。

本次增加参考材料、诊断策略、选参验证和重试预算，不能与 v1 混算从零成功率，也不是单因素消融。算法文件完全不变；不修改 Q/K/V、LUT、mask、除法、可信 E2E 或 PPA 门槛。

## 冻结评估与预算

- 校准同 v1：seed=20260915，2048 随机＋4 边界。
- 新增选参验证：seeds=2026091701、2026091702，各4096随机，不重复固定边界。Kernel/Critic可以看到这些测量。只有校准和选参验证的最差 RMSE ≤4.5% 才接受配置，为5%最终限制留0.5个百分点余量。
- **全新最终测试：seed=2026091801，8192随机**。搜索结束后才测，绝不反馈给 Agent。旧 seed=20260916 已曝光，不能当作本次独立测试。该样本数/种子在运行前固定，不根据结果挑选。
- 16 keys，head_dim=2，value_dim=1；其他数学与功耗口径沿用 [RQ1 v1](../rq1_20260915/PROTOCOL.md)。要求保留动态 X:M 机制，退化为固定配额或稠密的点不能作为本次成功结论。
- gemini-2.5-pro，temperature=0.2，输出48000tokens，LLM timeout600s、工具timeout3600s；不改模型。
- min_loops=max_loops=5，含初始设计，共5次外层候选尝试；失败尝试也消耗预算，但报告区分失败候选与完成E2E/PPA的设计，不声称必然完成5个有效点。
- Compiler 5次、参考读取3次、UArch/组装各5次、模块串行；SLURM cpu_short，主作业6h，后验证4h。
- 最终独立检查：5组额外 RTL 种子，布线后零延时门级功能验证，setup/hold/DRC及精度门槛。PPA为真实工具结果，功耗仍是统一活动率0.1下的估算，不是芯片实测。

## 通用修复

1. 模块复用缓存要求算法配置、模块完整契约/测试/提示、HDL语言、依赖源码hash和链接库hash全部一致。缓存源必须未变；每次复制后重新编译和功能检查，始终重做顶层组装、E2E和PPA。UArch直接优化的目标绕过缓存。
2. 设计候选耗尽修复预算，记录失败细节后回退到最近通过搜索约束的设计。Critic使用该基线的真实测量和本次失败诊断选择新干预，不把旧测量冒充失败候选的新结果。无可行基线时继续Compiler重规划。参考库完整性失败仍立即终止。
3. 提示明确显式类型寄存器，避免重复使用 RegNext 引发 elaboration 位宽未知；优化时保留无关模块契约。
4. profile.quality_loss 保留原校准误差；selection_quality_loss 单列校准与验证集最差值。最终测试结果只在后验证目录出现。

产物：jobs.json、source_freeze.json、source.tar.gz、逐轮源码和LLM调用、RESULTS.md、DESIGNS.md、metrics.csv及最终归档。失败和无改善结果同样保留。
