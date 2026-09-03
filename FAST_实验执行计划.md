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
Micro-Hackthon/
├── chia/                       # CHIA 源码，可编辑安装
├── DynaX/                      # DynaX 源码及算法 smoke tests
├── slurm/                      # Torch 集群环境、CPU/GPU smoke test 脚本
├── MICRO_A3_Proposal.pdf       # 实验提案
├── FAST_实验执行计划.md         # 本文档
└── FAST/                       # 已创建：五 Agent 集成与实验工程
```

当前实际执行环境：

- 代码工作区：`/home/gz2522/Micro-Hackthon`
- 大文件根目录：`/scratch/gz2522/gz2522/tmp/micro-hackthon`
- 登录节点 Python：3.12.14；隔离环境使用 Python 3.12。
- 算法环境：PyTorch 2.5.1+cu121、CUDA runtime 12.1、Transformers 4.48.3、Datasets 3.2.0、PEFT 0.14.0、Accelerate 1.2.1、NumPy 1.26.4。
- Slurm 项目账户：`torch_pr_674_tandon_advanced`。
- 已验证 GPU：NVIDIA A100-SXM4-80GB 与 NVIDIA L40S 46 GB，驱动 580.82.07。
- 仓库 HEAD：`23a0cddda8ebcd69acc5489ad97c8abb0ce96608`；本轮 DynaX 修复仍在工作区，尚未提交。
- Deploy Key 已配置为仓库专用只读密钥。

此前记录的 Windows Conda、RTX 3060 Laptop 和 GCP 项目仍可作为外部资源，但本轮验证实际在 NYU Torch Slurm 集群完成；目前没有创建用于 FAST 实验的云端 VM。

### 2.1 本轮执行进展（2026-09-03）

阶段 0 的算法基线已从“无法导入/无法执行”推进到以下状态：

1. 仓库已通过只读 GitHub Deploy Key 克隆到当前工作区。
2. 所有 DynaX Python 文件通过 `compileall` 语法检查。
3. DynaX 稀疏 attention 核心在 A100 上通过 GPU smoke test。
4. tiny Llama 与 tiny BLOOM 均完成 Dense 前向、X:M 前向、loss 计算和一次反向传播。
5. Hugging Face tiny Llama、WikiText 数据加载和受限样本 perplexity 流程已跑通。
6. 训练、评估和 LoRA merge 五个 CLI 入口可在隔离环境中成功导入。
7. DynaX smoke tests 已固化为正式 pytest golden suite；CPU suite 与 CUDA suite 均已通过。
8. 已创建 `FAST/` 五 Agent 控制框架，并完成 deterministic 单候选闭环与缓存验证。
9. 当前没有遗留的 Slurm 作业。

关键 Slurm 证据：

| Job ID | 资源 | 验证内容 | 状态 | 用时 |
|---|---|---|---|---|
| `16902825` | A100 80 GB | X:M、N:M、Top-K、Sanger、SALO、量化 QK 核心路径 | `COMPLETED (0:0)` | 11 秒 |
| `16903641` | CPU | tiny Llama/BLOOM Dense、X:M、loss、backward | `COMPLETED (0:0)` | 19 秒 |
| `16903776` | CPU | HF tiny Llama + WikiText，2 个长度 64 样本 | `COMPLETED (0:0)` | 39 秒 |
| `16903825` | CPU | train/eval/merge CLI 单进程导入检查 | `COMPLETED (0:0)` | 21 秒 |
| `16904851` | CPU | 正式 pytest golden suite | `COMPLETED (0:0)`，10 passed、2 deselected | 22 秒 |
| `16904852` | L40S 46 GB | 正式 pytest CUDA suite：mask CPU/GPU golden 一致性、tiny Llama/BLOOM CUDA 前向与 backward | `COMPLETED (0:0)`，2 passed、10 deselected | 45 秒 |
| `16905470` | CPU | 首次 FAST 环境创建 | `FAILED (1:0)`；计算节点默认 Python 3.9，不满足 CHIA ≥3.10 | 46 秒 |
| `16905518` | CPU | Python 3.12 FAST 环境、单元测试、首次 Ray 启动 | `FAILED (1:0)`；依赖安装和 9 tests 通过，scratch 路径使 Ray socket 超过 107 字节 | 4 分 43 秒 |
| `16905643` | CPU | FAST 9 tests + 五节点 CHIA/Ray task graph | `COMPLETED (0:0)`；`functional_passed=true` | 42 秒 |

FAST 框架本地测试为 `9 passed`，并已连续执行同一候选两次；第二次报告显示 Kernel、Compiler、µArch、Evaluator、Critic 五阶段全部命中缓存。作业 `16905643` 进一步证明五个 `ChiaFunction` 可作为真实 Ray task graph 执行。Ray 的临时 socket 已改用节点本地短路径 `/tmp`，数据库和报告仍保存到 scratch。当前这些结果验证的是控制流、门限和记录机制，使用的是 deterministic adapter，不代表 DynaX 性能或精度结论。

核心测试观测值：

| 方法 | 合成输入上的保留比例 |
|---|---:|
| X:M | 0.131836 |
| N:M（16:64） | 0.250000 |
| Top-K（8/64） | 0.125000 |
| SALO | 0.170898 |
| Sanger（阈值 `1e-4`） | 1.000000 |

X:M 的逐行保留数量满足 8 或 16，N:M 和 Top-K 的基数检查准确通过。Sanger 在本次随机合成输入和阈值下没有产生稀疏性，这只是 smoke test 观测，不能作为方法效果结论。

tiny 模型端到端结果：

| 模型 | 参数量 | Dense loss | X:M loss | X:M backward loss |
|---|---:|---:|---:|---:|
| Llama | 90,432 | 4.841329 | 4.838814 | 4.838814 |
| BLOOM | 108,416 | 4.860696 | 4.860834 | 4.860834 |

固定随机种子为 `20260903`。CPU tiny-model smoke test 的两次独立运行得到相同结果。HF tiny Llama 在 WikiText 上的 smoke perplexity 为 `32102.001953125`；由于使用随机 tiny 权重和两个样本，该数值只证明加载及评估链路可执行，不代表模型质量。

本轮新增的可复用入口：

- `DynaX/smoke_sparse_attention.py`：核心稀疏算法验证。
- `DynaX/smoke_tiny_models.py`：tiny Llama/BLOOM 端到端验证。
- `DynaX/models/utils/runtime_config.py`：支持用 `DYNAX_CONFIG_PATH` 选择候选专属配置。
- `DynaX/tests/` 与 `DynaX/pytest.ini`：正式 golden suite，覆盖运行时配置、Dense/N:M/X:M、非法配置、tiny Llama/BLOOM 与可选 CUDA 路径。
- `slurm/setup_dynax_env.slurm`：在 scratch 创建固定版本环境。
- `slurm/dynax_gpu_smoke.slurm`：GPU 核心验证。
- `slurm/dynax_tiny_model_cpu_smoke.slurm` 和 `slurm/dynax_tiny_model_smoke.slurm`：CPU/GPU 模型级验证。
- `slurm/dynax_tiny_eval_cpu.slurm`：真实模型与数据集加载 smoke test。
- `slurm/dynax_pytest_cpu.slurm` 和 `slurm/dynax_pytest_gpu.slurm`：在 CPU/GPU 分区执行正式 suite 并保存 JUnit 报告。
- `slurm/setup_fast_env.slurm`：在 scratch 创建 Python 3.12 的 CHIA/FAST 隔离环境。
- `slurm/fast_chia_smoke.slurm`：执行 FAST 单元测试和真实的五节点 CHIA/Ray task graph。
- `FAST/fast/`：五 Agent schema、Agent 实现、adapter 边界、CHIA node、SQLite 内容哈希缓存和本地 CLI。
- `FAST/configs/chia/fast-gcp.yaml.example`：不含凭据的 GCP CPU worker 模板。

运行产物位置：

```text
/scratch/gz2522/gz2522/tmp/micro-hackthon/
├── env/dynax-py312/
├── env/fast-py312/
├── cache/huggingface/
└── runs/
    ├── core_16902825/result.json
    ├── e2e_cpu_16903641/result.json
    ├── pytest_cpu_16904851/junit.xml
    ├── pytest_gpu_16904852/junit.xml
    ├── fast_framework_smoke/{fast.db,report.json}
    └── fast_chia_smoke_16905643/{junit.xml,report.json}
```

本轮修复内容：

- 修复 `train_llama.py` 和 `train_bloom.py` 的 `else if` 语法错误。
- 删除未定义 `model_path` 的重复 tokenizer 加载，补充 `train_num` 参数。
- 将 checkpoint 恢复参数移动到 `trainer.train()` 的正确位置。
- 修复 BLOOM attention 中未定义的 `attn_bias` 和 `bits_w`。
- 移除 DynaX Python 路径中的硬编码 `.cuda()`，统一按张量或模型设备执行。
- 修正 perplexity 的 batch 设备、label 设备和实际 token 分母。
- 为评估增加 `max_samples`，支持低成本 smoke test。
- 评估和 LoRA merge 捕获异常后会重新抛出，避免失败被报告为成功。
- 为 N:M、X:M、Top-K 增加基本参数与形状检查。
- 显式继承 `GenerationMixin`，保持后续 Transformers 兼容性。

仍未完成或不能过度宣称的内容：

- 早期模型级 tiny GPU 作业曾因项目账户 `QOSGrpGRES` 配额被阻塞并取消；随后正式 CUDA suite 已在 L40S 上完成，因此模型级 CUDA 前向与 backward 现已有自动化证据。
- 尚未下载或运行 Llama-3-8B、BLOOM-7B1，也未产生可用于论文结论的 perplexity/accuracy 数据。
- 模型级量化 attention 尚未完成端到端验证。
- 稀疏统计仍依赖进程内全局计数器；当前通过候选独立运行目录隔离，但尚未重构为显式结果对象。
- X:M 的 `n1=16`、`n2=8`、`m=64` 仍为实现内常量。
- 正式 pytest golden suite 已建立，CPU suite 与模型级 CUDA suite 均通过；尚未覆盖目标规模模型与长序列。
- FAST 已有 schema 版本、配置哈希、SQLite 缓存和本地单候选控制闭环，但完整 manifest 与真实 DynaX/Verilator adapter 尚未完成。
- Chisel/Verilator 工程仍未开始，当前 µArch Agent 只验证“未认证模板必须被拒绝”的控制门限。

## 3. 初步审计结论

### 3.1 DynaX 软件实现

DynaX 提供了动态 X:M 稀疏注意力的训练、评估和部分硬件实现，但暂时不能直接作为自动化设计空间探索的可靠基线。

首次审计问题及当前状态：

| 问题 | 当前状态 |
|---|---|
| `train_llama.py` 和 `train_bloom.py` 使用非法语法 `else if` | 已修复并通过语法检查 |
| 训练脚本引用未定义的 `model_path` 和未注册的 `args.train_num` | 已修复 |
| 多处硬编码 `.cuda()`，造成 CPU 和多设备冲突 | 已移除；CPU 模型链路和 GPU 核心链路已验证 |
| 模型反复读取共享 `configs/config.json` | 已支持 `DYNAX_CONFIG_PATH`；runner 使用候选独立副本 |
| 评估和 merge 捕获异常后仍以成功状态退出 | 已改为重新抛出异常 |
| BLOOM attention 引用未定义 `attn_bias` 和 `bits_w` | 已修复，并通过 tiny BLOOM 前向和 backward |
| 稀疏 attention 使用共享全局计数器和日志 | 待重构；当前仅通过独立进程和运行目录隔离 |
| X:M 固定 `n1=16`、`n2=8`、`m=64`，与外部配置不完全一致 | 待参数化 |
| 自定义 attention 的训练/推理 dropout 语义 | 已在 `eval()`、dropout=0 的 smoke test 覆盖；仍需针对非零 dropout 写正式测试 |

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

FAST 必须在项目侧实现 Kernel、Compiler、µArch、Evaluator、Critic 五类角色的数据协议和控制逻辑，而不是修改 CHIA 上游核心来硬编码本项目流程。

当前已完成第一版五 Agent 控制框架：五类角色使用版本化、JSON-safe 的类型协议，CHIA driver 仅作为控制平面而不计为第六个 Agent；`ChiaFunction` 节点通过逻辑资源标签在执行时映射到本地、Slurm 所在节点或 GCP worker。该版本已经验证门限、Critic 证据约束和完整报告缓存，但 deterministic adapter 只用于验证编排，不能作为论文实验结果。

CHIA 仓库已确认原生提供 `gcp_nodes` 创建/销毁、GCP 集群 YAML、ADC/SSH 两层认证与异构 Ray worker 资源路由。新增的 `fast-gcp.yaml.example` 已通过 CHIA `load_config` 解析验证。因此后续 GCP 接入不需要改写五个 Agent，只需替换 backend adapter 和集群资源映射。实际 GCP 实例尚未创建，镜像/环境安装、费用告警和自动关机仍需在 provisioning 前完成。

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

### NYU Torch Slurm 集群

本轮算法基线实际使用该集群完成。约定如下：

- 使用项目账户 `torch_pr_674_tandon_advanced`。
- CPU 设置与 smoke test 使用 `cpu_short`。
- GPU 候选分区为 `h200_tandon,l40s_public,h100_tandon,a100_tandon`。
- 环境、Hugging Face 缓存、模型和实验产物统一放置在 `/scratch/gz2522/gz2522/tmp/micro-hackthon`。
- 代码保留在 `/home/gz2522/Micro-Hackthon`，不在 home 下保存大模型和虚拟环境。
- 遇到 `QOSGrpGRES` 时不得绕过调度器；保留 CPU smoke 结果，等待项目 GPU 配额释放后再提交。

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
| Slurm 项目 GPU 配额占满 | GPU 模型级 smoke 延迟 | 先完成 CPU 端到端与 GPU 核心验证，待 `QOSGrpGRES` 释放后补跑 |
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

1. 审查本轮 DynaX 修改，为其创建独立工作分支并提交可回滚的阶段 0 基线。
2. CPU 与 CUDA 正式 pytest golden suite 已完成；下一步把 JUnit、GPU 型号与配置哈希收入完整 manifest。
3. 重构稀疏统计全局变量，并把稀疏率、索引和日志作为显式结果写入候选目录。
4. tiny Llama/BLOOM 模型级 CUDA 前向与 backward 已完成；下一步扩展到选定的公开基线模型与序列长度。
5. 使用同一公开小模型和固定 WikiText 样本比较 Dense 与 X:M perplexity，而不是使用随机 tiny 权重得出质量结论。
6. `FAST/` 工程骨架、实验 schema、配置哈希、缓存与五 Agent deterministic 闭环已完成；下一步实现真实 DynaX adapter 和完整 manifest。
7. 建立 Chisel 工程并首先验证一个最小模块。
8. 本地与 Slurm 单候选闭环稳定后，再决定是否启动 GCP CPU 实例。

阶段 0 尚未完全验收前，不执行大模型下载、大规模云端搜索或 FireSim 部署。

## 12. 第一阶段完成定义

满足以下条件后，项目才进入云端 DSE：

- [x] DynaX Python 源码通过语法检查。
- [x] Dense 与 X:M tiny 模型测试通过（CPU 前向和 backward）。
- [x] 已移除硬编码 `.cuda()`；CPU 模型链路、A100 核心链路和 L40S 模型级 CUDA suite 均通过。
- [x] 当前 Slurm runner 为每个候选使用独立配置、日志和结果目录。
- [ ] 所有失败都有非零退出码和结构化错误（非零退出已完成，结构化错误 JSON 尚未完成）。
- [ ] 至少一个 Chisel 模块通过软件 golden test。
- [ ] Verilator 可以由脚本非交互运行。
- [ ] FAST 单候选闭环能够生成完整 manifest。
- [ ] 云端费用、并发和自动关机策略已经配置。
