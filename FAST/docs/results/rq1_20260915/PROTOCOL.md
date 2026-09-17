# RQ1：跨稀疏机制自主硬件生成（v1，2026-09-15）

研究问题：Can FAST generalize across diverse dynamic sparse-attention algorithms and automatically derive effective full-stack designs without algorithm-specific manual optimization?

本轮是四种机制各一次从零生成的探索实验。每种最多 5 个外层设计轮次，允许 Critic 提前停止；不是 5 次建议之外再加初始设计。一次运行不足以估计成功概率，后续重复实验与 Critic 消融应另列。

## 冻结的共同条件

- 16 keys、head_dim=2、value_dim=1，单条全可见 decode row。Q/K 有符号 4 bit，2 位小数；V 有符号 8 bit，4 位小数；输出有符号 16 bit，8 位小数。
- 同一精确整数 exp LUT、截断除法、低索引优先打破 Top-k 平局。算法契约是可信软件库；没有人工 RTL、预制系统计划或历史生成设计输入。
- 精度：`sqrt(sum((sparse_fixed_output - dense_float_output)^2) / sum(dense_float_output^2)) ≤ 0.05`。浮点 dense-softmax 使用完全相同的量化 Q/K/V。不是逐样本相对误差平均，也不是模型任务准确率下降。
- 校准：随机种子 20260915，2048 条随机样本加 4 个固定边界样本；所有配置完整枚举。留出：种子 20260916，4096 条随机样本，不含重复边界样本，结果不反馈给 Agent。误差包括稀疏、LUT 和输出量化误差，同时单列 dense 定点误差下限。
- RTL 独立 E2E：生成种子 17 对应的 96 随机 + 4 边界；后续额外种子 101、211、307、401、503。输出值与 mask 均需精确一致。重复边界样本不计为独立样本。
- 300 MHz 固定时钟（周期 3.333…ns），单元面积上限 200000 µm²，Nangate45 TT。真实 Hammer / Yosys / OpenROAD 放置布线及寄生提取；需 setup/hold 均非负、route DRC=0。
- 功耗为 OpenSTA 基于库、布线寄生与统一 0.1 活动率的分析值，**不是实测芯片功耗或波形驱动功耗**。能量=平均查询延迟×功耗；能效=queries/J。共同 dense 等效计算量 96 ops/query，仅用于可比换算，不以删掉的运算数制造能效增长。
- 同一提示词、模型 gemini-2.5-pro、temperature=0.2、输出预算 48000 tokens、LLM timeout=600s、工具 timeout=3600s；同一参考库。Compiler 最多 3 次，模块与组装最多 5 次，模块串行；每个任务 SLURM 最多 4h。
- Kernel→Compiler→模块 UArch/局部验证→独立组装 UArch→算法 E2E→Hammer PPA→Critic。Critic 的全部建议、应用状态、失败和中止均保留。只有通过精度、功能、物理限制的点进入 latency–energy-efficiency Pareto。

## 四种机制与软件搜索空间

| 机制 | 软件配置 | 区别 |
|---|---|---|
| DynaX X:M | m=8；n1∈{7,8}, n2∈{4,6,7}, t0∈{2,4,6}/4, t1∈{0,1}/4 | 两块按归一化概率质量动态选 n1/n2/0 |
| Block N:M | m=8；n∈{4,5,6,7} | 每块固定配额，动态选索引 |
| Global Top-k | k∈{8,10,12,14,15} | 整行全局排名，无块配额 |
| Sanger threshold | threshold∈{1,2,3,4,6,8}/256 | 每键按 softmax 概率阈值决定保留 |

X:M 在某些输入可能全保留；需报告实际稀疏率及全保留查询比例。其余配置空间不提供全保留常量配置。不得把退化稠密点视为有效稀疏适配。所有失败配置的校准结果同样保留。

四个机制均有本地 DynaX 软件函数可核对（`models/utils/sparse_attention.py`）。数学适配含 LUT 与明确平局规则，因此并不宣称与任意原论文实现逐位一致。论文出处：[DynaX 官方仓库](https://github.com/coralabo/DynaX)、[Top-k attention](https://arxiv.org/abs/2106.06899)、[Sanger](https://liqianglu-zju.github.io/files/conference/2021/MICRO_2021_Sanger.pdf)。Block N:M 是通用块内选择契约，不声称复现某篇论文的完整架构。

## 预检查与解释范围

8-key、m=4 的 N:M 3:4 在共同预检查数据上的相对 RMSE 约 8.8%，不满足 5%。因此在主实验之前统一改为 16-key、m=8，保留相同随机分布与精度阈值。校准枚举显示四种机制各有非稠密可行配置；该结果仅验证软件配置可行，不代表硬件成功。

本轮可支持的结论是：在共同小规模定点契约和共享参考库下，对四种选择机制的自主跨层适配能力。不能外推到任意注意力算法、真实大模型准确率或大规模吞吐，也不能仅靠这轮证明取代人工专家优化。后续需要真实模型 QKV、规模扩展、人工/模板基线、多次重复与预算匹配的 Critic 消融。

主运行之前记录源码/任务/库 hash；冻结后不按算法人工修改提示词或 RTL。通用框架故障如需修复，保留原失败 cohort，并给新运行单独版本，禁止混合计算成功率。
