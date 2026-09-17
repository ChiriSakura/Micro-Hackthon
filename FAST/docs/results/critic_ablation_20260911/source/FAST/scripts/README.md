# 脚本入口索引

所有路径以 `FAST/` 为当前目录。初读先看 [架构导读](../docs/agent-architecture.md)，再选择下面的一条执行路径。

## 搜索与闭环

| 入口 | 用途 | 主要产物/后续 |
|---|---|---|
| `python -m fast.cli` | L0 单候选控制流 smoke；可替换 Kernel 后端 | `report.json`、数据库、manifest；默认 evaluator 仍是 deterministic |
| `python -m fast.cli_kernel` | 单独搜索算法参数并测量质量 | Kernel search JSON，供 codesign 读取 |
| `run_dynax_rediscovery.py` | 从显式合法域联合搜索原 DynaX 参数和硬件，默认接入 Critic | `search.json`、分析与动作结果、候选设计、可选独立调度器验证 |
| `run_codesign.py` | 从已有 Kernel search JSON 执行 Critic 闭环 | 多轮计划、评价、归因及实验记录 |
| `refine_rediscovery.py` | Critic 分析最新独立验证结果，逐轮提议硬件修正 | 每轮分析 → 动作 → 实测结果；`--critic off` 可关闭 |
| `run_pareto_benchmark.py` | 在同一输入与配置下比较搜索策略 | 候选、前沿及预算记录 |

查看参数：`python scripts/run_dynax_rediscovery.py --help`、`PYTHONPATH=. python scripts/run_codesign.py --help`。完整真实实验配置见 [rediscovery 指南](../docs/dynax-rediscovery.md)。

## 候选确认与独立验证

| 入口 | 用途 |
|---|---|
| `select_confirmed_candidate.py` | 用扩大后的质量确认结果选择候选 |
| `validate_pareto_scheduler.py` | 重放真实 mask 工作量，验证所选调度器的功能、周期、综合和 STA |
| `run_final_inventory.py` | 冻结候选的调度器 gate 与组件面积/功耗清单；组件和不等于整机 |
| `summarize_final_experiment.py` | 汇总确认、验证及 inventory 产物 |
| `synthesize_modules.py` | 独立模块综合 |
| `design_ppa.py`、`l2_closed_loop.py` | 较早的组件 PPA / L2 演示入口，仍保留供旧作业复现 |

新系统 bring-up 入口在工作区的 `../slurm/rtl/fast_system_verify.slurm`。`fast_power_recalibrate.slurm` 用于组件功耗重测；它的产物尚未自动回填搜索模型。

## 报告与环境工具

| 脚本 | 用途 |
|---|---|
| `build_report.py`、`report_template.html` | 从实验记录生成浏览报告 |
| `summarize_eval.py`、`plot_results.py`、`plot_pareto_benchmark.py` | 汇总、结果图与前沿图 |
| `setup_hammer_nangate45.py`、`fetch_nangate45_srams.py` | 综合/工艺库准备与 SRAM 宏表 |
| `gcp_*` | 云环境配置、检查、集群管理；阅读核心框架时可跳过 |

旧实验入口仍被 Slurm 和历史报告引用，所以保留原路径。新增通用逻辑应进入 `fast/` 对应层，脚本负责参数、工具装配和产物导出。
