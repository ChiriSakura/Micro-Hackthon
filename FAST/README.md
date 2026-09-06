# FAST — 动态稀疏注意力的全栈 Agent 协同设计

FAST（Full-stack Agentic Co-design for Dynamic Sparse Attention）用五个 Agent
把「算法稀疏化 → 调度 → 微架构 → 评估 → 归因」串成一个闭环，基准是 DynaX
（ASPLOS'25）的动态 X:M 稀疏注意力加速器，工作流控制平面是 CHIA。

这个项目的核心主张不是「Agent 能自动设计硬件」，而是：

> **协同设计里最容易出错的不是搜索，是把不同置信度的证据当成同一种东西。**

所以框架里每个结论都带 `fidelity` 标签，每个门限都能说出自己为什么拒绝，
每个测量都记录它实际覆盖了什么配置。下面的组织方式就是围绕这一点展开的。

---

## 1. 五个 Agent 与门限

```text
ExperimentSpec
    │
    ▼
Kernel Agent ─────── 精度、稀疏率、块占用率、负载不均衡度
    │  quality gate：Δ 精度 > ε 则拒绝
    ▼
Compiler Agent ───── tile、布局、并行度、访存预测
    │  schedule gate：违反硬件约束则拒绝
    ▼
µArch Agent ──────── 从已验证 Chisel 模板组合硬件候选
    │  verified-template gate：模板没有仿真证据则拒绝
    ▼
Evaluator ────────── 功能正确性、周期、利用率、PPA、成本
    │  functional gate：仿真失配则整条结果作废
    ▼
Critic Agent ─────── 证据化瓶颈归因 + 下一轮 mutation
```

Compiler 和 µArch 实际上是**双向耦合**的，不是单向流水：
`fast/agents/cooptimizer.py` 让硬件约束反向裁剪调度空间，
停止准则是 proposal Table II 给的「Reduction or timeout」——
连续 `patience` 轮 EDP 降幅不到 2% 就停。

**三个上游仓库的分工**：`../chia/` 是工作流控制平面（Ray 调度、资源路由、
缓存、追踪），不是第六个 Agent；`../DynaX/` 是算法与 RTL 基准；
`FAST/` 只保存本项目自己的协议、门限和闭环。

---

## 2. 证据分层：L0 / L1 / L2

每个 `EvaluationResult` 都带 `fidelity` 字段，它会一路传到 Critic 的归因里。
这不是精度声明，是**这个数字是怎么来的**：

| fidelity | 含义 | `functional_passed` |
|---|---|---|
| `L0-deterministic` | 合成数据，只验证控制流跑得通 | 恒 `False` |
| `L1-analytical-shared-model` | 一阶代价模型 | 恒 `False` |
| `L2-rtl-simulation` | Chisel → Verilator → golden 向量 | **实测** |
| `L2-synthesis-nangate45` | Chisel → yosys → 面积；OpenSTA → 时序/功耗 | 不适用（不测功能） |

`L1` 那个后缀是刻意的。协同优化器用代价模型挑出获胜设计，
Evaluator 再用**同一个模型**给它打分——这时候「一致」是算术，不是确认。
`fast/adapters/analytical.py` 会把这句话写进 evidence：

```
NOT INDEPENDENT: this shares the co-optimizer's cost model, so it
cannot disagree with the choice it is scoring
```

`L2`（`fast/adapters/verilator.py`）是另一半：它跑真实 RTL，参照是独立的，
**它可以反对**。但它也不许越界——单模块仿真只能确定算术，确定不了整层周期，
所以 `cycles` / `area` / `power` 仍标为 L1，evidence 里明写：

```
cycles/area/power are NOT simulated: they remain L1-analytical
```

**参照的选择比参照的精度更重要。** 这是六个 DynaX 缺陷能被找出来的原因：

- 想发现「算错了」→ 用数据通路的 bit-exact 镜像（`ExpUnit`、`PSumSoftmax`）
- 想发现「设计得不对」→ 用「一个正确的实现应该怎样」（`SRAM` 的分 bank 读）
- 想发现「接口约定接反了」→ 用**软件本身**（两条 `PrePEArray` 通路分别对
  `quant_qk_matmul("1_2_4bit")` 和 `("1_4_6bit")`）——加速器就是为了跑这个软件，
  镜像 RTL 只能证明 RTL 等于它自己
- 想发现「代价模型在做错误的取舍」→ 用**综合工具**（见第 6 节）

---

## 3. 仓库结构

```text
FAST/
├── fast/                              # 框架本体
│   ├── schemas/models.py              # Agent 间版本化协议 + 配置哈希
│   ├── agents/
│   │   ├── kernel.py                  # Kernel Agent 与精度门限
│   │   ├── proposers.py               # 候选提议：sweep（对照）/ LLM（Vertex AI）
│   │   ├── compiler.py                # 调度生成
│   │   ├── codesign.py                # 协同设计空间、约束、一阶代价模型
│   │   ├── cooptimizer.py             # Compiler×µArch 双向耦合搜索
│   │   ├── uarch.py                   # verified-template 门限
│   │   ├── templates.py               # 模板注册表：provenance + verified_scope
│   │   ├── evaluator.py               # 统一指标检查
│   │   ├── critic.py                  # 证据化归因与 mutation
│   │   └── llm_backends.py            # Vertex AI（免 Ray 调用路径）
│   ├── adapters/
│   │   ├── base.py                    # Kernel / Evaluator 后端协议
│   │   ├── deterministic.py           # L0：控制流测试
│   │   ├── dynax.py                   # Kernel：真实 DynaX 测量
│   │   ├── analytical.py              # L1：一阶代价模型（自称不独立）
│   │   └── verilator.py               # L2：真实 RTL 仿真
│   ├── orchestrator/flow.py           # 五 Agent 顺序、门限、缓存
│   ├── runtime/                       # ChiaFunction 节点与 Ray/GCP smoke
│   └── storage/
│       ├── experiment_db.py           # 跨 Agent 共享搜索数据（Critic 跨层归因）
│       ├── sqlite.py                  # 内容哈希缓存
│       └── manifest.py                # artifact 校验值与工具版本
├── hardware/                          # DynaX RTL 的构建与验证 → 见 hardware/README.md
│   ├── chisel/                        # elaborate 入口 + Chisel 源码
│   │   ├── Elaborate.scala            #   单个 / LIST:a,b,c / ALL 三种目标形式
│   │   └── src/main/scala/            #   DynaX 源码 + FAST 的修复与补全
│   ├── golden/                        # 参照模型，按被测单元分层
│   │   ├── fixedpoint.py              #   Chisel 窄化赋值的截断行为（基础层）
│   │   ├── exp_unit.py                #   指数单元
│   │   ├── software.py                #   DynaX 自己的 Python，预测单元的判据
│   │   ├── execute_unit.py            #   RePE / RePERow / RePEArray / SRAM
│   │   └── predict_unit.py            #   TopK / softmax / PrePE / PrePEArray
│   ├── tb/                            # Verilator testbench + golden.h
│   │   └── gen_ports.py               #   按阵列尺寸生成端口访问（64×8 有 512 个）
│   └── gen_golden.py                  # 命令行入口（薄）
├── scripts/
│   ├── l2_closed_loop.py              # 协同优化 → 真实 RTL 仿真确认
│   ├── synthesize_modules.py          # 综合全部模块 → 面积/时序/功耗
│   ├── setup_hammer_nangate45.py      # 修补 hammer 上游的 4 处缺陷（幂等）
│   ├── build_report.py                # eval 结果 → Markdown 表 + JSON
│   ├── plot_results.py                # → figures/
│   ├── summarize_eval.py              # results.json → 汇总
│   └── gcp_*.{py,sh}                  # GCP 预检、渲染、bringup、清理
├── configs/
│   ├── experiments/                   # 固定候选与预算
│   └── chia/*.example                 # 无凭据的集群拓扑模板
├── figures/                           # 实测生成的图（稀疏度、Pareto、块占用等）
├── docs/
│   ├── GCP接入.md                      # GCP 拓扑、边界与执行顺序
│   └── results/                       # 实测表格与汇总 JSON
└── tests/                             # 150 个测试
```

仓库根目录：

```text
../slurm/env/      环境构建（DynaX / FAST 各一套 scratch 隔离环境）
../slurm/kernel/   DynaX 模型评估、掩码可视化、pytest
../slurm/rtl/      Chisel elaborate + Verilator 验证
../slurm/loop/     FAST 闭环、Kernel 搜索、L2 闭环
../slurm/cloud/    CHIA smoke、GCP bringup、出网探测
../FAST_实验执行计划.md    全项目进度、证据、风险
```

---

## 4. 怎么跑

按证据强度从弱到强，四条路径：

### 4.1 控制闭环（秒级，无需外部环境）

```bash
python -m pytest tests/ -q               # 150 passed
fast-smoke --run-dir runs/smoke          # L0：只验证控制流
```

### 4.2 真实算法测量（需要 DynaX 环境）

```bash
sbatch slurm/kernel/dynax_eval_matrix_cpu.slurm     # 一次模型加载，扫全部方法
python scripts/build_report.py --results .../results.json --out .../report
python scripts/plot_results.py                       # → figures/
```

`DynaX/run_eval_matrix.py` 支持参数化方法标签：`xm:N1:N2:M`、`nm:N:M`、`topk:K`。
结果见 [`docs/results/results.md`](docs/results/results.md)。

### 4.3 RTL 验证

```bash
sbatch slurm/rtl/fast_rtl_verify_all.slurm      # 10 个配置 vs golden 向量，约 1 分钟
sbatch slurm/rtl/fast_rtl_verify_paper.slurm   # 论文尺寸（大一个数量级，几分钟）
sbatch slurm/rtl/fast_rtl_elaborate_all.slurm  # 19 个配置 elaborate + lint
sbatch slurm/rtl/fast_synthesis.slurm          # yosys + Nangate45 面积
```

### 4.4 L2 闭环：协同优化的结果由真实仿真确认

```bash
sbatch slurm/loop/fast_l2_closed_loop.slurm
```

它把 L1 和 L2 的结论并排打出来，最后给一句：

```
the co-optimizer's winner IS backed by a passing RTL simulation
```

---

## 5. 硬件基准：DynaX 的实际状态

「基准可复现」不是免费的。**按发布状态，DynaX 开源的 8 个 Chisel 文件里
只有 `topk.scala` 能独立编译，而它功能是错的。**

已修复 6 个缺陷（其中 2 个 lint 干净、只有仿真能发现），补全 1 个缺失模块。
全部 10 个配置现已通过 golden 向量验证：

| 模块 | 参照 | 规模 |
|---|---|---|
| `TopK` | `torch.topk`（同一定点网格） | 8 cases / 128 lanes |
| `ExpUnitFixPoint` | 数据通路 bit-exact 镜像 | 7 cases / 116 点 |
| `PSumSoftmax` | 含截断宽度的镜像 | 7 cases / 31 点 |
| `SRAM` | 「一个正确的分 bank SRAM」 | 4 cases / 22 次读 |
| `RePE` | 逐周期 FSM 模型 | 11 cases / 157 周期 |
| `RePERow` | 结构模型 | 7 cases / 87 周期 |
| `RePEArray` | 结构模型 | 4×2 / **32×4** / **64×8**，共 344 周期 |
| `PrePE_1_2` | 逐周期 FSM 模型 | 8 cases / 116 周期 |
| `PrePEArray_1_2` | **DynaX 自己的 Python**（`1_2_4bit`） | 2×8 / **32×32**，共 624 周期 |
| `PrePEArray_1_4` | **DynaX 自己的 Python**（`1_4_6bit`） | 2×8 / **64×32**，共 780 周期 |

**`exp_unit` 是 FAST 写的，不是 DynaX 的。** DynaX 不发布这个模块，
但 5/8 文件 import 它。RePEA 和 PrePEA 的任何数字都依赖它，
所以模板注册表用 `provenance` 字段区分
（`dynax-upstream` / `dynax-patched` / `fast-reconstruction`），
Critic 归因时会读到，测试强制非 upstream 的模板必须写明改了什么。

**论文尺寸（DynaX-S 32×4 / 32×32，DynaX-L 64×8 / 64×32）已全部验证**，
见 `slurm/rtl/fast_rtl_verify_paper.slurm`。做这一步时论文尺寸暴露了小实例
掩盖的一个问题：沉降时间必须是 `height + 链长`（脉动延迟本身），height=2
时留 `columns+4` 也能过，height=32 时前几行正确、后面逐行衰减到 0。

**`verified` 是关于证据的断言，而证据是有规模的。** `verified_scope` 字段
记录每条记录实际覆盖的配置，以及两条源码从未说明的约束：预测阵列每组必须
按**下标降序**喂（1:2 和 1:4 同一条规则），以及 K 必须按链长压小，
否则 `exp(psum)` 饱和会让测试失去区分力。测试强制 verified 的模板必须
填这个字段。

细节见 [`hardware/README.md`](hardware/README.md)。

---

## 6. 综合：把面积、时序、功耗从「猜的」变成「量的」

`codesign.py` 的一阶面积公式从来没有被任何工具校准过，协同优化器却在用它
排序。一个把面积算错 3 倍的公式，在 Pareto 前沿上和正确公式看起来一模一样。

```bash
sbatch slurm/rtl/fast_synthesis.slurm     # yosys 出面积，OpenSTA 出时序与功耗
```

三者**共用同一份映射网表**——否则面积和时序可能在描述两个不同的电路。

工艺是 **Nangate45（开源 45nm）**，不是论文的 28nm 商业工艺。绝对面积不可与
论文的 1.08 / 6.05 mm² 比较；能比的是设计之间的相对关系，而那正是协同优化器
需要的。

### 实测暴露的不是「不准」，是「取舍做错了」

| 模块族 | 族内一致性 | 标定系数 |
|---|---|---|
| `topk_area_units` | 1.08× → 形式正确 | 45.3 µm²/unit |
| `array_area_units` | 1.07× → 形式正确 | 1146.2 µm²/unit |

族内一致说明公式的**形式**是对的；**族间差 25.3 倍**说明预测单元和执行单元
的相对权重错了。协同优化器恰恰在用 `kept_per_block`（预测单元面积）换阵列
规模（执行单元面积）——这个偏差直接改变它选出哪个点。

按实测标定后，四个配置误差 3.3–3.8%，并有测试钉住。`max_area_units` 也随之
改名为 `max_area_um2`：单位变了名字不跟着改，正是这个项目在别处反复防的
静默错配。

### 实测结果（Nangate45，理想时钟、无线延迟）

可信的时序，9 个配置：

| 模块 | 面积 µm² | 关键路径 | 上限频率 | 功耗 @ 实测 α |
|---|---|---|---|---|
| `TopK_S` | 3 142 | 0.847 ns | 1180 MHz | 6.03 mW |
| `PrePE_1_2` | 464 | 0.958 ns | 1044 MHz | 0.32 mW（α=0.154） |
| `TopK` | 6 469 | 1.174 ns | 852 MHz | 13.58 mW（α=0.286） |
| `PrePE_1_4` | 1 486 | 1.206 ns | 829 MHz | 0.55 mW |
| `ExpUnit` | 626 | 1.659 ns | 603 MHz | 8.80 mW（α=0.371） |
| `RePEArray_L` | 1 591 880 | 2.222 ns | **450 MHz** | 3 243 mW |
| `RePEArray_S` | 371 999 | 2.230 ns | 448 MHz | 399 mW（α=0.078） |
| `RePE` | 2 671 | 2.308 ns | 433 MHz | 12.04 mW（α=0.194） |
| **`PSumSoftmax`** | 2 218 | **14.825 ns** | **67 MHz** | 121.7 mW（α=0.306） |

**系统瓶颈是 softmax 归一化器，不是 PE 阵列。** `FixedPointDiv` 把
`(num << point) / den` 做成一次**纯组合除法**——252 级逻辑、14.8 ns，比其他
所有模块慢 6 倍。执行阵列在 450 MHz 附近（已经略低于论文的 500 MHz），
而除法器只有 67 MHz。

这对协同优化器有直接含义：**如果它在调阵列规模，而时钟由除法器决定，
它优化的是错的东西。** 真实设计里这个除法器需要流水化或换成倒数近似。

### 一道守卫，以及它拦下了什么

`SRAM`、`SRAMBank`、`PrePEArray_S/L` 的时序被判为**不可信**：单级延迟
6.8～196.2 ns，而 45nm 标准单元约 0.02–0.1 ns。起点都是广播到成百上千个
负载的控制信号——**综合后的网表没有插过缓冲，那是布局布线干的活**。

这不是工具配置问题，是流程本身的边界，也是把 hammer 的 `par` 打通的硬理由：
不做 P&R 就拿不到高扇出设计的可信时序。

守卫的判据是**单级延迟**而不是总延迟：`PSumSoftmax` 总延迟 14.8 ns 但每级
都在 0.35 ns 以内（252 级），所以它可信；`PrePEArray_L` 总延迟 229 ns 却只有
7 级，其中一个 NOR2 报 196 ns，所以它不可信。两者靠总延迟分不开。

这道守卫是被咬过之后加的——我差点把那批伪影当成「DynaX 达不到 500 MHz」
报出去。

### 功耗：难点不在工具，在 α

功耗 = 泄漏 + 内部 + 翻转。后两项**严格正比于翻转率 α**。同一份网表只改 α：

| α | 总功耗 | 泄漏 |
|---|---|---|
| 0.05 | 1.199 mW | 14.8 µW |
| 0.20 | 4.751 mW（4.0×） | 14.8 µW |
| 0.50 | 11.854 mW（10.0×） | 14.8 µW |

所以**用工具默认的 α 等于给出一个任意数**，更糟的是那个数和稀疏度完全无关，
而 DynaX 省的恰恰就是翻转。拿它做协同优化，等于让优化器看不见稀疏化的
主要收益。

`activity_from_stimulus()` 因此从**实际施加的激励**里数出 α，而不是取默认值。
`activity_source` 字段跟着结果走，说明这个 α 是数出来的还是假设的。

实测的 α 跨度是 **0.033（PrePEArray_S）到 0.371（ExpUnit），11 倍**。用默认
0.2 会让 PrePEArray_S 的功耗高估约 6 倍——这就是「测」和「猜」的差别。

**当前边界**：激励是验证向量（随机控制走查、饱和边界），不是真实注意力
负载的轨迹。所以现在的功耗是「该验证激励下的功耗」。要让它随稀疏配置变化，
需要用真实 Q/K 生成激励——接口已留好，`activity` 是入参。

再上一档是门级 VCD（OpenSTA 支持 `read_power_activities -vcd`，内部节点也
实测），需要 Nangate45 的 Verilog 单元模型，当前拿不到。

### hammer：能用，但要先修四处上游缺陷

`scripts/setup_hammer_nangate45.py`（幂等）修完之后，hammer 的 `syn` 完整
走通，产出 `mapped.v`、`.sdc` 和能喂给 `syn-to-par` 的 `syn-output.json`——
面积 629.09 µm²，和直驱 yosys 的 625.90 差 0.5%。

| # | 缺陷 | 性质 |
|---|---|---|
| 1 | `Stackup` 缺 `grid_unit` | 数据（×1） |
| 2 | 每个 `Metal` 缺 `grid_unit` | 数据（×10） |
| 3 | `max_width` 哨兵值不对齐网格 | 数据（×10） |
| 4 | `latch_map_file` 未设时生成 `techmap -map None` | **插件代码 bug**（Python 的 `None` 被字符串化写进 tcl） |

另有两处是配置而非缺陷：`yosys_bin` 必须显式给（不走 PATH）；PDK 路径是
`<install_dir>/lib/` 而不是 `<install_dir>/nangate45/lib/`——hammer **替换**
`nangate45/` 前缀而不是拼接。

修的都是**数据**不是逻辑，所以升级 hammer 后重跑脚本即可，不必维护 fork。
走通 hammer 的价值在于 `par` / `drc` / `lvs` 可以直接经 CHIA 的 `HammerNode`
调用——**布线后的面积和功耗才是能和论文的 mm² 与 mW 对得上的量级**。

### 两条边界必须说清楚

**SRAM 的实测不用于标定。** yosys 没有存储器宏编译器，把 `SyncReadMem` 映射
成了 226703 个触发器、530247 µm²；真实芯片用 SRAM 宏会小一到两个数量级。
那个数字反映的是综合流程缺一环，不是设计的面积。所以 `sram_area_units`
明确标为**估计**，和另外两个有实测支撑的区分开。

**为什么不是 hammer。** CHIA 提供了 `HammerNode`（`chia/vlsi/hammer.py`），
hammer-vlsi 1.2.0 也自带 `synthesis.yosys` 和 `technology.nangate45`。但那个
组合当前跑不通——hammer 自带的 `nangate45.tech.json` 过不了 hammer **自己的**
pydantic 校验（`grid_unit` 位置不对；补上后又卡在 `max_width` 不对齐网格）。
两处都在上游。所以 `fast/adapters/synthesis.py` 直接驱动 yosys，经
`fast/runtime/chia_nodes.py:synthesis_node` 走 CHIA 的资源路由；等有了可用的
PDK 和 tech plugin，`HammerNode` 是原位替换。

顺带记一个坑，它**在两条独立路径上各咬了一次**：`yowasp-yosys`（纯 pip、
免 root）装得上但用不了——WASI 起不了外部进程，综合会在 ABC 那一步**静默
停下并返回 0**。第一次是在直驱流程里，第二次是把它喂给 hammer 时——hammer
一路修到最后卡在「没有 mapped.v」，根因还是它。适配器因此以「输出里有没有
面积行」为判据，不看退出码。

---

## 7. 门限：什么情况下会失败

| 门限 | 触发条件 | 结果 |
|---|---|---|
| quality | Kernel 精度损失 > ε | 后续阶段全部 `SKIPPED` |
| schedule | 调度违反硬件约束 | µArch 不执行 |
| verified-template | 模板无仿真证据 | 候选 `FAILED`，`allow_unverified=True` 可探索但仍报 `FAILED` |
| functional | RTL 仿真失配 | 整条 `EvaluationResult` 判 `FAILED`，周期数不再有意义 |

设计上的一条硬规则：**门限拒绝时必须说出理由**。
「unverified」而不给原因，正是这个项目开始时的状态。

---

## 8. 执行后端

**Slurm**：脚本按用途分在 `slurm/` 的五个子目录里。
一条经验值得记下——一个 30 秒的作业申请 8 CPU / 1 小时时限就进不了 backfill，
会卡在 160 深的队列后面。把 9 个模块合并成一个作业、资源按实际工作量申请，
排队时间从数十分钟降到接近零。

**GCP**：已完全打通——head 在 Slurm 计算节点，worker 在 `us-central1-a`，
反向 SSH 隧道连接，7 次尝试总成本 < $0.05，每次都已销毁。
LLM 走 Vertex AI（`gemini-2.5-flash`），复用已有 ADC，不引入新密钥。
渲染出的集群配置是 gitignored 的（机器相关）。详见
[`docs/GCP接入.md`](docs/GCP接入.md)。

**凭据**：`*credentials*.json`、`*service-account*.json`、`*.pem`、`*.key`
全部在 `.gitignore` 里。凭据文件只放磁盘、给路径，不进对话也不进仓库。

---

## 9. 当前状态

已完成：

- 五 Agent 协议、门限、证据化 Critic、SQLite 内容哈希缓存、完整 manifest
- Kernel 接入真实 DynaX 测量：2 个模型 × 最多 4 种序列长度 × 9 种方法
- Compiler×µArch 双向耦合搜索（硬件约束反向裁剪调度空间）
- 跨 Agent 共享实验数据库，含 `cross_layer` 视图供 Critic 跨层归因
- **DynaX 全部 RTL 通过 golden 向量验证**（6 个缺陷 + 1 个补全模块），
  含**论文尺寸** DynaX-S / DynaX-L；两条预测单元通路（1:2 / 1:4）
  都以 DynaX 自己的 Python 为判据
- L2 Evaluator 后端：`functional_passed` 从常量变成实测
- **面积模型经 yosys + Nangate45 实测标定**，修正了预测单元与执行单元
  25.3 倍的相对权重偏差
- CHIA/Ray 五节点任务图 + GCP 实机打通
- **时序与功耗**：OpenSTA 实测，α 从实际激励数出；hammer 的 `syn` 也已打通
- 150 个自动化测试

尚未完成：

- **高扇出设计的时序**：4 个配置（SRAM、SRAMBank、PrePEArray_S/L）拿不到
  可信时序，因为综合后没有插缓冲。要靠 hammer 的 `par`
- **功耗的 α 仍来自验证向量**，不是真实注意力负载的轨迹。要让功耗随稀疏
  配置变化，需要用真实 Q/K 生成激励；再上一档是门级 VCD
- **布局布线**：hammer 的 `syn` 已通，`par` 还没跑。综合后面积不含布线，
  和论文的 mm² 差一个系统性因子
- **除法器是系统瓶颈**（67 MHz vs 阵列的 450 MHz），但协同优化器的搜索空间
  里还没有「除法器实现方式」这个维度
- **28nm 对齐**：Nangate45 是开源 45nm，和论文的 1.08 / 6.05 mm² 不可直比。
  要对齐需要商业 PDK，或至少一次跨工艺的缩放校准
- **SRAM 面积仍是估计**：yosys 没有存储器宏编译器，实测反映的是流程缺一环
- 论文描述但仓库没有的模块：N-index / X-index buffer、X:N 剪枝、
  block scheduler（Algorithm 1）、DynaX-S/L 顶层
- 多种子的 sweep vs LLM 提议对照实验

---

进度、证据与风险详见 [`../FAST_实验执行计划.md`](../FAST_实验执行计划.md)。
