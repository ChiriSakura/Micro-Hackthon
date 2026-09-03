# FAST 实验执行计划

> 项目：Full-stack Agentic Co-design for Dynamic Sparse Attention  
> 基础框架：[CHIA](./chia/)  
> 目标工作负载：[DynaX](./DynaX/)  
> 依据文档：[MICRO_A3_Proposal.pdf](./MICRO_A3_Proposal.pdf)  
> 文档日期：2026-09-03

## 1. 项目目标

本项目拟构建 FAST（Full-stack Agentic Co-design for Dynamic Sparse Attention）：一个基于 CHIA 的闭环、多 Agent、跨层协同设计系统。

FAST 不只是按顺序调用算法、编译和硬件工具，而是让不同 Agent 交换结构化证据，并由 Critic Agent 将性能瓶颈归因到具体设计层，再生成下一轮修改建议。

预期闭环如下：

```text
Kernel Agent
  │  稀疏率、精度、索引分布、张量形状
  ▼
Compiler Agent
  │  调度、分块、数据布局、负载均衡、访存估计
  ▼
µArch Agent
  │  Chisel 参数与硬件候选
  ▼
Evaluator
  │  正确性、周期、PE 利用率、PPA、运行成本
  ▼
Critic Agent
  │  跨层瓶颈归因和定向修改建议
  └──────────────────────────────► 下一轮搜索
```

最终目标包括：

1. 获得“稀疏度—模型精度—性能—面积—功耗”的 Pareto 前沿。
2. 比较完整 FAST、无 Critic 的黑盒搜索、等预算搜索和专家设计方案。
3. 验证结构化跨层反馈是否提高 PE 利用率、降低 EDP，并保持可接受的精度损失。
4. 形成可重复执行、可追溯、可缓存的开源实验流程。

## 2. 当前目录与状态

工作区结构：

```text
MICRO_Hackthon/
├── chia/                       # CHIA 源码，可编辑安装
├── DynaX/                      # DynaX 上游源码
├── MICRO_A3_Proposal.pdf       # 实验提案
├── FAST_实验执行计划.md         # 本文档
└── FAST/                       # 后续创建：集成与实验工程
```

当前环境：

- Windows Conda 环境：`C:\Users\11345\.conda\envs\chia_env`
- Python：3.10.19
- CHIA：chialoops 1.0.1，以 editable 模式安装
- google-cloud-compute：1.51.0
- DynaX：已克隆，当前提交为 `be22dda622c98a4b04721048fec2c75fed066453`
- 本地 GPU：NVIDIA GeForce RTX 3060 Laptop，6 GB 显存
- GCP 项目：`project-842e7b1d-4f04-40b2-9b0`
- GCP CLI、ADC、quota project 和 Compute Engine API 已配置

目前没有创建用于 FAST 实验的云端 VM，也没有修改 DynaX 上游源码。

## 3. 初步审计结论

### 3.1 DynaX 软件实现

DynaX 提供了动态 X:M 稀疏注意力的训练、评估和部分硬件实现，但暂时不能直接作为自动化设计空间探索的可靠基线。

已发现的问题包括：

- `train_llama.py` 和 `train_bloom.py` 存在非法 Python 语法 `else if`。
- 训练脚本引用未定义的 `model_path` 和未注册的 `args.train_num`。
- 部分代码硬编码 `.cuda()`，CPU 模式和多设备执行容易发生张量设备冲突。
- 稀疏注意力实现使用共享全局计数器和共享日志文件，不支持多个候选安全并行运行。
- X:M 实现中存在固定的 `n1=16`、`n2=8`、`m=64`，与外部配置不完全一致。
- 模型在 attention forward 中反复读取共享的 `configs/config.json`，并行 DSE 时会产生配置竞争。
- 部分评估脚本捕获异常后仍可能以成功状态退出，使编排器误判实验结果。
- 需要重点检查自定义 attention 在推理时是否错误地持续启用 dropout。

### 3.2 DynaX 硬件实现

`DynaX/hardware/` 中有预测单元和执行单元的 Scala/Chisel 源码，但缺少独立构建与验证所需的工程文件：

- 没有 `build.sbt` 或其他 Scala 构建定义。
- 没有 elaboration 入口。
- 没有 ChiselTest 或 Verilator testbench。
- 没有依赖版本锁定。
- `PrePE`、`RePE` 等模块引用仓库中缺失的 `ExpUnitFixPoint`。

因此这些文件目前应视为硬件模块片段，不能直接声称已经通过综合或功能验证。

### 3.3 CHIA 可复用能力

`chia/examples/timing_opt/` 是当前最接近 FAST 需求的参考实现，可复用以下模式：

- SQLite 实验记录和缓存。
- Agent 工具接口。
- 命令执行、失败检测和调试重试。
- Verilator 与综合结果反馈。
- 子模块并行评估。

FAST 仍需自行实现 Kernel、Compiler、µArch、Evaluator、Critic 五类角色的数据协议和控制逻辑。

### 3.4 基础设施约束

- 本地 6 GB GPU 适合小模型、短序列和功能 smoke test，不适合完整 Llama-3-8B BF16 实验。
- GCP 免费试用资金应优先用于 CPU Verilator、编排和批量低成本评估。
- GCP 免费试用账号通常不能给 VM 添加 GPU，不能把免费额度当作完整 GPU 训练预算。
- CHIA 当前 FireSim 实现面向 AWS F2/S3，不是 GCP FPGA。
- FireSim 最终验证需要单独准备 AWS 账号、F2 配额和预算。
- CHIA 的现有 Hammer 示例依赖商业综合工具和 PDK；没有许可证时只能先使用开源综合代理指标。
- 提案预算约 1207 美元，明显高于 300 美元 GCP 免费额度，必须采用多保真筛选和硬性预算上限。

## 4. 工程组织方案

建议创建第三个平行目录 `FAST/`，保存本项目代码，而不是直接把编排逻辑写入两个上游仓库。

```text
FAST/
├── README.md
├── pyproject.toml
├── configs/
│   ├── experiments/
│   ├── models/
│   └── hardware/
├── fast/
│   ├── orchestrator/
│   ├── agents/
│   │   ├── kernel.py
│   │   ├── compiler.py
│   │   ├── uarch.py
│   │   ├── evaluator.py
│   │   └── critic.py
│   ├── schemas/
│   ├── adapters/
│   │   ├── dynax.py
│   │   ├── verilator.py
│   │   ├── synthesis.py
│   │   └── firesim.py
│   └── storage/
├── hardware/
│   ├── build.sbt
│   ├── src/main/scala/
│   └── src/test/scala/
├── tests/
├── scripts/
├── runs/                       # 默认不提交大型产物
└── docs/
```

基本原则：

1. `chia/` 和 `DynaX/` 尽量保持可追踪的上游状态。
2. FAST 通过 adapter 调用两者。
3. 必须修改 DynaX 时，使用独立分支并保留小而清晰的提交。
4. 每次实验都使用独立运行目录，禁止多个任务共享可变的 `config.json`。
5. 每项结果都绑定代码提交、配置哈希、随机种子、环境和工具版本。

## 5. 分阶段执行计划

### 阶段 0：建立可运行、可信的算法基线

目标：让 DynaX 在小规模条件下正确、确定、可自动判定地运行。

任务：

- 修复训练脚本语法、参数和路径错误。
- 统一 CPU/CUDA 设备处理，移除硬编码 `.cuda()`。
- 将共享配置改为显式参数或每次运行独立配置。
- 将日志和统计数据写入候选专属目录。
- 失败时返回非零退出码，并输出机器可读错误信息。
- 固定随机种子，记录模型、数据集和环境版本。
- 为 Dense、N:M 和 X:M 建立确定性单元测试。
- 使用 tiny/random 模型或小型 BLOOM 完成端到端 smoke test。
- 对稀疏 mask、attention 输出和稀疏率进行独立 golden check。

验收条件：

- 所有 Python 文件能够通过语法检查。
- CPU smoke test 可运行；CUDA 可用时能运行小规模 GPU smoke test。
- 同一配置和种子重复运行得到一致结果。
- 非法配置和运行异常不会被误报为成功。
- 每次运行生成完整 manifest 和独立产物目录。

### 阶段 1：建立可验证的 Chisel/Verilator 工程

目标：将 DynaX 的硬件源码片段变成可编译、可测试的硬件基线。

任务：

- 创建 `build.sbt` 并锁定 Scala、Chisel 和 ChiselTest 版本。
- 补齐或实现可验证的 `ExpUnitFixPoint`。
- 增加 Verilog elaboration 入口。
- 为 `TopK`、`PrePE`、`RePE`、`RePEArray`、`SRAM` 建立模块测试。
- 从 Python/PyTorch 生成输入和 golden vectors。
- 打通 Chisel → Verilog → Verilator 流程。
- 记录周期数、吞吐量和关键硬件参数。

验收条件：

- 清洁环境中可以一条命令完成编译。
- 每个核心模块至少有正常、边界和非法输入测试。
- Verilator 输出与软件 golden model 一致。
- 未经验证的 RTL 不进入 Agent 的可复用硬件模板库。

### 阶段 2：构建 FAST 最小闭环

目标：跑通单个候选的完整 Agent 路径，而不是立即进行大规模搜索。

任务：

- 定义五类 Agent 的类型化输入、动作、输出和错误模式。
- 建立 SQLite 实验数据库和内容寻址缓存。
- 实现 DynaX、Verilator 和综合工具 adapter。
- 定义最小 compiler schedule DSL，例如分块、映射、数据布局和并行度。
- 接入 CHIA 的工具调用、重试和反馈机制。
- 实现确定性规则版 Critic，随后再接入 LLM Critic。
- 对一个固定 X:M 候选完成端到端闭环。

推荐数据流：

```text
ExperimentSpec
    ↓
KernelResult
    ↓ 精度门限
CompilerSchedule
    ↓
HardwareCandidate
    ↓ 功能门限
EvaluationResult
    ↓
Critique + LayerAttribution + Mutations
```

验收条件：

- 单条命令可以提交一个候选并得到最终报告。
- 任一阶段失败都能定位到具体 Agent 和具体产物。
- 相同候选不会重复执行已有的昂贵步骤。
- Critic 的每条建议都引用可检查的指标，而不是只输出自由文本。

### 阶段 3：多保真设计空间探索

目标：在有限预算下搜索有意义的跨层 Pareto 候选。

按成本分级执行：

| 级别 | 检查内容 | 适用候选 |
|---|---|---|
| L0 | 配置、AST、形状、静态约束、缓存命中 | 全部候选 |
| L1 | 小模型精度、稀疏率、索引统计 | 通过 L0 的候选 |
| L2 | ChiselTest、Verilator 正确性与周期 | 通过精度门限的候选 |
| L3 | 综合、面积、频率、功耗代理值 | 每轮 Top-K |
| L4 | FireSim 和高保真验证 | 最终少量候选 |

搜索空间至少包括：

- 算法层：X、M、阈值、层级稀疏策略、量化策略。
- 编译层：tile 大小、循环顺序、数据布局、双缓冲、PE 映射。
- 硬件层：PE 数量、阵列形状、队列深度、SRAM 容量、数据宽度。

每个候选必须记录：

- Accuracy、perplexity 或任务指标变化。
- 实际稀疏率、索引熵、块占用率。
- 工作量分布和负载不均衡程度。
- 估计及实际数据搬运量。
- 周期、吞吐量、PE 利用率、SRAM/DRAM 访问量。
- 面积、频率、功耗和 EDP。
- wall-clock 时间、云费用和 Agent token 消耗。

停止条件：

- 精度损失超过预设阈值。
- 功能验证失败且在限定修复次数内无法恢复。
- 连续若干轮没有 Pareto 改善。
- 达到时间、云费用或 token 硬上限。

### 阶段 4：消融实验和最终验证

目标：验证 FAST 的收益确实来自结构化跨层反馈。

至少比较：

1. Expert-designed baseline。
2. Equal-budget black-box search。
3. FAST without Critic。
4. 完整 FAST。

公平性要求：

- 使用相同候选空间和随机种子集合。
- 使用相同 wall-clock、评估次数或费用预算。
- 对同一候选使用相同验证工具与精度门限。
- 同时报告失败候选，不进行选择性隐藏。

最终候选再执行：

- 更大模型或更长序列验证。
- AWS FireSim 高保真验证。
- Hammer/PPA 流程；若缺少商业许可，则使用开源综合代理并明确标注限制。

## 6. Agent 接口建议

Agent 之间应传递结构化对象，而不是依赖聊天文本或共享配置文件。

### Kernel Agent

输入：

- 模型、数据集和序列长度。
- 稀疏方法及参数。
- 精度损失上限。

输出：

- 精度或 perplexity。
- 实际稀疏率。
- 稀疏索引和分块统计。
- 可复现的 trace/artifact 路径。

### Compiler Agent

输入：

- Kernel profile。
- 当前硬件约束。
- 可用调度动作集合。

输出：

- 类型化 schedule。
- tile、映射和数据布局。
- 数据流量与利用率预测。

### µArch Agent

输入：

- Schedule 与硬件约束。
- 已通过验证的 Chisel 模板。

输出：

- 参数化硬件候选。
- 生成的 RTL 和构建 manifest。
- 参数合法性说明。

### Evaluator

输入：

- 软件 golden vectors。
- RTL、testbench 和综合配置。

输出：

- 功能验证结果。
- 周期、利用率、流量和 PPA 指标。
- 标准化错误及完整日志路径。

### Critic Agent

输入：

- 所有上游结果和历史候选。
- 当前预算及停止条件。

输出：

- 瓶颈所属层及证据。
- 一个或多个受约束的 mutation。
- 预期影响、风险和优先级。
- 继续、回退或停止决定。

## 7. 实验记录格式

建议每次运行生成如下目录：

```text
runs/<experiment_id>/<candidate_id>/
├── manifest.json
├── kernel_result.json
├── compiler_schedule.json
├── hardware_candidate.json
├── evaluation_result.json
├── critique.json
├── stdout.log
├── stderr.log
└── artifacts/
```

`manifest.json` 至少包含：

- experiment ID 和 candidate ID。
- CHIA、DynaX、FAST 的 Git commit。
- 完整配置及其哈希。
- Python、PyTorch、CUDA、Java、Scala、Verilator 和综合工具版本。
- 随机种子。
- 开始/结束时间与执行主机。
- 输入和输出 artifact 的校验值。
- 退出码、失败阶段和重试次数。
- 云费用及 token 使用量。

## 8. 资源使用方案

### 本地机器

用于：

- 代码开发和静态检查。
- tiny/small 模型功能测试。
- 小规模稀疏 profile。
- Chisel/Verilator 单元测试。

不用于：

- Llama-3-8B BF16 完整加载和长序列评估。
- 大规模并行搜索。

### GCP 300 美元额度

优先用于：

- CPU 型 Verilator 批量评估。
- CHIA 编排和实验数据库。
- Top-K 候选的 CPU 综合任务。

策略：

- 基线没有通过前不创建高规格 VM。
- 从单台低成本实例验证启动、SSH 和环境配置。
- 设置预算告警、并发上限和自动关机。
- 每个任务完成后立即释放按时计费资源。
- 不假设免费试用额度可以提供 GPU。

### AWS

仅用于最终少量 FireSim 候选。开始前必须确认：

- AWS F2 区域与配额。
- FireSim 镜像和 S3 配置。
- 每小时费用与总预算上限。
- 自动终止和失败清理机制。

### 大模型 GPU

完整 Llama-3-8B 实验需要另行准备足够显存的 GPU。若资源暂时不可用，开发阶段使用小模型建立功能正确性，最终结果中必须明确小模型与完整模型验证的区别。

## 9. 风险与应对

| 风险 | 影响 | 应对措施 |
|---|---|---|
| DynaX 基线存在实现错误 | 搜索结果不可信 | 先完成独立 golden test |
| 共享配置造成并发污染 | 候选结果串线 | 每次运行使用不可变配置和独立目录 |
| RTL 缺少依赖和测试 | 无法使用 Verilator | 先建立最小 Chisel 工程和模块测试 |
| LLM 生成不可综合 RTL | 搜索大量失败 | 只组合已验证模板，限制 mutation schema |
| Critic 产生无证据建议 | 无法证明跨层反馈价值 | 每条建议必须引用指标和归因字段 |
| 直接运行昂贵后端 | 快速耗尽预算 | 使用 L0–L4 多保真门控和 Top-K 晋级 |
| GCP 无免费 GPU | 无法运行完整模型 | 本地小模型开发，另行安排大显存 GPU |
| FireSim 不在 GCP 上 | 基础设施不匹配 | 将 AWS FireSim 作为独立最终阶段 |
| Hammer 缺少许可证/PDK | 无法获得签核 PPA | 使用开源代理值并明确实验限制 |

## 10. 建议时间表

时间表以提案节点为目标，但以“正确性通过后才升级成本”为原则：

| 时间 | 交付物 |
|---|---|
| 9 月 3–4 日 | DynaX 修复清单、可重复算法 smoke test、FAST 骨架 |
| 9 月 5–7 日 | Chisel 工程、模块测试、PyTorch golden vectors |
| 9 月 8–11 日 | FAST 单候选端到端闭环 |
| 9 月 12–15 日 | 多保真 DSE、缓存、并行评估和 Pareto 记录 |
| 9 月 16–18 日 | Expert/black-box/no-Critic 消融实验 |
| 9 月 19–20 日 | 最终候选高保真验证、报告和开源整理 |

如果硬件依赖、许可证或云配额未及时解决，应保留完整的软件和 Verilator 实验结果，并把 FireSim/Hammer 标为有明确前置条件的增强验证，不能用未验证结果代替。

## 11. 最近下一步

下一轮实施按以下顺序进行：

1. 创建 `FAST/` 工程骨架及实验 schema。
2. 为 DynaX 创建工作分支，修复阻断运行的问题。
3. 建立 tiny 模型 Dense 与 X:M smoke test。
4. 加入独立运行目录、manifest、退出码和可复现性记录。
5. 建立 Chisel 工程并首先验证一个最小模块。
6. 在本地端到端闭环稳定后，再启动 GCP CPU 实例。

第一阶段完成前不执行大模型下载、大规模云端搜索或 FireSim 部署。

## 12. 第一阶段完成定义

满足以下条件后，项目才进入云端 DSE：

- [ ] DynaX Python 源码通过语法检查。
- [ ] Dense 与 X:M tiny 模型测试通过。
- [ ] CPU/GPU 设备处理一致，没有硬编码设备依赖。
- [ ] 每个候选拥有独立配置、日志和结果目录。
- [ ] 所有失败都有非零退出码和结构化错误。
- [ ] 至少一个 Chisel 模块通过软件 golden test。
- [ ] Verilator 可以由脚本非交互运行。
- [ ] FAST 单候选闭环能够生成完整 manifest。
- [ ] 云端费用、并发和自动关机策略已经配置。

