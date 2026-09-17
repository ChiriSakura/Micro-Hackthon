# 历史工具

此目录保留可追溯、仍可按旧协议调用的早期工具。集群脚本已更新到新路径。

| 文件 | 历史用途 | 当前替代 |
|---|---|---|
| `l2_closed_loop.py` | L1 搜索后单模块 L2 验证演示 | `fast.fullstack.cli`，完整系统生成 |
| `design_ppa.py` | 分别综合组件再求和 | 完整生成顶层的 Hammer PPA；历史 inventory 用 `../run_final_inventory.py` |
| `build_report.py`、`report_template.html` | 初期 DynaX 算法评估 HTML | 当前逐轮指标用 `../report_generated_run.py` |
| `plot_results.py`、`summarize_eval.py` | 初期模型评估图表和汇总 | 历史数据专用 |
| `report_threshold_bringup.py` | 硬编码 threshold-attention / 预布局范围的早期归档报告 | `../archive_generated_run.py` + `../report_generated_run.py` |

这些代码不参与当前 `FullStackFlow`。通用修复应进入 `fast/`；不要在本目录增加新的主线实现。
