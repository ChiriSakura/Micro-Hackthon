# FAST/hardware — DynaX RTL 的构建与验证

CHIA 不参与这里。`ChiselBuildNode`（`chia/chia/chipyard/chisel_build_node.py:303`）
是在 Chipyard checkout 的 `sims/verilator` 里跑 `make CONFIG=<ConfigClass>`，
产出能启动 RISC-V 二进制的整 SoC 仿真器；它要求被测对象是挂在 TileLink/RoCC
上的 Chipyard `Config`。DynaX 的模块是裸 Chisel `Module`，没有总线接口，
所以走 scala-cli + Verilator 直路。论文自己的评估也不是 SoC 仿真
（28nm 综合 + cycle model）。

## DynaX 开源 RTL 的实际状态

8 个文件、931 行。按发布状态，**只有 `topk.scala` 能独立编译，而它功能是错的**：

| 文件 | 发布状态 |
|---|---|
| `predict_unit/topk.scala` | 编译通过，仿真错（block 边界丢最后一个元素） |
| `predict_unit/psum_softmax.scala` | **编译失败**：`SInt.resize` 在 Chisel 3.6 不存在 |
| `execute_unit/sram.scala` | **编译失败**：`Mux1H` 重载不匹配 |
| `predict_unit/prepe_1_2.scala` | **依赖缺失**：`exp_unit.ExpUnitFixPoint` |
| `predict_unit/prepe_1_4.scala` | 同上 |
| `execute_unit/repe.scala` | 同上 |
| `execute_unit/repe_row.scala` | 经 `repe.scala` 间接阻塞 |
| `execute_unit/repe_array.scala` | 同上 |

论文描述但仓库没有的：exp unit、N-index / X-index buffer、X:N 剪枝模块、
block scheduler（Algorithm 1）、DynaX-S / DynaX-L 顶层。

## 发现的缺陷与 FAST 的改动

五处改动，其中三处只是让发布的代码能编译，两处是仿真才暴露的功能缺陷，
一处是补一个整模块。每处都在源文件里就地注明，并在 `fast/agents/templates.py`
里以 `provenance` 字段区分（`dynax-upstream` / `dynax-patched` / `fast-reconstruction`）。

| # | 位置 | 性质 | 说明 |
|---|---|---|---|
| 1 | `psum_softmax.scala:26` | 编译失败 | `.resize()` 在 Chisel 3.6 的 `SInt` 上不存在 → `.pad()` |
| 2 | `sram.scala:52` | 编译失败 | 两参数 `Mux1H` 无匹配重载 → 去掉第二参数 |
| 3 | `exp_unit/ExpUnitFixPoint` | 模块缺失 | 5/8 文件 import 它，发布里没有 → **FAST 新写** |
| 4 | `topk.scala` | 功能错误 | 脉冲 valid 的同周期清 `runnerUpReg`，后赋值抹掉正在转发的值；每个 m 宽 block 丢最后一个元素，低位全部上移一名 |
| 5 | `sram.scala` bank 选择 | 功能错误 | `SyncReadMem` 是一拍延迟读，但 bank 多路选择器用**当前**地址组合选择；跨 bank 的读全部返回错误 bank 的数据 → `RegNext(bankAddr)` |

缺陷 4 和 5 都只有仿真能发现——两个文件的 lint 都是干净的。缺陷 5 的隔离方式值得一提：
`single_bank` / `repeat_read` / `write_read_interleaved` 三个 case 不跨 bank，全部通过；
只有 `bank_switch` 每次读都错。存储本身没问题，错的是多路选择器的时序。

另外记录一个不算缺陷但影响使用的性质：`RePE` 的 `acc` 和 `score_exp` 都是 `Reg`
而非 `RegInit`，**复位不清它们**，而 `acc_clear` 只清 `acc`——`score_exp` 没有任何清零路径，
只能靠跑一次 `exp_compute` 覆盖。testbench 因此每个 case 都要先驱动一段前导序列
把模块带到已知状态。

### 关于 `ExpUnitFixPoint`

DynaX 不发布这个模块。FAST 写了一个移位 + LUT 指数单元
（`e^x = 2^ki · 2^kf`，整数部分走桶形移位器，2^fracBits 项 LUT 存尾数），
调用签名 `(bits, point, 6, 4)` 读作 `(intBits, fracBits)`。
加 4 位 guard 做舍入而非截断，把 e^x≥1 区间最坏相对误差从 6.08% 降到 2.65%。

**RePEA 和 PrePEA 的任何数字都依赖这个我们自己写的单元，不能当作 DynaX 基准报告。**

## 当前结果

`slurm/rtl/fast_rtl_elaborate_all.slurm` — 16/16 配置 elaborate 成功，Verilator lint
0 error，含 DynaX-S（32×32 PrePEA + 32×4 RePEA）和 DynaX-L（64×32 PrePEA + 64×8 RePEA）
完整阵列（PrePEArray_1_4 32271 行 Verilog）。

`slurm/rtl/fast_rtl_verify_all.slurm` — **一个作业跑完全部 8 个模块，59 秒**。
一个作业而不是每模块一个：单模块只要 30 秒，但排队要等很久，
8 次提交就付了 8 次排队成本。资源申请也按实际工作量收紧
（4 CPU / 8G / 20 分钟）——一个 4 分钟的作业申请 8 CPU 和 1 小时时限，
backfill 根本排不进去，这才是它卡在 160 深队列后面的原因。
JVM 只启动一次，第一个模块之后的 elaborate 都是几百毫秒。

`slurm/rtl/fast_rtl_verify.slurm` — 单模块版，用于迭代某个 testbench。已验证：

| 模块 | 参照 | 结果 |
|---|---|---|
| `TopK` | `torch.topk`（同一定点网格） | 8 cases / 128 lanes，0 失配 |
| `ExpUnitFixPoint` | 数据通路的 bit-exact 镜像 | 7 cases / 116 点，0 失配 |
| `PSumSoftmax` | 含截断宽度的 bit-exact 镜像 | 7 cases / 31 点，0 失配 |
| `SRAM` | 正确的分 bank 同步读 SRAM（**不是**本 Verilog 的镜像） | 4 cases / 22 次读，0 失配 |
| `RePE` | 逐周期 FSM 模型 | 11 cases / 157 周期，0 失配 |
| `RePERow` | 由 RePE 模型组合的结构模型 | 7 cases / 87 周期，0 失配 |
| `RePEArray` | 同上（4×2 阵列） | 5 cases / 56 周期，0 失配 |

| `PrePE_1_2` | 逐周期 FSM 模型 | 8 cases / 116 周期，0 失配 |
| `PrePEArray_1_2` | **DynaX 自己的 Python**（见下） | 6 cases / 108 周期，0 失配 |
| `PrePEArray_1_4` | 同上（`"1_4_6bit"` 路径） | 6 cases / 108 周期，0 失配 |

参照的选择是有区别的，这一点重要：`SRAM` 的参照写的是「一个正确的 SRAM 应该怎样」，
所以它能发现缺陷 5；其余模块的参照是数据通路本身的 bit-exact 镜像，
所以能发现「算错」而不是「设计得不好」。用容差比对 `math.exp` 会把错误的 LUT 项
藏进容差里——这是刻意避开的。

**verified 是关于证据的断言，而证据是有规模的。** `RePEArray` 验的是 4×2，
论文的 DynaX-L 是 64×8——后者只有 elaborate 和 lint 覆盖。行链是同构的，
所以 4 行验的是同一个跨行链路，但这是**论证不是测量**。
模板注册表用 `verified_scope` 字段把每条记录实际覆盖的配置写下来，
测试强制 verified 的模板必须填这个字段。

### PrePEArray：参照必须是软件，不能是镜像

1:2 剪枝的决定不在 PE 里，在阵列的 `cycleToggle` 块：锁存一个 Q 元素、
和下一个比较、输出较大者加一个 select 位。这个 select 位对应 `top_in0`
还是 `top_in1`，源码和论文都没说——而**镜像 RTL 的参照永远答不了这个问题，
它只能证明 RTL 等于它自己**。

判据是软件：`models/utils/sparse_attention.py` 的
`quant_qk_matmul("1_2_4bit")` 定义了每对相邻 Q 元素按 |·| 取大保留、
另一个置零，再算 `Q_sparse @ Kᵀ`。**加速器就是为了跑这个**，
所以它必须复现这个结果。

结论是决定性的，而且 1:4 路径给出**同一条规则**：

| 路径 | 正确顺序 | 反向顺序 |
|---|---|---|
| 1:2（`"1_2_4bit"`） | 200/200 | 4/200 |
| 1:4（`"1_4_6bit"`） | 200/200 | 12/200 |

**每组必须按下标降序喂。** 1:2 里 `sel=1` 绑的是「先锁存的那个赢了」，
而 `sel=1` 选 `top_in1 = K[2c+1]`；1:4 里 `cycleCount==3` 时比较器看到的是
`io.left_in`→索引 0、`l_first`→1、`l_second`→2、`l_third`→3，
**索引顺序和到达顺序相反**。两者是同一个约定，1:2 的「奇数先喂」
就是它在两元素组上的特例。

这不是缺陷，RTL 在该顺序下自洽。这是一条**源码从未写下、
现在被测试钉住的使用约束**，记录在模板注册表的 `verified_scope` 里。

### 测试的边界（三条，都是刻意的）

1. **组内不取等值**——等值时软件的 `argmax` 保留最小下标，
   RTL 的每个比较都是严格 `>`，保留最大下标。这是另一个分歧，单独记录。
2. **操作数非负**——让 `torch.abs` 成为恒等，
   RTL 的无符号比较才和软件的 `argmax(abs)` 同义。
3. **1:4 的 K 压到 3 bit，Q 保持满 6 bit**——唯一可观测的输出是
   Q8.8 的 `exp(psum)`，超过 e⁷ 就饱和。满量程 6-bit 操作数会把 psum
   推到 e³¹，**每个 case 都读出 32767，测试就和自己一致了**：
   实测下，故意喂错顺序在这种情况下仍有 149/200 "通过"。
   Q 决定选择、K 只影响乘积，所以压 K 不影响被测的比较逻辑。

第 3 条是这批测试里唯一一处**测试本身差点失去区分力**的地方，写在这里
是因为它比结论更容易被下一个人重复踩。

### RePE 的控制排程

源码和论文都没写 `acc_ctrl` / `exp_ctrl` 该怎么排。它是从数据通路反推出来的，
写在 `gen_golden.py` 的 `RePEModel` 里：

| 状态 | 行为 |
|---|---|
| `acc_clear` | `acc := 0` |
| `acc_accumulate` | `a=q_in, b=reg_cols[sel_col]`，`acc += a·b` → QKᵀ 点积 |
| `exp_compute` | `score_exp := exp(acc)`，且 `io.out = score_exp` |
| `acc_move_out` | `a=score_exp`，`acc := score_exp·b`，`io.out = 旧 acc` → AV 流水 |

关键在 `io.out` 是双用途的：除 `acc_move_out` 外都输出 `score_exp`，
在 `acc_move_out` 下输出累加器。正是这一处复用，让同一棵行加法树既产出
softmax 分母 `Σⱼ exp(sⱼ)`，又产出 AV 分子 `Σⱼ exp(sⱼ)·vⱼ[k]`。

## 接入 FAST：L2 Evaluator 后端

`FAST/fast/adapters/verilator.py` 把上面这条流程包成 `EvaluationAdapter`。
它存在的意义是让 `functional_passed` **从常量变成测量**：
`AnalyticalEvaluationAdapter` 和协同优化器共用同一个代价模型，
所以它不可能反对自己选中的设计；这个后端跑的是独立参照，**它可以反对**。

两条刻意的约束：

- 单模块仿真只能确定算术对不对，确定不了整层要多少周期。所以
  `cycles` / `area` / `power` 仍然来自分析模型，evidence 里明写
  `cycles/area/power are NOT simulated: they remain L1-analytical`。
- 没有 golden testbench 的模板返回 `SKIPPED` 而不是 `PASSED`——
  「elaborate 通过、lint 干净」正是绝不能当作通过的那个状态。

一次运行是一个 Slurm 作业（JVM 启动 + Chisel elaborate + Verilator 构建），
量级是分钟不是毫秒，所以它用于确认搜索选出的设计，而不是给搜索循环里
每个候选打分。相同 (template, 参数) 的重复运行走缓存。

## 用法

```bash
FAST_RTL_TARGET=ExpUnit FAST_RTL_TOP=ExpUnitFixPoint FAST_RTL_TB=tb_exp.cpp \
  FAST_RTL_GOLDEN="--module ExpUnit" FAST_RTL_SIM="" \
  sbatch --export=ALL,FAST_RTL_TARGET,FAST_RTL_TOP,FAST_RTL_TB,FAST_RTL_GOLDEN,FAST_RTL_SIM \
  slurm/rtl/fast_rtl_verify.slurm
```
