# 从原 DynaX 参数重新搜索

入口：`scripts/run_dynax_rediscovery.py`。它直接调用原 DynaX 模型测质量和分布，再搜索调度/硬件。Critic 默认接入算法批次、硬件搜索批次和独立验证后的修正迭代。

**消除固定答案，保留算法定义与合法域**

DynaX XM 的块概率质量为 `softmax(scores + mask)` 在 M 列上的概率之和，再乘 `sequence_length/M`。质量大于 T0 的块保留 N1 个元素，小于 T1 的块跳过，其余保留 N2 个元素。搜索改变这五个参数，算法的数学定义保持固定。

候选标签现在支持 `xm:N1:N2:M:T0:T1`。五个参数一起进入原 DynaX 的 `method_config`、逐候选运行配置、配置哈希、FAST 算法契约、硬件尺寸及重放命令。旧 `xm:N1:N2:M` 标签继续用于兼容旧报告，重搜索入口要求显式阈值。

`configs/experiments/dynax_rediscovery.json` 是可修改的实验域，不是预选赢家。示例包含 M={32,64}、N1={8,16,32}、N2={4,8} 和五组阈值，共 60 个合法算法配置。旧默认值也在合法域内，但没有被标为推荐或优先测量；不能通过排除旧默认值强迫搜索“发现变化”。调度 tile、并行度、阵列行数、每行 PE、寄存器宽度、队列深度、bank 数、除法流水级数、SRAM 容量均有显式域；数据位宽由约束输入给定。

初始设计为空。LLM proposer 和搜索 Critic 不会得到旧赢家或预排优劣的校准表。Proposer 调用失败回退为随机采样；LLM Critic 调用失败、引用不存在的证据或给出非法动作时回退为规则 Critic，分别记录实际来源。评估器仍使用标注过的校准模型。规则 Critic 包含通用诊断启发式，因此不能称整个系统“完全无先验”。

**闭环如何执行**

1. Kernel 提议新的 N1/N2/M/T0/T1，检查合法性、重复和预算。
2. 原 DynaX 在相同模型、数据窗口及 seed 上跑 dense 与稀疏配置，记录真实 perplexity 和 mask 统计。
3. 通过质量门的每个算法配置获得相同的硬件搜索预算。实际 N1/M 决定 TopK 容量和硬件接口尺寸。
4. 硬件批次之间调用 Critic，读取已有指标和约束失败；合法的一字段干预占用下一批的一个评估名额。算法测量完成后也调用 Critic，其合法候选建议进入下一批真实质量测量。分析与前沿一起反馈给 proposer。
5. 从所有算法–硬件组合提取联合 Pareto 前沿，导出每个候选的 `design.json` 和参数完整的重放命令。
6. 使用 `--validate-frontier` 时，对每个前沿候选重新调用 DynaX 抓取其真实 mask，固定同一层、head 和 token 窗口，保留完整任务的所有活跃 tile；按候选 rows/M 切块，再按候选 rows/PE/M/queue 构建 BlockScheduler，运行工作守恒、排空、逐周期计数、综合和 STA。导出 token 哈希与 `complete_captured_task`，不能用相同数量的 tile 代替相同任务。
7. Critic 复核每个独立验证结果。若前沿全部被拒，按 `budgets.repair_hardware` 的额外预算调用 `refine_rediscovery.py`：保留算法，Critic 分析最新失败 → 执行一个新硬件候选 → 独立验证 → 将新结果交给下一轮 Critic。默认配置修正预算为 4；与初始评估次数分开报告。新提案无论通过或失败均记录，过程不会放宽目标频率或质量门。

额外修复了分布统计始终按 64 列切块的问题：XM/NM 现在传入实际 M，并记录 4/8/16/32/64 行的 tile 负载统计。否则 M=32 的候选虽然算法变了，下游收到的统计仍是错误形状。

**运行方式**

在仓库根目录：

```bash
sbatch --export=ALL,FAST_METHOD=llm slurm/loop/fast_dynax_rediscovery.slurm
sbatch --export=ALL,FAST_METHOD=random slurm/loop/fast_dynax_rediscovery.slurm
# 同一 proposer、参数域与预算下关闭 Critic，做消融对照
sbatch --export=ALL,FAST_METHOD=llm,FAST_CRITIC=off slurm/loop/fast_dynax_rediscovery.slurm
```

设置 `FAST_CONFIG` 可替换整份任务、参数域、约束和预算；`FAST_SEED` 控制随机搜索，LLM 输出没有可重现的采样 seed。两个方法使用同一个配置文件。每次输出使用新目录，失败构建不能沿用旧产物。

`--critic auto|llm|rule|off` 控制 Critic，默认 auto：LLM 搜索用 LLM Critic，随机搜索用规则 Critic。`random + rule` 是带规则反馈的随机提议策略；纯随机对照必须显式使用 `random + off`。固定预算模式下，Critic 的 stop 表示本阶段不干预，不提前消耗掉或扩大剩余预算。每次干预最多改一层的一个字段。

或者在 FAST 目录、已有环境中运行：

```bash
python scripts/run_dynax_rediscovery.py \
  --config configs/experiments/dynax_rediscovery.json \
  --out /path/to/new-run --method llm --seed 0 \
  --dynax-python /path/to/dynax/python --gcp-project YOUR_PROJECT
```

直接使用 Kernel 搜索入口时也可显式展开参数：

```bash
python -m fast.cli_kernel --run-dir /path/to/kernel-run \
  --algorithm xm --block-ms 32 64 --xm-high 8 16 32 --xm-low 4 8 \
  --threshold-0 0.75 1.5 --threshold-1 0.05 0.2 \
  --proposer llm --gcp-project YOUR_PROJECT --dynax-python /path/to/dynax/python
```

这个单独 Kernel 入口只评估算法层；要让硬件反馈参与算法下一轮选择，使用 rediscovery 入口。

**证据边界**

- 默认小实验只使用 2 个 512-token 窗口，ε=0.05。质量结论仅覆盖该样本；未验证量化执行路径的模型精度。
- 联合搜索中的延迟/能耗是 L1 共享模型预测；能耗仍不含全部预测、控制和存储访问。不能称为整机实测能效。
- RTL 重放验证的是所选算法产生的真实工作量在所选调度器上的行为。软件计算 T0/T1 选择，当前硬件验证不包含自主计算这些阈值或完整 attention 数值路径。
- 模块验证只实现候选中 rows/PE/M/queue 的子系统；bank、SRAM、divider 等其他参数虽然被搜索并导出，尚未组成同一次完整系统 PPA 验证。
- 参数、源代码和重放身份一致，是本次打通的内容；独立能耗优势、稳定优于人工优化与跨模型泛化仍需单独实验。
- 修正后的 `module_verified` 只表示调度器功能及目标频率通过，不意味着完整加速器质量、面积、功耗都已实测。原始模型前沿仍保留在 `search.json`，独立验证及修正结果另行记录，不能把它们当成同一证据等级。
- 与原 DynaX 默认方案比较时，应另外冻结原算法参数与完整硬件配置；不能将随机对照称为原论文人工优化基线，也不能用不同质量样本或不同模块范围的数字相除。

`search.json` 保存逐算法测量、全部算法–硬件设计、下游反馈事件、前沿、回退记录及源码哈希。`candidates/<design_id>/` 保存精确配置、重放命令、trace、工具日志与 RTL 验证清单。脚本结束时检查源码是否在运行中变化。

`search.json` 与 `refinement.json` 中的 `critic_reviews` 保存输入上下文及哈希、Critique、回退原因、实际执行的 before/after 和 outcome。`state=evaluated` 只说明干预被评估；`model_frontier_extended` 是 L1 前沿变化；`independent_constraint_recovered` 是独立子系统约束恢复。它们均不等于独立整机能效改善。`critic_calls` 单独记录 LLM 回复、耗时与成功/回退情况，不能仅比较工具评估次数而忽略额外模型开销。

LLM 的完整提示词、回复和调用失败也随结果保留。正式长作业使用冻结的源码目录；可通过 Slurm 的 `FAST_REPO` 指向快照，避免工作目录继续开发时改变实验代码。

对于已有的失败实验，可通过 `slurm/loop/fast_dynax_refine.slurm` 指定 `FAST_SOURCE` 重入，不必重复支付已经完成的质量测量成本。修正记录保留完整父实验副本及其哈希，避免父报告后续增加状态字段后无法核对来源。
