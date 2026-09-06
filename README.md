# Micro-Hackthon — FAST 项目工作区

这个目录是 **三个独立仓库 + 一层共享执行脚本**，不是一个大工程。
先读这一节再看任何代码，因为「哪些是我们写的、哪些是上游的」是这个项目
所有结论的前提。

```
Micro-Hackthon/
├── FAST/     ★ 本项目          五 Agent 协同设计框架 + DynaX RTL 的验证
├── DynaX/      上游（ASPLOS'25）动态 X:M 稀疏注意力：算法实现 + 开源 RTL
├── chia/       上游             工作流控制平面（Ray 调度、资源路由、缓存）
├── slurm/      本项目           所有集群作业脚本，按用途分五组
├── FAST_实验执行计划.md          进度、证据、风险、边界
└── MICRO_A3_Proposal.pdf        原始设计提案
```

## 为什么不合并成一个仓库

看起来把 `DynaX/` 并进 `FAST/` 会更整齐，但那会毁掉这个项目最重要的一条性质：

1. **`git diff` 是我们证明缺陷真实存在的方式。** 我们在 DynaX 的 RTL 里
   找到 6 个缺陷。「这是上游发布的样子」和「这是我们改过的样子」必须能一条
   命令分开，否则读者无法区分我们发现了 bug 还是我们引入了 bug。
2. **`provenance` 机制依赖这条边界。** `FAST/fast/agents/templates.py` 用
   `dynax-upstream` / `dynax-patched` / `fast-reconstruction` 标记每个硬件
   模板的来源。边界一旦模糊，「DynaX 的基准数据」这句话就不成立了。
3. **两边的 Python 环境不同**，DynaX 有自己的固定版本依赖。

所以边界保留，但**必须显式**。下面这张表就是那个显式声明。

## 我们对上游改了什么

### DynaX（算法侧）

| 文件 | 改动性质 |
|---|---|
| `models/utils/sparse_attention.py` | 删除全局计数器，改为显式 recorder；X:M 参数化为 `(n1, n2, m)` |
| `models/utils/sparsity_stats.py` | ★ 新增：分布画像（行/块密度直方图、负载不均衡度、列质量集中度） |
| `models/llama_modeling.py`、`bloom_modeling.py` | 接入上面的 recorder |
| `models/utils/runtime_config.py`、`configs/*.json` | 支持参数化方法标签 |
| `run_eval_matrix.py` | ★ 新增：一次模型加载扫全部方法，按方法断点续跑 |
| `plot_attention_masks.py` | ★ 新增：掩码捕获与可视化 |
| `tests/test_sparsity_stats.py` | ★ 新增 |

上游的 `train_*.py` / `eval_*.py` / `dataUtil.py` / `qlora_merge.py` 未改动。

### DynaX 的 RTL

**没有就地修改。** DynaX 的 Chisel 源码被复制到
`FAST/hardware/chisel/src/`，修复只发生在副本上，每处都在源文件里就地注明。
`DynaX/hardware/` 保持发布原样，作为对照基准。

按发布状态，那 8 个 Chisel 文件里**只有 `topk.scala` 能独立编译，而它功能是错的**。
详见 [`FAST/hardware/README.md`](FAST/hardware/README.md)。

### chia

未改动。作为库使用。

一个值得记的边界：CHIA 的 `ChipyardHammerNode` 和 `ChiselBuildNode` 都是
**SoC 级**工具（要 Chipyard `CONFIG`、跑 RISC-V 二进制），对 DynaX 这样的
裸 Chisel 模块用不上。真正用得上的是 `chia/vlsi/hammer.py` 的 `HammerNode`
和 `ChiaFunction` 的资源路由——`FAST/fast/runtime/chia_nodes.py` 里的
`synthesis_node` 就是后者。

## 从哪开始读

| 想了解 | 去哪 |
|---|---|
| 整体架构、证据分层、怎么跑 | [`FAST/README.md`](FAST/README.md) |
| DynaX RTL 的真实状态与验证方法 | [`FAST/hardware/README.md`](FAST/hardware/README.md) |
| 实测结果表格 | [`FAST/docs/results/results.md`](FAST/docs/results/results.md) |
| 图 | [`FAST/figures/`](FAST/figures/) |
| GCP 接入 | [`FAST/docs/GCP接入.md`](FAST/docs/GCP接入.md) |
| 进度与风险 | [`FAST_实验执行计划.md`](FAST_实验执行计划.md) |

## 集群作业

```
slurm/env/      环境构建（DynaX / FAST 各一套 scratch 隔离环境）
slurm/kernel/   DynaX 模型评估、掩码可视化、pytest
slurm/rtl/      Chisel elaborate + Verilator 验证
slurm/loop/     FAST 闭环、Kernel 搜索、L2 闭环
slurm/cloud/    CHIA smoke、GCP bringup、出网探测
```

一条踩过的经验：**作业的资源申请要贴着实际工作量**。一个 30 秒的作业申请
8 CPU / 1 小时时限就进不了 backfill，会卡在上百深的队列后面；把多个短作业
合并成一个、按实需申请，排队时间从数十分钟降到接近零。

## 凭据

`*credentials*.json`、`*service-account*.json`、`*.pem`、`*.key` 全部在
`.gitignore` 里。**凭据文件只放磁盘、给路径，不进对话也不进仓库。**
