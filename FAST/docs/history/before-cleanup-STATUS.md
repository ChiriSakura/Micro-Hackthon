# FAST 现状表

> 最新完整系统生成结果：[参考测试、Hammer 物理实现与 Critic 对照](results/fullstack_extensions_20260913/RESULTS.md)；[20 分钟阅读与新 PPT 思路](results/fullstack_extensions_20260913/READING.md)。下文为较早参数搜索/反馈修正路径的历史记录，数字与结论不能代替本轮生成实验。

> 新增主线请先读 [参考库驱动的完整系统生成](fullstack-generation.md)。下文保留历史调用链和实验口径，不能将它们自动视为新系统生成流程的证据。

> 2026-09-13 阅读提示：下文包含较早阶段的状态，不能整表视为当前结论。最新硬件反馈 Critic 消融已完成 24×5-loop；`RandomProposer` 已存在，默认 `ObjectiveSpec` 使用 seconds/energy_j（仍为部分能量模型）。本轮另有 scheduler 统一活动率功耗估计，不能推广为完整 PPA。当前阅读请先看 [快速指南](quick-reading-20260913.md) 和 [消融报告](results/critic_ablation_20260911/RESULTS.md)，下文保留供历史追溯。

**每条主张对应：状态、证据、最后验证时间、以及它不能支持什么。**

评审（`research-review-2026-09-09.md` §9）要的就是这张表：「用一份机器生成
的现状表替代互相矛盾的历史叙述」。散在 `agent-architecture.md` 里的历史叙述
仍然保留（它记录了怎么走到这一步），但**历史数字请核对对应原始报告，新主线以页首最新报告为准**。

图例：✅ 已验证 · ⚠️ 有限制 · ❌ 已作废 · 🚧 未做

---

## 1. 硬件：已验证的测量

| 主张 | 状态 | 证据 | 日期 |
|---|---|---|---|
| AttentionTile 数值通路正确 | ✅ | golden testbench 32/32，有符号误差均值 −0.031 | 09-11 |
| 控制 FSM 与 golden 逐维一致 | ✅ | `AttentionTileTop` 32/32，硬件自报 46 拍/行 | 09-11 |
| 选择通路一致 | ✅ | `AttentionTileSystem` 硬件 TopK 选出 8/8 与参照相同的列 | 09-11 |
| 预测阵列控制广播扇出已修 | ✅ | 62.68 → **1.858 ns**（33.7×），slack VIOLATED→MET，面积 +0.46~0.89% | 09-11 |
| bank 冲突随 bank 数下降 | ✅ | 实测 4/8/16/32 banks → 冲突 4/2/0/0 拍 | 09-11 |
| 整设计面积模型可信 | ✅ | 实测/预测 = **0.987**（1.3% 以内） | 09-10 |

## 2. 硬件：有限制的

| 主张 | 状态 | 限制 |
|---|---|---|
| 多行并行吞吐 | 🚧 | 阵列是脉动列广播（`rows(i+1).regs_top := rows(i).regs_bottom`），第 r 行数据延迟 r 拍。当前全部验证**只驱动第 0 行** |
| 预测阵列自身排程 | 🚧 | 相位补偿、组内降序装 Q、逐 key settle 都还在 testbench 里，没进 FSM。分数由外部串行喂入（这是 tile 的设计意图） |
| 动态阈值分档 | ⚠️ | `BlockTierSelect` 已实现三档 {0, n2, n1}，但硬件比的是**未归一化**的 exp 和，软件比的是 softmax 之后的概率。严格对齐需要两趟——`TierThresholds.hardware_is_exact()` 恒为 False |
| 存储停顿 | ⚠️ | KeyFeeder 反压已接通并可测，但当前配置（kept=8=peCount，单趟）下冲突被 feeder 内部吸收，未传导成 FSM 停顿 |
| 时序数 | ⚠️ | 综合后网表，**未做布局与缓冲插入**（容器里没有 OpenROAD）。是可比的相对值，不是物理可实现频率 |

## 3. 功耗：已作废，待重测

| 主张 | 状态 | 说明 |
|---|---|---|
| 全部功耗标定 | ❌ | 用 `set_power_activity -input` 测的，而该旋钮对内部网**没有控制力**（α 扫 45 倍，功耗非单调抖动 ±5%）。换 `-global` 后同一模块差 **4.8 倍** |
| EDP 排序 | ❌ | 建立在上面那些数上 |
| 基于旧功耗的 Pareto 前沿 | ❌ | 见 `results/superseded/README.md` |
| 活动率 α | ⚠️ | 实测手段已建（`vcd_activity.py`，RTL 级 VCD）。**不是逐网精确**：`-global` 对所有网一视同仁，会高估深层逻辑；消除它要门级 VCD，而 PDK 只有 `.lib` 没有 Verilog 单元模型 |

**在重测并验证外推之前，功耗与 EDP 不进任何排序判据**（`ObjectiveSpec.pareto_axes` 里没有 `power`）。

## 4. 代价模型

| 主张 | 状态 | 说明 |
|---|---|---|
| 总工作量不随分块变化 | ✅ | `head_dim` 是必填参数；改 `tile_d` 不再改变 cycles |
| 稠密预测是 O(N²) 下限 | ✅ | 稀疏度 0.95→0.99 时 cycles 饱和 |
| 搜索空间 = 11,520 | ✅ | 原 1,658,880 里有 **5 个惰性维度**（改变时七个指标全不变），虚增 144 倍 |
| 取数减速系数 | ⚠️ | 按**算法名查表**，没标定过的算法静默继承 xm 的值。出处已可见（`measured:` / `fallback:`），但仍是人工标定的知识 |
| 阶段覆盖 | ⚠️ | selection/TopK、softmax、索引控制、片上片外搬运的成本被并进 `memory_slowdown` 一个系数 |

## 5. Agent 循环

| 主张 | 状态 | 说明 |
|---|---|---|
| 五层闭环可运行 | ✅ | 真实 Vertex 调用，L2 真实 RTL 仿真，分层重入 |
| RTL 变异落地并经门验证 | ✅ | elaborate + 仿真 + 综合 + STA，失败回退 |
| 共享板记录完整轨迹 | ✅ | 主键含 `round_index`，喂 Critic prompt |
| 收敛判据 | ✅ | 瓶颈耗尽 / 无进展，由 orchestrator 强制而非交给 LLM |
| 约束优化 | ✅ | min L(x) s.t. ε/面积/功耗/频率，输出帕累托表而非单点 |
| 变异的实际收益 | ⚠️ | 实测三次 accepted 的变异关键路径只动了 0.01~0.9%。`gate_metrics` 现在可见，但**没有「改进不足就拒绝」的门槛** |
| 等预算方法对比 | 🚧 | 随机/Sobol proposer 未实现；旧结果已作废 |

## 6. 算法与质量

| 主张 | 状态 | 说明 |
|---|---|---|
| 精度是约束不是目标 | ✅ | ε 门是二值的；Critic prompt 带真实反例（loss +0.0271 那个被抛弃的点快一倍） |
| X:M 契约类型化 | ✅ | 保留 `kept_high`/`kept_low` 两档，不用单个 kept 数替代 |
| tile 抓取身份 | ✅ | 带 `reference_semantics` / 内容哈希；匹配检查四维 |
| **L2 验证范围** | ⚠️ | 参照是**固定 top-n**，不是 X:M。testbench 把参照选的列驱动进硬件再比输出，所以验的是「给定保留列后执行通路对不对」，**硬件自己的选择语义没有被验证** |
| Q8.8 输出与 DynaX 对齐 | 🚧 | 未做 |

---

## 复现入口

| 做什么 | 怎么跑 |
|---|---|
| 单元/控制测试 | `python -m pytest tests -q` |
| tile 数值验证 | `sbatch slurm/rtl/fast_attention_tile.slurm` |
| 控制 FSM 验证 | `sbatch slurm/rtl/fast_tile_top_verify.slurm` |
| 完整系统 + bank 扫描 | `sbatch slurm/rtl/fast_system_verify.slurm` |
| 扇出对照实验 | `sbatch slurm/rtl/fast_broadcast_fanout.slurm` |
| 功耗重标定 | `sbatch slurm/rtl/fast_power_recalibrate.slurm` |
| 协同设计循环 | `sbatch slurm/rtl/fast_codesign_l2.slurm`（`MAX_AREA_UM2=` 等给约束） |
