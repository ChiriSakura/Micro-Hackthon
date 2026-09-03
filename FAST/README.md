# FAST 五 Agent 框架

FAST（Full-stack Agentic Co-design for Dynamic Sparse Attention）是一个基于
CHIA 的动态稀疏注意力软硬件协同设计框架。

当前版本已经可以跑通五个 Agent 的控制闭环、门限、结构化结果、SQLite
缓存和 CHIA/Ray 任务图。Kernel 和 Evaluator 暂时使用 deterministic adapter
验证编排正确性，因此当前输出不能作为 DynaX 性能或精度实验结论。

## 1. 先理解整体关系

```text
ExperimentSpec
    │
    ▼
Kernel Agent ── 精度、稀疏率、索引统计
    │ quality gate
    ▼
Compiler Agent ── tile、布局、并行度、访存预测
    │
    ▼
µArch Agent ── 从已验证 Chisel 模板生成硬件候选
    │ verified-template gate
    ▼
Evaluator ── 正确性、周期、利用率、PPA、成本
    │
    ▼
Critic Agent ── 证据化瓶颈归因与下一轮 mutation
```

- **CHIA** 是工作流控制平面，负责 Ray 调度、资源路由、缓存和追踪，不是第六个 Agent。
- **Slurm 和 GCP** 是执行后端。同一个 Agent 接口可以根据 CHIA resource label 放到不同机器执行。
- **FAST** 保存本项目自己的协议和闭环；`../chia/`、`../DynaX/` 作为平行上游仓库，通过 adapter 接入。

## 2. 文件结构

```text
FAST/
├── README.md                         # 本文：中文快速上手
├── pyproject.toml                    # Python 包、依赖分组和 fast-smoke 命令
├── configs/
│   ├── experiments/
│   │   └── dynax_golden.json         # 当前固定候选/预算示例
│   └── chia/
│       └── fast-gcp.yaml.example     # 无凭据的 GCP/CHIA 集群拓扑模板
├── fast/
│   ├── cli.py                        # 本地 deterministic 闭环入口
│   ├── schemas/
│   │   └── models.py                 # Agent 间版本化输入/输出协议与配置哈希
│   ├── agents/
│   │   ├── kernel.py                 # Kernel Agent 与精度门限
│   │   ├── compiler.py               # Compiler Agent 与最小 schedule
│   │   ├── uarch.py                  # µArch Agent 与 verified-template 门限
│   │   ├── evaluator.py              # Evaluator 与统一指标检查
│   │   └── critic.py                 # 规则版 Critic、归因和 mutation
│   ├── adapters/
│   │   ├── base.py                   # Kernel/Evaluator backend 协议
│   │   └── deterministic.py          # 低成本控制流测试后端
│   ├── orchestrator/
│   │   └── flow.py                   # 五 Agent 顺序、门限和缓存控制
│   ├── runtime/
│   │   ├── chia_nodes.py             # 五个可远程执行的 ChiaFunction
│   │   └── chia_smoke.py             # 本地 Ray 五节点图 smoke test
│   └── storage/
│       └── sqlite.py                 # Head-node SQLite 元数据/结果缓存
└── tests/
    ├── test_five_agent_flow.py       # 闭环、门限、Critic 与缓存测试
    └── test_storage.py               # 内容哈希存储测试
```

仓库根目录还有两个相关入口：

```text
../slurm/setup_fast_env.slurm          # 在 scratch 创建 Python 3.12 CHIA/FAST 环境
../slurm/fast_chia_smoke.slurm         # 在 CPU 节点运行 tests + CHIA/Ray 五节点图
../FAST_实验执行计划.md                 # 全项目进度、证据、风险和下一步
```

## 3. 最快运行方式

### 3.1 已有环境：运行本地控制闭环

```bash
cd /home/gz2522/Micro-Hackthon/FAST
source /scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/activate

python -m pytest
python -m fast.cli \
  --run-dir /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fast-smoke
```

生成：

```text
runs/fast-smoke/
├── fast.db       # SQLite 缓存和各阶段结构化结果
└── report.json   # 完整五 Agent 报告
```

使用同一配置再运行一次时，报告的 `cache_hits` 应包含五个 Agent，说明没有重复执行候选。

### 3.2 从零创建环境并验证 CHIA 图

不要在登录节点直接启动长期 Ray 任务。从仓库根目录提交：

```bash
cd /home/gz2522/Micro-Hackthon
sbatch slurm/setup_fast_env.slurm
```

环境创建在：

```text
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312
```

环境已经存在时，只运行验证作业：

```bash
sbatch slurm/fast_chia_smoke.slurm
```

检查状态和日志：

```bash
squeue -u "$USER"
ls /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/
```

成功作业会生成：

```text
/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fast_chia_smoke_<job_id>/
├── junit.xml
└── report.json
```

已验证作业 `16905643`：9 个测试通过，五个 Agent 以真实 `chia_remote`
Ray task graph 执行，最终 `functional_passed=true`。

## 4. 五个 Agent 分别改哪里

| 需求 | 主要文件 | 输入 | 输出 |
|---|---|---|---|
| 接入 DynaX 真实精度与稀疏统计 | `adapters/`、`agents/kernel.py` | `ExperimentSpec` | `KernelResult` |
| 扩展 schedule 搜索空间 | `agents/compiler.py` | `KernelResult` | `CompilerSchedule` |
| 增加已验证 Chisel 模板 | `agents/uarch.py` | schedule + template registry | `HardwareCandidate` |
| 接入 Verilator/综合/GCP 执行 | `adapters/`、`agents/evaluator.py` | hardware candidate | `EvaluationResult` |
| 修改归因与搜索策略 | `agents/critic.py` | 全部上游证据 | `Critique` + `Mutation` |
| 修改闭环顺序或缓存行为 | `orchestrator/flow.py` | 五类 Agent | `RunReport` |
| 修改跨 Agent 字段 | `schemas/models.py` | — | 版本化 JSON schema |
| 修改 CHIA 资源映射 | `runtime/chia_nodes.py` | resource label | Ray task |

增加或改变 schema 字段时，应同步更新缓存反序列化、测试和
`schema_version`，避免把旧结果误当成新结果。

## 5. 门限和失败行为

- `KernelResult.quality_loss > ExperimentSpec.epsilon`：Compiler 及后续阶段跳过，Critic 归因到 Kernel。
- 模板不存在或 `verified=false`：µArch 候选失败，不能进入真实硬件评估。
- 功能验证失败：Critic 返回 `REVERT`，并引用 evaluation 日志证据。
- PE 利用率过低：当前规则版 Critic 归因到 Compiler，并建议增加并行度。
- 相同 `ExperimentSpec + template_id`：直接读取完整报告缓存。

Critic 的每条结论必须包含可检查的 `evidence` 字段，不能只输出自由文本。

## 6. GCP 使用边界

`configs/chia/fast-gcp.yaml.example` 已通过 CHIA 配置解析，但它目前只是
集群拓扑模板，不会自动创建 VM。正式使用前还要补齐经过验证的镜像或
worker 环境、预算告警、并发限制和自动关机。

准备 GCP 时建议按以下顺序：

```bash
cp configs/chia/fast-gcp.yaml.example configs/chia/fast-gcp.yaml
export HEAD_IP=<CHIA-head-address>
export FAST_SSH_USER=<ssh-user>
export GCP_PROJECT=<gcp-project-id>
export GCP_PRIVATE_KEY_PATH=<private-key-path>

gcloud auth application-default login
chia up --dry-run configs/chia/fast-gcp.yaml
```

确认 dry-run、费用上限和销毁路径后才能执行真实 `chia up`。不要把凭据、
service-account JSON 或私钥提交到仓库。

当前 GCP 规划只承担 CHIA 编排、CPU Verilator 和低成本综合。大模型 GPU
继续使用 Slurm；FireSim 最终验证仍是 AWS 后端，不能当作 GCP 功能。

## 7. 当前完成度

已完成：

- 五 Agent 类型协议和基础实现；
- 质量、硬件模板和功能门限；
- 规则版 evidence-bound Critic；
- SQLite 内容哈希缓存；
- 本地 deterministic 闭环；
- CHIA/Ray 五节点任务图；
- GCP 集群配置模板和解析验证；
- 9 个 FAST 自动化测试。

尚未完成：

- 真实 DynaX Kernel adapter；
- 完整 experiment manifest 和 artifact checksum；
- 可编译并通过 golden vector 的首个 Chisel 模板；
- Verilator、综合与 FireSim 真实 adapter；
- GCP 实例实际部署和费用保护措施。

下一步应先接入真实 DynaX adapter 和完整 manifest，再建立首个验证通过的
Chisel 模板。详细进度与实验边界见仓库根目录的
[`FAST_实验执行计划.md`](../FAST_实验执行计划.md)。
