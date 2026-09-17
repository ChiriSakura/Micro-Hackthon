# 脚本索引

当前生成入口：`python -m fast.fullstack.cli`，或安装后的 `fast-generate`。标准任务为 `configs/fullstack/dynax_autonomous.json`。先读 [运行与复现指南](../docs/dynax-autonomous.md)。

## 当前主线

| 工具 | 用途 |
|---|---|
| `revalidate_generated_design.py` | 无 LLM 重建指定轮源码、E2E 和 PPA；支持搬迁后的归档 |
| `verify_generated_holdout.py` | 重建后增加算法种子；功能通过不代表复验后端的 PPA 可行 |
| `verify_routed_design.py` | 布线后网表的独立数值 E2E，零延时功能验证 |
| `archive_generated_run.py` | 归档 run/source/verification，逐文件 SHA-256 校验，排除缓存；从不删除输入 |
| `report_generated_run.py` | 从任意算法/后端的原始结果导出 JSON、CSV 与 Markdown，不补估算值 |
| `report_generation_comparison.py` | 匹配起点检查、ON/OFF 表格与图 |
| `verify_module_gates.py` | Verilator 模块验证基础设施检查 |
| `audit_dynax_xm_contract.py` | 原 DynaX X:M 与小型契约的语义审计 |
| `audit_rq1_semantics.py` | 四种机制与实际 DynaX 软件函数核对，保留 LUT 阈值差异与平局差异 |
| `finalize_rq1_run.py` | 主运行结束后独立留出精度、RTL/门级验证、token 记录与完整归档；不反馈给 Agent |
| `report_rq1.py` | 根据原始证据刷新四算法进度、逐轮 CSV/JSON/Markdown；不填补缺失 PPA |
| `repair_generated_assembly.py` | 显式外部辅助修复；产物不能归算为自主成功 |

核心复验逻辑在 `fast/fullstack/revalidation.py`，归档逻辑在 `fast/fullstack/artifacts.py`。脚本只负责参数、输出和工具装配。

## 仍可复现的历史实验

| 类别 | 脚本 |
|---|---|
| 参数搜索 A | `run_dynax_rediscovery.py`、`select_confirmed_candidate.py`、`run_pareto_benchmark.py` |
| 反馈修正 B | `refine_rediscovery.py`；`prepare_critic_ablation.py`、`run_critic_ablation.py`、`analyze_critic_ablation.py` |
| 旧闭环 C | `run_codesign.py` |
| 独立硬件与 inventory | `validate_pareto_scheduler.py`、`run_final_inventory.py`、`synthesize_modules.py` |
| 历史报告 | `report_critic_ablation.py`、`archive_critic_ablation.py`、`summarize_final_experiment.py`、`plot_pareto_benchmark.py` |
| 环境 | `setup_hammer_nangate45.py`、`fetch_nangate45_srams.py`、`gcp_*` |

这些入口仍被历史实验、Slurm 和测试引用。`legacy/` 专门收纳已由新入口替代的早期演示与报告，当前主线无需阅读。

- `probe_extended_references.py`：对固定版本的 Sanger / FlexCiM / bitonic 与既有 TopK 执行独立组件检查，保留失败日志；不把组件结果算作生成系统 E2E。
- `report_rq1.py` / `plot_rq1.py`：读取指定 cohort 的 jobs.json，生成逐轮结果、参考库使用审计及 latency–energy-efficiency 图；支持不同算法数量。
