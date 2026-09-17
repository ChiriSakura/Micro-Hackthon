# FAST：参考库驱动的全栈硬件协同设计

RQ1：**Can FAST generalize across diverse dynamic sparse-attention algorithms and automatically derive effective full-stack designs without algorithm-specific manual optimization?**

FAST 从只读算法契约与硬件参考库出发，由 Kernel 分析算法、Compiler 规划并分派模块、UArch 编写和组装系统，经独立 E2E 验证与 PPA 提取后，由 Critic 分析并迭代。优化目标是在质量、面积、频率约束下，降低 **Latency**、提高 **Energy Efficiency**。

**当前结果：四种稀疏机制均已有满足300 MHz、输出RMSE≤5%的小规模硬件设计。** 原RQ1四算法各5候选，DynaX、Global Top-K、Sanger获得独立合格点；Block N:M原五轮未通过时序，后续外部诊断辅助FAST将15级串行最大值比较改成4层平衡树，独立验收通过，单列为A1。DynaX R5相对首个可行点能效提高23.2%；Sanger保留R1；N:M A1达到233.33 ns、41780.89 µm²、13.416 mW。规模为16 keys、head_dim=2、value_dim=1，功耗为布线后EDA建模；这些是跨版本开发与恢复证据，不能称为4/4统一自主泛化成功。

## 从这里开始

| 目的 | 入口 |
|---|---|
| 20 分钟读懂项目 | [阅读指南](docs/quick-reading-20260913.md) |
| 当前能力、限制与验收证据 | [状态表](docs/STATUS.md) |
| 模块职责与调用关系 | [架构说明](docs/agent-architecture.md) |
| 最终配置、硬件、PPA 与 Critic 过程 | [RQ1总报告](docs/results/rq1_completion_20260917/RQ1_SUMMARY.md) |
| 最终设计源码与配置 | [四算法设计代码](docs/results/rq1_completion_20260917/designs/README.md) |
| 启动新实验或断点恢复 | [全栈运行与恢复](docs/fullstack-generation.md) |
| 汇报 PPT 的论证顺序 | [汇报提纲](docs/presentation-outline-20260913.md) |
| 历史对照与失败记录 | [结果索引](docs/results/README.md) · [历史索引](docs/history/README.md) |

## 工程结构

```text
FAST/
├── fast/fullstack/     当前主线：契约、Agent、调度、工具、复验、归档
├── libraries/          只读算法插件与硬件模板注册表
├── hardware/           可引用的 Chisel IP、golden 与 testbench
├── configs/fullstack/  生成任务、目标约束与预算
├── scripts/            当前验证、归档、报告，以及仍可用的实验工具
│   └── legacy/         早期 L2 / 组件 PPA / 旧报告入口
├── tests/              控制流、数值契约、工具与完整性测试
├── docs/               当前架构、复现与汇报说明
│   ├── results/        经筛选的实验记录；最新结果含独立压缩包
│   └── history/        旧状态、开发失败证据与迁移记录
└── fast/{agents,adapters,orchestrator,...}/
                        历史搜索/闭环和共享基础设施
```

`fast/agents/` 仍为主线提供 LLM 后端，`fast/adapters/` 提供部分工具适配器，不能整组删除。历史 A/B/C 路径用途见 [架构说明](docs/agent-architecture.md)。相邻 `../DynaX/` 为算法与上游参考，`../chia/` 为历史运行时依赖，`../slurm/` 为集群入口。

## 开发检查

```bash
python -m pip install -e '.[test]'
python -m pytest -p no:cacheprovider
python -m fast.fullstack.cli --help
python scripts/archive_generated_run.py --help
```

单元测试不需要 LLM、GPU 或 EDA；真实生成需要配置 Vertex 后端、Chisel/Verilator 和 Hammer/OpenROAD 环境。详细命令与已验证配置见 [复现指南](docs/dynax-autonomous.md)。
