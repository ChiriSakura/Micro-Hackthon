# 联合重搜索中的 Critic

`DynaXRediscovery` 和独立验证后的 `refine_rediscovery.py` 现在都接入现有的 `CriticAgent` / `LLMCriticAgent`，输出继续使用 `Critique` 与 `Mutation`，没有新增一个角色。

```text
算法提议 → DynaX 质量测量 → 质量门
             ↓                  ↓
       Critic 算法分析       硬件批次评估 → Critic → 一字段干预
             ↓                    ↑                ↓
       下一批真实测量              └── 下一批评估 ──┘
                                      ↓
                               前沿 RTL/STA 验证 → Critic 复核
                                      ↓ 失败
                        Critic → 新配置 → 独立验证 → 再分析
```

## 读哪些代码

| 位置 | 作用 |
|---|---|
| [critic.py](../fast/agents/critic.py) 的 `review_search` | 规则 Critic 的搜索接口 |
| [llm_critic.py](../fast/agents/llm_critic.py) 的 `review_search` | LLM 分析、解析、可执行性校验、规则回退、调用记录 |
| [rediscovery_critic.py](../fast/agents/rediscovery_critic.py) | 实际上下文、允许的动作、证据路径检查、候选执行及结果回写 |
| [rediscovery.py](../fast/agents/rediscovery.py) | 接入算法批次和硬件批次；连接 review ID 与 design ID |
| [refine_rediscovery.py](../scripts/refine_rediscovery.py) | 独立验证后逐个候选迭代，上一轮的新结果进入下一轮分析 |

Critic 的搜索提示词只使用当前参数域、约束、搜索历史和独立验证证据，不沿用旧五 Agent 提示词中的固定校准表。LLM 的不合法动作会留下回退原因；不能把规则回退的收益算给 LLM。

## 哪些动作会真正执行

- **算法阶段**：`kernel / candidate / set / 合法且未测量的标签`。候选进入下一批 DynaX 测量，仍必须通过质量门。规则版在质量失败时可建议相同 M、阈值下增加保留数。
- **硬件阶段**：`compiler / 某个硬件字段 / set / 域内值`。从明确的 parent point 出发只改一个字段，拒绝重复点，占用下一批已有预算中的一个名额。
- **独立验证阶段**：先分析并记录结果；如果前沿全部被拒，再进入单独计费的修正预算。每次修正完成后把新验证结果交给下一轮 Critic。

当前入口不执行 Critic 建议的 RTL 重写或功耗模型重标定；这些动作不会被伪装成已经执行。RTL 修改仍使用 FiveAgentFlow 的既有路径。Critic 不能更改 epsilon、目标频率、面积预算或测量结果。

`attribution` 表示问题归因，`mutation.layer` 表示执行动作的角色，可以不同。例如硬件时序问题可以通过 Compiler 调整 queue 参数解决；可执行性按动作字段和合法域检查。

## 启用与消融

```bash
# 完整 LLM 搜索：LLM proposer + LLM Critic（auto 默认）
python scripts/run_dynax_rediscovery.py --config CONFIG --out NEW_RUN \
  --method llm --critic auto --seed 0 --dynax-python DYNAX_PYTHON \
  --gcp-project PROJECT

# 同一 proposer、域、seed、工具预算，关闭 Critic
python scripts/run_dynax_rediscovery.py --config CONFIG --out CONTROL_RUN \
  --method llm --critic off --seed 0 --dynax-python DYNAX_PYTHON \
  --gcp-project PROJECT
```

Critic 模式为 `auto|llm|rule|off`。`random + auto` 使用规则 Critic，纯随机对照应选择 `random + off`。Slurm 入口通过 `FAST_CRITIC` 设置。独立修正脚本支持相同参数，可单独重放已有失败实验。

固定预算下不根据 Critic 的 stop 提前退出搜索。该决策表示本阶段不派发干预；候选评估预算不增加，Critic 的额外 LLM 调用和耗时另行报告。

## 怎样判断它有没有起作用

查看 `search.json` / `refinement.json` 的 `critic_reviews`：

| 字段 | 含义 |
|---|---|
| `context`、`context_sha256` | 这一条分析实际看到的证据 |
| `critique` | 层归因、建议、证据路径和预期效果 |
| `fallback_reason`、`llm_call` | 是否由 LLM 成功产生，还是规则回退 |
| `outcome.before / after` | 真正送去评估的参数变化 |
| `outcome.state = evaluated` | 候选已被评估，不代表改善 |
| `outcome.model_frontier_extended` | 是否超出该算法此前的可行 L1 前沿；不是整机实测收益 |
| `outcome.independent_module_verified` | 子系统身份、完整捕获任务、源码一致性、功能与目标频率通过 |
| `outcome.independent_constraint_recovered` | 从独立验证失败恢复为通过；不表示能耗或延迟同时下降 |

`independent_improvement` / `independent_energy_improvement` 缺少相应证据时保持 null。Critic 的假设、真实参数改变、模型改善、独立约束恢复应分别报告。最后还需要同预算的 `off` 对照才能讨论 Critic 的净收益。

本轮工程回归和实际硬件复验见 [接入验证记录](results/critic_integration_20260911/RESULTS.md)。

## 5-loop 消融入口

实际完成的 24×5-loop 结果见 [消融报告](results/critic_ablation_20260911/RESULTS.md)。固定网格与证据边界见 [消融协议](results/critic_ablation_20260911/PROTOCOL.md)。

1. `prepare_critic_ablation.py`：读取已有 32-window 精度确认，冻结完整 trace，并重新验证两个不满足时序的起点。
2. `run_critic_ablation.py --study STUDY --index INDEX ...`：运行 `STUDY/protocol.json` 中一个实验单元，装配 `refine_rediscovery.py`，固定 `--budget 5 --max-loops 5`。
3. `analyze_critic_ablation.py --study STUDY --out REPORT --plots`：汇总全部单元、逐轮记录、Critic 行为和独立工具结果，检查源码/设计身份与 shadow 对照。

修正入口新增 `--seed`、`--max-loops`、`--ablation none|shadow|no_independent|local_random`、`--workload-cache`。控制逻辑集中在 [critic_ablation.py](../fast/experiments/critic_ablation.py)；验收门保持一致。`shadow` 只记录分析，`no_independent` 只对 Critic 隐藏独立证据及其派生标记，`local_random` 用随机单字段变异替代诊断。

`refinement.json` 保留历史最优已验证延迟方案的 `best_verified_design_id`，与最后一次探索的候选分开；保留成功点不会增加评估预算。`api_*.json` 保存原始模型交互，独立工具记录在每个设计目录中。uniform-activity 功耗/能量只作为 scheduler 组件估计，不代替完整任务功耗。
