# FAST：能耗–延迟目标与 Hackathon 实施报告

2026-09-10。当前交付包含目标函数改造、对照实验工具、真实 LLM 小实验，以及一次发现并修复调度器死锁的独立 RTL 验证。**尚未证明 FAST 自主跨层适配稳定优于对照，也没有整机实测能耗。**

**研究问题与本次可交付的主张**

长期问题保留：Can agentic full-stack co-design replace algorithm-specific manual optimization for dynamic sparse-attention acceleration?

本次实验建议收窄为：在固定质量和硬件预算下，FAST 能否利用验证反馈，完成一次跨层适配，并以相同探索预算获得优于固定配置和无反馈搜索的可行能耗–延迟前沿？

价值在于减少每换一种稀疏模式就重新手工调整布局、调度、队列和硬件参数的工作。关键证据是“新输入触发了不同的设计决策，而且独立评估认可了收益”。一次成功适配可以证明可行性；“替代人工优化”还需要多任务迁移、强人工基线和优化成本比较。

**统一优化定义**

\[
\min_x (T(x),E_{task}(x)),\quad
E_{task}=\int_0^{T(x)}P(t)\,dt,\quad
\eta=1/E_{task}
\]

约束为质量损失不超过 ε、面积不超过预算、可实现频率达到目标，以及 SRAM、PE、合法位宽和功能正确性限制；用户给定功耗上限时也检查功耗。当前近似使用平均功耗乘任务时间。

- task 必须固定输入及输出语义，例如同一输入上的单个 attention head，N=512、head_dim=64。稀疏化可以减少执行的 MAC，但不能借此改变任务计量单位。
- 面积是可行性条件，不再是默认 Pareto 轴。能效用 task/J，避免用随稀疏度改变的实际 MAC 数归一化。
- EDP 仅作为附带指标保留，不能替代 Pareto。默认代表点是前沿中延迟最低者；完整前沿才是搜索输出。
- 缺失、非有限或非正的目标坐标不进入前沿；已启用约束所需的数据缺失时，报告可行性未验证并排除。
- 质量门仍沿用输入 Kernel 报告的指标和 ε，不能把一个小样本质量通过解释为全面模型精度保证。

**已落地的工程改动**

| 改动 | 作用 |
|---|---|
| `fast/agents/pareto.py` | 统一非支配关系、前沿进展、固定参考点的二维 hypervolume |
| `codesign.py`、`cooptimizer.py` | 默认优化 seconds/J；修正 mW 到 W 的换算；按前沿进展早停；保留完整评估轨迹 |
| `compiler.py`、`flow.py` | 目标贯穿内外循环；降能耗也算进展；缓存包含目标、约束、head_dim 和模型版本 |
| `experiment_db.py`、`run_codesign.py` | 输出能耗、能效和证据范围；功能验证通过与性能实测分开标注 |
| `plan_proposers.py`、`llm_critic.py` | 明确精度是门槛；显示延迟/能耗反馈；记录 LLM 成功、拒绝和规则回退 |
| `run_pareto_benchmark.py` | 同一起始批次、搜索空间和评估预算；随机/规则/LLM/去数值反馈对照；轨迹及输入哈希 |
| `rtl_gate.py` | 工具异常不能沿用旧输出通过；仿真非零退出不能被 PASSED 字样覆盖；启用断言并保留周期测量 |
| `validate_pareto_scheduler.py` | 新构建目录、冻结 trace、源码哈希、功能检查、综合面积和可信 STA 时序 |

能耗目前只覆盖执行阵列动态功耗和 SRAM 漏电，未覆盖 predictor、top-k、scheduler、divider、gather 及动态访存等项。现阶段能耗排名属于探索假设。不要用不同证据范围或不同任务的点拼接同一前沿。

**独立 RTL 结果：验证先发现错误，再允许性能比较**

冻结输入是 TinyLlama 层 10 的 XM trace，32 rows × 4 PE，切片 `[256,384)` 共 128 tiles。这只是同一模型的另一个切片，不是 held-out 模型。所有配置都固定 350 MHz。

第一轮新构建中，原有 BlockScheduler 的三个深度都未通过工作守恒/排空检查。原因是屏障流水化混用了当前周期和上一周期的完成状态。此次工程修复统一了 `ahead`、`leaving`、屏障推进的更新周期，并恢复性能计数器的逐周期接口语义；新增 TB 检查从公开输出独立计算计数增量。

| 队列深度 | 功能验证 | 活跃周期 | 固定频率延迟 | 综合逻辑面积 μm² | STA 关键路径 ns | 相对 depth 0 的周期减少 |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 通过 | 438 | 1.251 μs | 8,894.508 | 2.2685 | — |
| 2 | 通过 | 357 | 1.020 μs | 26,382.678 | 2.4318 | 18.49% |
| 4 | 通过 | 338 | 0.966 μs | 42,826.266 | 2.7601 | 22.83% |

三者在综合后、布局前 STA 中均满足 350 MHz，验证期间源码哈希未变化。队列加深提高了利用率，也增加了面积并缩小时序余量。depth 4 不能因此被称为“整体最优”。

这些周期覆盖 **BlockScheduler 活跃调度过程**，不覆盖完整 attention、输入搬运和整个系统流水线。能耗没有测量，JSON 中明确为 null。这个验证切片与下方 LLM 候选也不是同一个完整设计，不能用该表替 LLM 候选背书。

本次死锁修复由开发助手直接实施，**不能计入 FAST 自主适配成果**。可展示的证据是验证工具确实拒绝了有问题的设计，并在修复后重新构建验证。

原始结果：[失败清单](results/scheduler_validation_before_20260910.json)、[通过清单](results/scheduler_validation_after_20260910.json)。构建与命令日志分别保留于 `/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/pareto_validation_17350589` 和 `pareto_validation_17350655`。

**等预算搜索结果：有可展示的闭环迹象，尚无稳定胜出结论**

规则对照使用同一已测 Kernel 报告中质量门通过的 `xm:32:4:64`、`xm:32:16:64`，N=512、head_dim=64、ε=0.05，面积上限 4,000,000 μm²、目标 350 MHz、最多 256 PE 和 512 KiB SRAM。

三种策略 × 两个配置 × 五个 seed × 24 次唯一设计评估，共 **720 次评估**，全部完成预算。第一批四个点相同。主要最优点重合，因此没有证据说规则反馈比基线更优。guided 是确定性策略，其五次重复不是五次独立随机实验。完整数据：[JSON](results/pareto_pilot_20260910.json)、[汇总](results/pareto_pilot_20260910.md)、[图](../figures/pareto_energy_latency_20260910.png)。

随后在 `xm:32:4:64` 上进行了真正的 LLM 调用：每种方法 8 次评估，其中 4 次共同初始化、1 次 LLM 批量提出另外 4 个候选。Gemini 2.5 Pro 带反馈和去数值反馈版本均成功返回，均为 **1 个成功批次、0 次规则回退**。

| 方法 | 最终非支配坐标（延迟 μs，部分模型能耗 μJ） | 搜索耗时 |
|---|---|---:|
| LLM 带反馈 | (59.043, 40.190)、(70.189, 37.250) | 58.321 s |
| LLM 去数值反馈 | (59.043, 40.190) | 51.937 s |

第二个点在模型中以约 18.9% 更长延迟换取约 7.3% 更少能耗，验证了“保留取舍”的新目标行为。它不是更快的点。小实验只覆盖一个配置的一次随机 LLM 输出，不能推断显著性；LLM 采样并未设置 seed。去数值反馈只是隐藏历史数值/可行性/诊断，并不是完整的 no-Critic 系统消融。

LLM 成功数据：[JSON](results/pareto_llm_live_retry_20260910.json)。此前 DNS 失败与 45 秒超时结果也保留，分别为 `pareto_llm_smoke_20260910` 和 `pareto_llm_live_20260910`；它们触发了回退，不能算作 LLM 搜索成功。API 货币成本目前未采集。成功小实验早于 benchmark 源码哈希记录的补充，只包含输入哈希；后续运行会记录 Python 源码哈希和 LLM 配置。

**复现入口**

以下命令在 `FAST/` 下运行。固定输入路径必须显式给出，不自动选取 latest 文件。

```bash
python -m pytest -q

python scripts/run_pareto_benchmark.py \
  --search /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/kernel_search_llm_17248126/kernel_search_llm.json \
  --head-dim 64 --labels xm:32:4:64 xm:32:16:64 \
  --budget 24 --batch 4 --seeds 0 1 2 3 4 \
  --out docs/results/pareto_pilot_reproduction.json

python scripts/plot_pareto_benchmark.py \
  --results docs/results/pareto_pilot_reproduction.json \
  --out figures/pareto_reproduction.png

sbatch --export=ALL,WORKLOAD_JSON=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/workload_17126047/workload_rows32.json \
  ../slurm/rtl/fast_pareto_validate.slurm
```

LLM 对照在 benchmark 命令上使用 `--methods llm llm-no-feedback --gcp-project <project> --llm-timeout 180`，使用已有 ADC。统计性比较应使用多次独立 LLM 运行；相同整数 seed 不保证 LLM 输出相同。若计算 hypervolume，需在实验前为每个任务固定共享参考点，同时传入 `--reference-latency-s` 与 `--reference-energy-j`。

**Hackathon 下一阶段的验收协议**

1. 冻结一次迁移：旧 workload 上的人工配置 → 一个未参与调参、且实际改变分布/瓶颈的新 workload。保留旧设计作为强基线。不能只展示更换标签。
2. 让 FAST 自主提交候选、调用工具并读取失败原因。记录至少两个相互影响的层级决策，例如稀疏块预算改变 → 队列/布局改变；最终评估必须消费候选的真实参数。
3. 与固定旧配置、随机搜索、规则搜索和去数值反馈策略比较。统一设计空间、起始信息、质量门、独立验证次数及搜索预算，并记录耗时、LLM 成本和人工干预。
4. 对最终前沿候选与基线进行相同工具链的独立评估。先检查功能与精度，再检查面积/时序，再比较延迟和能耗。整机能耗需要同一边界下的活动数据与功耗估算，包含动态存储访问；得不到时只能报告性能与部分能耗假设。
5. 在冻结的新 trace 上重放胜出候选。成功标准是改善独立评估的前沿或达到部署约束所需的探索成本更低；前沿点数更多、LLM 说有收益、同一模型重复打分均不是成功标准。

建议展示顺序：输入迁移与约束 → FAST 的跨层决策和被拒绝候选 → 独立通过的设计 → 相同预算的对照图 → 一键重放。当前可以展示目标统一、失败拒绝、调度器验证，以及真实 LLM 保留能耗取舍的轨迹；“完整自主适配胜过对照”仍需要上述实验闭合。
