# 脚本入口索引

新主线从 `python -m fast.fullstack.cli`（安装后为 `fast-generate`）进入：Compiler 检索只读硬件库并按模块分配参考，独立模块 UArch 分别设计并验证（默认 `module_workers=1` 顺序执行），再由独立组装 UArch 连接系统，验证/PPA 后由 Critic 迭代。见 [新框架指南](../docs/fullstack-generation.md)。

- `revalidate_generated_design.py`：不调用 LLM，校验源码哈希后重新编译、数值验证和提取 PPA。
- `verify_generated_holdout.py`：先重新编译并复验 E2E/PPA，再用额外 5 个算法种子各检查 100 次；不调用 LLM，保留逐种子日志。
- `report_fullstack_generation.py`：归档完成的生成运行，保留失败与原始角色/工具记录。
- `verify_module_gates.py`：真实 Verilator 回归，检查算术错误被拒绝、修复后通过、同步寄存器，以及可执行行为契约的正确/错误流水延迟测试；不调用 LLM。

下文为原有实验脚本的索引。

所有路径以 `FAST/` 为当前目录。初读先看 [架构导读](../docs/agent-architecture.md)，再选择下面的一条执行路径。

## 搜索与闭环

| 入口 | 用途 | 主要产物/后续 |
|---|---|---|
| `python -m fast.cli` | L0 单候选控制流 smoke；可替换 Kernel 后端 | `report.json`、数据库、manifest；默认 evaluator 仍是 deterministic |
| `python -m fast.cli_kernel` | 单独搜索算法参数并测量质量 | Kernel search JSON，供 codesign 读取 |
| `run_dynax_rediscovery.py` | 从显式合法域联合搜索原 DynaX 参数和硬件，默认接入 Critic | `search.json`、分析与动作结果、候选设计、可选独立调度器验证 |
| `run_codesign.py` | 从已有 Kernel search JSON 执行 Critic 闭环 | 多轮计划、评价、归因及实验记录 |
| `refine_rediscovery.py` | Critic 分析最新独立验证结果，逐轮提议硬件修正 | 每轮分析 → 动作 → 实测结果；`--critic off` 可关闭 |
| `prepare_critic_ablation.py`、`run_critic_ablation.py`、`analyze_critic_ablation.py` | 准备、执行、分析固定 5-loop Critic 消融 | [实验结果](../docs/results/critic_ablation_20260911/RESULTS.md)、逐轮 CSV、原始 API/工具证据 |
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

## 完整生成系统的新验证入口

| 脚本 | 用途 |
|---|---|
| `audit_dynax_xm_contract.py` | 调用原 DynaX X:M 函数审计小型 decode-row 契约及 tie/LUT 语义 |
| `revalidate_generated_design.py` | 冻结候选源码重新构建、E2E、PPA；`--ppa-backend hammer_openroad` 执行真实物理流程 |
| `verify_generated_holdout.py` | 不调用 LLM，重新构建后使用额外 seed 检查独立算法 E2E |
| `repair_generated_assembly.py` | 外部诊断辅助的组装修复：已验子模块重新构建后复用，单独标记，不能计为原自主实验成功 |
| `verify_routed_design.py` | 用同一 Liberty 功能模型验证布线后 gate netlist 的算法输出 |
| `report_generation_comparison.py` | 匹配起点校验、逐轮表格和 Latency–Energy Efficiency 图；物理与预布局分开 |

本轮配置、输出与证据边界见 [完整报告](../docs/results/fullstack_extensions_20260913/RESULTS.md)。
