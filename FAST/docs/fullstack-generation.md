# 完整系统生成的实现约定

先读 [当前架构](agent-architecture.md)，启动和复验见 [DynaX 指南](dynax-autonomous.md)。本页说明扩展算法、IP 和验收时需要遵守的接口。

## 算法是输入

`libraries/catalog.json` 注册用户维护的可信算法插件。插件描述输入/输出端口、合法配置域、配置验证、画像测量和独立 E2E 参考。当前有 `threshold_attention` 与 `dynax_xm_row`，未知算法明确拒绝；支持新算法需要注册相应契约，不能只改 prompt 后默认沿用 DynaX 数学。

Kernel 实际运行可用配置并分析模式；Compiler 读取画像和端口，检索硬件参考，定义 SystemPlan。最外层 E2E 由算法插件提供，模块 Agent 不能替换。

## 参考库与新硬件

模板条目可包含 `support_sources` 和 `test_references`。Compiler 把对应源码与 golden 分派给模块 UArch，并说明接口/数学/位宽差异。原 testbench 是参考材料，不会未经适配直接计作生成模块的验证通过。

生成硬件写入新运行目录。`reference_ids` 声明参考来源；`linked_reference_ids` 必须是其子集，用于只读编译原生 Chisel 实现与完整依赖闭包。原生类无需重写，生成器可以写薄适配器；所有库文件和生成文件都有哈希。

Chisel 模式生成零参数 RawModule、显式时钟/复位和契约端口；可信驱动负责 main、依赖和 elaboration。Verilog 模式遵守受支持的可综合源码约束。不能向参考库写文件，也不能通过源码夹带工具执行。

## 模块设计和组装

Compiler 在 SystemPlan 中声明模块依赖、端口、实现任务和有界数学/周期行为。`behavior.py` 计算局部测试期望值，不执行任意 Agent 测试代码。每个模块具有独立 prompt、尝试与工具日志。

`DesignDispatcher` 默认顺序执行模块，也支持按依赖并发。模块通过后由独立 AssemblyUArchAgent 组装；accepted_modules 的哈希在组装前复核。局部失败由 UArch 修复；契约或架构问题可经 CompilerDiagnosis 返回 Compiler。

独立 E2E 必须再次校验最终算法数值与协议。所有模块通过不代表系统通过。失败不会进入 PPA，更不会以估算值补齐。

## PPA 与 Critic

`yosys_opensta` 提供综合/预布局估计；`hammer_openroad` 执行完整生成顶层的物理实现。结果必须注明后端、工艺、活动率和有效性，不能跨后端混用。当前 Hammer 模型包含布局、CTS、详细布线和 RC 提取；无 GDS、多 PVT signoff 或硅片测量。

完整 E2E/PPA 后，Critic 返回 `kernel`、`compiler`、`uarch` 或 `stop` 并引用真实字段。Kernel 重入重新分析配置；Compiler 重入修改计划；UArch 重入先保留契约，但发现接口/延迟冲突仍可升级重规划。诊断与 Critic 分别计数。

Pareto 仅保留满足质量/面积/频率等约束的测得点，目标是 latency 更低、energy efficiency 更高。相同任务下降低 J/query 与提高 queries/J 等价。非支配点不等于全局最优。

## 运行产物

```text
run/
  task.json, algorithm_contract.json
  library_manifest.json, references/
  kernel_survey.json
  agent_calls/                     全部角色的原始请求和回复
  events.json                      实际事件序列
  round_01/
    build_01/
      system_plan.json
      reference_bindings.json
      accepted_modules.json
      <Module>/                    独立任务、源码、尝试、测试、诊断
      <Top>/check_*/                可信 E2E 向量和结果
      hammer/                      配置、工具日志、最终物理产物
    result.json                    本轮配置、实现、哈希、PPA、Critic
  summary.json                     结束状态、调用数、非支配轮次
```

保存使用 `scripts/archive_generated_run.py`，复验使用 `scripts/revalidate_generated_design.py`。源码哈希、完整性和测量是否完成是验收依据；Agent 自述的性能收益仅为解释，必须核对测量。

## 可选的恢复与验证配置

`reuse_verified_modules` 默认关闭。启用后，只有算法配置、语言、完整模块契约（包括测试和提示）、依赖源码hash与链接库hash均相同的模块才可复制；复制后仍重新编译和功能验证。顶层始终重新组装，E2E/PPA始终重测。Critic 的 `uarch` 干预默认重生成所有模块，也可用 `target_modules` 指定范围；Compiler通过修改目标模块契约使其重新实现，未变模块可复用。

`continue_after_build_failure` 默认关闭。启用后，设计构建预算耗尽记为 `candidate_failed`，可回退到已有最高能效搜索可行设计，使用基线测量与本次失败反馈重新调用Critic。没有可行基线时继续Compiler规划。完整性错误不可恢复。`failed_rounds` 与 `completed_design_rounds` 分别统计失败候选和完成物理评估的轮次；回退后的Critic标注 `critique_evidence_round`，不伪造新测量。

`quality_validation_seeds` 与 `quality_validation_samples` 可为实现 `measure(config,seed,count,boundaries=False)` 的可信算法增加选参验证。`quality_loss` 仍是校准值；`selection_quality_loss` 为校准和验证最差误差。`quality_margin` 从搜索接受门槛中扣除，最终限制不变。选参验证用于选择配置，不能称最终测试；后验证使用独立新seed，且禁止与选参验证seed重合。


## 从中断恢复（2026-09-17）

`--resume-run OLD_RUN --run-dir NEW_RUN` 必须使用新目录：原任务、事件、调用、失败和测量保留不变。恢复检查算法/库/源码哈希以及质量、面积、频率、种子、活动率等科学约束；允许显式改变恢复策略和执行预算。`recovery_origin.json`记录来源和原轮次文件hash，继承测量标记为历史证据。

配置选择和E2E完成后立即保存`round_N/result.json`，PPA开始前状态为`ppa_pending`；PPA返回、Critic返回再次保存。`summary.json`也随阶段更新，因此`status=running`不是终态。物理后端在`hammer/result.json`记录当前阶段，日志实时写盘。断点恢复以已保存的候选/已接受RTL为边界：未完成PPA的原样RTL先重新通过可信E2E，再在`ppa_retry_N`重测物理结果；这不消耗一个新的外层候选。物理子步骤记录不等于直接复用任意中间数据库；当前恢复会重跑物理流程。

启用`continue_after_build_failure`后也处理PPA不完整：保留`ppa_failed`证据并调用Critic，若有可行点则回退；无可行点时Critic可依据工具错误提出下一轮修改。构建失败已消耗的轮次不重置，旧失败和`prior_evaluations`保留。候选预算仍由原轮号和`max_loops`限制。

后验证和测量报告使用`read_summary`，缺少最终汇总时从逐轮记录恢复，状态明确为`interrupted_without_summary`。已完成点可以独立验收，但不会据此把原作业改写为正常结束。建议独立SLURM后验证作业使用`afterany`依赖，避免主作业被调度器终止时跳过收尾。

### OpenROAD ODB-0445 兼容性重试

默认后端对精确匹配的 `ODB-0445 / dbTechNonDefaultRule` 错误自动执行一次 CTS 检查点恢复：保留失败的脚本、日志和数据库，重新启动 OpenROAD，从 `clock_tree_resize` 继续。恢复重新施加原有 1 ns 输入/输出延迟、5 fF 负载及 CTS placement padding，保留全部默认 setup 修复动作、hold修复、布线、提取和可行性检查。`par_recovery`记录检查点hash、原失败与重试命令，`par_measurement_log`指向重试日志。其他错误不触发该恢复；这不是任意PPA阶段的断点恢复。

`--openroad-setup-policy no-clone-buffer` 是显式工具兼容模式，默认仍为 `default`。它只给 `repair_timing -setup` 增加 `-skip_gate_cloning -skip_buffering`，保留尺寸调整、引脚交换、hold修复、完整布线与寄生提取，并保留所有PPA可行性判断。运行元数据、Hammer配置及测量结果记录该策略。

遇到已确认的 `No undo_updateField support for type dbTechNonDefaultRule` 时，可对不可变的已验收RTL在新目录使用 `--resume-run` 重测同一轮；这不是新候选，也不是降低频率或跳过时序检查。不同物理优化策略的结果不能未经同策略重测，就全部解释为Critic收益。

恢复后的旧失败决策保存为`prior_attempt_decisions`（包括旧Critic、回退轮号和证据轮号），避免把历史回退误标为新PPA的状态。此前冻结实验保留原始文件；报告把“旧PPA尝试曾回退”与“当前同轮重测完成”分别显示。

### 物理关键路径反馈

Hammer后端在布线和寄生提取结束后保存最差三条setup路径，并从实际`routed.v`映射起终点单元及寄存器网名。`evaluation.timing_diagnosis`包含`paths`、可引用的`endpoint_mapping`及`report_excerpt`。这是STA测量证据，不自动等价于某行源代码的根因；Critic须结合实际模块源码分析，缺乏映射时应保留不确定性，不能凭算子成本猜测瓶颈。新增报告命令不改变布局布线几何或优化策略。

后续源码上下文修复：Critic请求通过`accepted_sources`接收当前已接受的生成代码及hash，发送前校验原始源码和展开RTL的清单。实现说明/源码hash不能替代代码本身。综合网名可能来自消费者端口的别名，不能仅根据前缀推断寄存器所属流水级或反向依赖。2026-09-17的N:M五候选冻结实验使用v4，未包含这一后续修复；其收益需要新的统一实验验证。
