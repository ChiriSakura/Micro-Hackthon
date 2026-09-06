# 图表

本目录的 PNG 全部由脚本从 `results.json` 重新生成，不要手工编辑。
所有数字都来自真实公开模型在 WikiText-2 上的实测，不是方法的标称比例。

## 重新生成

结果类图表（Pareto、成本/稀疏度、逐层热力图、块占用率）：

```bash
source /scratch/gz2522/gz2522/tmp/micro-hackthon/env/dynax-py312/bin/activate
python FAST/scripts/plot_results.py \
    --results /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/eval_matrix_cpu_*/results.json \
    --out FAST/figures
```

注意力掩码图需要跑真实前向捕获掩码，必须走 Slurm，不要在登录节点跑：

```bash
sbatch slurm/kernel/dynax_plot_masks_cpu.slurm
```

可用环境变量覆盖：`FAST_PLOT_MODEL`、`FAST_PLOT_SEQ_LEN`、`FAST_PLOT_LAYER`、
`FAST_PLOT_HEAD`、`FAST_PLOT_METHODS`、`FAST_PLOT_OUT`。

## 各图含义

| 文件 | 内容 | 要点 |
|---|---|---|
| `block_occupancy.png` | 稀疏率 vs 64 宽列块占用率，四个运行叠在一张图 | 同样的稀疏率，N:M/SALO 恒 100%，X:M 只有 28–45%；只有 X:M 允许硬件整块跳过 |
| `pareto_<模型>_seq<长度>.png` | 稀疏率 vs 相对困惑度损失，标出 Pareto 前沿 | 每个模型/序列长度一张 |
| `cost_sparsity_<模型>_seq<长度>.png` | 左：精度代价条形图；右：实测稀疏率条形图 | 蓝色为前沿上的配置 |
| `per_layer_<模型>_seq<长度>.png` | 逐解码层保留比例热力图 | X:M 与 Sanger 随层变化，N:M/Top-K 是平的横条——动态与静态预算的直接证据 |
| `attention_masks.png` | 单层单头的真实注意力掩码 | 第一格是 dense 注意力概率（对数），其余是各方法实际保留的位置 |
| `kept_per_row.png` | 每个查询行保留了多少个注意力值 | X:M 的保留数随行变化，N:M 是常数 |
| `mask_stats.json` | 掩码图对应的数值 | 因果掩码内统计，非全矩阵 |

## 边界

- 每个配置只测了 8 个窗口（约 4 千 token），CPU float32。可以支持方法之间的
  相对排序和链路可复现性，不足以作为论文级 perplexity 结论。
- `attention_masks.png` 取的是单层单头的一个窗口，是定性示意，不是全模型统计；
  全模型统计看 `per_layer_*.png` 和 `results.json`。
- 图中不含任何周期数、面积、功耗——Evaluator 仍是 deterministic 后端，
  这些数字目前没有硬件依据。
