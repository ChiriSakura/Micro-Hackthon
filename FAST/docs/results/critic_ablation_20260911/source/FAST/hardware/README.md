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

六处改动，其中三处只是让发布的代码能编译，三处是仿真才暴露的功能缺陷，
一处是补一个整模块。每处都在源文件里就地注明，并在 `fast/agents/templates.py`
里以 `provenance` 字段区分（`dynax-upstream` / `dynax-patched` / `fast-reconstruction`）。

| # | 位置 | 性质 | 说明 |
|---|---|---|---|
| 1 | `psum_softmax.scala:26` | 编译失败 | `.resize()` 在 Chisel 3.6 的 `SInt` 上不存在 → `.pad()` |
| 2 | `sram.scala:52` | 编译失败 | 两参数 `Mux1H` 无匹配重载 → 去掉第二参数 |
| 3 | `exp_unit/ExpUnitFixPoint` | 模块缺失 | 5/8 文件 import 它，发布里没有 → **FAST 新写** |
| 4 | `topk.scala` | 功能错误 | 脉冲 valid 的同周期清 `runnerUpReg`，后赋值抹掉正在转发的值；每个 m 宽 block 丢最后一个元素，低位全部上移一名 |
| 5 | `sram.scala` bank 选择 | 功能错误 | `SyncReadMem` 是一拍延迟读，但 bank 多路选择器用**当前**地址组合选择；跨 bank 的读全部返回错误 bank 的数据 → `RegNext(bankAddr)` |
| 6 | `repe.scala:61` | 数值错误 | `mul := a * b` 把 FixedPoint(2\*bits,2\*point) 直接赋回 fpType，丢掉低 `point` 位小数——补码下那是 **floor**，误差恒为负 → 加半个 LSB 再截断（四舍五入） |

### 缺陷 6：偏差随 head_dim 累积，所以小尺寸测不出来

这一个值得单独写，因为它**通过了模块级的全部验证**才被抓到。

`RePE` 每个 head-dim 步做一次乘法再累加。单次乘积的截断误差期望是 -0.5 LSB，
方向恒为负，于是 QK^T 的偏差**随 head_dim 线性累积**：

| head_dim | 分数偏差（实测 512 个分数） | tile 测试 |
|---|---|---|
| 8 | 约 -4 tick | 32/32 通过 |
| 64 | 平均 -29.8 tick，范围 [-37,-22] | **894**/2048 超容差（1154 在容差内），**无一偏大** |

「无一偏大」是定位它的那一半证据：一个真正的算错不会单侧。而**抓到**它的
是容差本身——逐维度的窗口随趟数放宽却不随 head_dim 放宽，所以每步一点的
偏差在 headDim=8 藏得住、在 headDim=64 藏不住。

补丁后同一份激励 **2048/2048 全部在容差内**（job 17224318），误差均值
**+0.04 tick**。

### 容差本身也漏了一项

修完之后 `pe=16`（单趟、headDim=64）仍有 4/1024 个维度超窗——而它们是
**±2 tick、三正一负、均值 +0.06**。那不是缺陷的形状（缺陷会是同向的、成片的），
是窗口漏了一项：原来的容差只有「每趟读一次 row_sum、各截断一次」= kPasses
个 tick，这一项对 floor 时代是全部，因为那时误差由同向截断主导。改成四舍五入
之后，每个 MAC 步引入 ±0.5 LSB 的**双侧**噪声，在 headDim 步上做随机游走——
逐点偏差因此随 head_dim 增长，而 kPasses 这一项对它完全是盲的。

容差改成 `kPasses + ceil(sqrt(headDim)/8)`。sqrt 是随机游走的形状；系数取到
**恰好不低于实测最大值**而不是照抄分数上的标准差 `0.5*sqrt(headDim)`（那在
headDim=64 会给 4，而 softmax 的归一化把那个噪声衰减掉了大半，照抄等于把窗口
松一倍、白白丢掉鉴别力）。

五个尺寸全部通过：

| tileQ x tileK / headDim / kept / pe | 趟 | 结果 | 误差均值 |
|---|---|---|---|
| 4x32 / 8 / 8 / 8 | 1 | 32/32 | -0.03 |
| 4x64 / 64 / 16 / 8 | 2 | 256/256 | +0.09 |
| 32x64 / 8 / 16 / 8 | 2 | 256/256 | -0.23 |
| 32x64 / 64 / 16 / 8 | 2 | **2048/2048** | +0.04 |
| 16x64 / 64 / 16 / 16 | 1 | 1024/1024 | +0.06 |

补丁把判据本身也改了：原来的规则是「差 <= N tick **且** 硬件幅值不超过
PyTorch」，后半句成立的前提正是 floor。舍入之后误差是双侧的（实测 495 偏小 :
583 偏大），单侧规则会把**修好的**数据通路判成错的。判据因此改成双侧容差，
方向分布降级为归因线索。

**没有拿别的比例去补这条规则。** 我按 2048 个点拟过一条「低侧必须占多数」，
它在 headDim=8 上立刻把一个每点都在容差内的运行判成失败——而且那个比例本身
是误读来的：旧统计按**幅值**分桶，负数上「差为正」等于幅值变小，被算进了
「偏小」。拿单个数据集拟出来的阈值不是判据。

教训不是「要测大尺寸」，是**逐点容差对「每步一点、同向累积」的缺陷是盲的**，
而这类缺陷在定点数据通路里很常见。`tb_attention_tile.cpp` 因此加报了误差
**均值**：它与尺寸无关，floor 下是 -29.8 tick，补丁后是 +0.04。

改 RTL 的同时必须改 `golden/fixedpoint.py` 的 `fp_mul`——模块级金标准是
数据通路的逐位镜像，只动一边会让金标准把**正确的** RTL 判成错的。改完
10 个模块全部重跑通过（job 17223928）；单独验证过这不是「两边一起改所以
自然一致」：同一批 RePE 向量在 floor 和 round 下有 7/358 个期望值不同，
金标准确实有鉴别力。

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

## BlockScheduler：把 `queue_depth` 从模型变成实测

`predict_unit/block_scheduler.scala` 是 FAST 新增模块，不属于 DynaX 发布。
它补的是 `index_scheduler.scala` 里明说没做的那一半——**跨行负载均衡**。

### 为什么必须做成 RTL 而不是改公式

`fast/agents/codesign.py` 的 `pe_utilisation()` 原本是

    utilisation = 1 / (1 + (imbalance - 1) / (1 + queue_depth))

函数注释自己写着「It is a model, not a measurement」。而 `queue_depth` 是
协同优化器的一个**搜索维度**，并且当时：

* `area_units()` 完全不收它的面积
* `clock_period_ns` 完全不算它的关键路径
* 公式对它单调递增

也就是**只有收益没有成本**。这种维度上优化器必然走到最深的一档，而且没有
任何东西会报错。流水化除法器那次是完全同一个形状的洞。

### 实测结果（Nangate45 + Verilator，真实模型工作量）

驱动是 TinyLlama L10 真实跑出来的逐 tile 行工作量（`DynaX/capture_row_workload.py`），
不是合成分布——动态稀疏的全部问题就在行长差异，那个差异假设不出来。

DynaX-S 形状（32 行 × 4 PE），xm（DynaX 默认稀疏方法）：

| 深度 | 面积 µm² | 关键路径 | 利用率 | 利用率/周期 |
|---|---|---|---|---|
| 0 | 8,899 | 2.273 ns | 0.7079 | 0.311 |
| 2 | 26,392 | 2.528 ns | 0.8323 | **0.329** |
| 4 | 42,826 | 2.760 ns | 0.8644 | 0.313 |
| 8 | 74,421 | 3.140 ns | 0.8669 | 0.276 |
| 16 | 134,870 | （守卫拒绝） | 0.8669 | — |

三件模型看不到的事：

1. **面积**：深度 16 的队列是 135k µm²，DynaX-S 两个阵列合计约 740k——18%。
2. **时序**：关键路径随深度涨到 3.14 ns。执行阵列是 2.23 ns，所以**深度 8 起
   调度器取代阵列决定系统时钟**。41% 的时钟惩罚，换来的利用率是 0.864→0.867。
3. **饱和**：利用率在 1 以下就停了（xm 停在 0.867，公式在深度 16 承诺 0.976）。
   差的那部分是 tile 内结构性损失——一行的保留数不是 PE 数整数倍时最后一趟
   有空槽，加多少队列都填不上。

结果是四种稀疏方法选出的深度**全部改变**：旧启发式选 xm 16 / nm 8 / topk 0 /
sanger 16，实测之后是 nm 0 / 其余全 2。topk 是往**相反方向**动的。

### 模型此前还吃错了一个量

`pe_utilisation()` 吃的 `load_imbalance` 是整行、全序列、跨头拍平的全局极值，
主要反映因果斜坡。阵列感受到的是共享同一个 tile 的那 32 行之间的差异。
两者连排序都不一样：

| 方法 | tile 内 | 全局量（旧输入） |
|---|---|---|
| sanger | 1.95 | 4.92 |
| topk:64 | **1.68** | **1.07** |
| xm | 1.46 | 3.26 |
| nm:16:64 | **1.00** | **1.83** |

全局量把按构造完美均衡的 N:M 排在 topk 之前，实际正好相反。
`sparsity_stats.py` 现在同时记 `mean_tile_load_imbalance`（按阵列高度分别记），
`KernelProfile.tile_imbalance_for()` 取用它。

### testbench 的两条判据

`tb/tb_block_scheduler.cpp` 不验证数据通路（那是 `tb_attention_tile` 的事），
它测**占用率**。但两条结构性判据必须过，否则测量本身是错的：

1. **工作量守恒**：硬件计数器数出的「PE·拍」忙碌数必须精确等于输入里保留列的
   总数。对不上说明有工作被丢了或重复发了。
2. **深度 0 必须等于 1/imbalance**：这是严格锁步的定义，也是原公式在 0 处的
   解析极限。对不上说明队列语义和模型说的不是同一件事，后面所有深度的数
   都不能拿去和模型比。

这两条抓住了实现过程中的三个 bug（详见源文件注释）：行间无耦合导致曲线全平；
1 深 FIFO 默认 `pipe=false` 让吞吐正好减半；保留数为 0 的行不发空趟导致 tile
计数器和其它行错位（topk 上让利用率从 0.609 掉到 0.394）。

第四个 bug 靠综合抓住：`minActiveTile` 用 Chisel 的 `reduce`（左结合）生成的是
numRows 级 16 位比较器**线性链**，32 行 19.0 ns / 64 行 36.6 ns，调度器会变成
52 MHz 的系统瓶颈。改成每行一个「领先屏障几个 tile」的小计数器（位宽
`log2(queueDepth+3)`，没有任何跨行算术）之后降到 2.27 ns，且 20 个
(方法, 深度) 测量点**逐位不变**——证明改写只动时序不动功能。

    sbatch slurm/kernel/dynax_capture_workload.slurm   # 抓真实行工作量
    sbatch slurm/rtl/fast_block_scheduler_sweep.slurm  # 利用率曲线
    sbatch slurm/rtl/fast_synth_block_scheduler.slurm  # 面积/时序曲线

## KeyFeeder：访存路径，以及一个结构性缺口

`execute_unit/key_feeder.scala` 是 FAST 新增模块，不属于 DynaX 发布。

### 缺口：带宽差 2 到 4 倍，而且没有反压

追一遍带宽：

    repe_row.scala:62    reg_cols := io.regs_top      每拍无条件更新
    repe_array.scala:48  rows(0).regs_top := io.regs_top

阵列**每个周期**要 `regWidth` 个新 K 标量——DynaX-S 是 8×16 = **128 位/拍**，
DynaX-L 是 256 位/拍。而 `sram.scala` 的 `SRAM` 是**单地址端口**（一个 `addr`，
`Mux1H` 从 bankCount 个 bank 里选一个输出），每拍只给 `bankWidth` = **64 位**。

差 2 到 4 倍，而且 `RePEArray` 没有反压输入——它没法被告知「这拍没数据」。
开源发布里这条路没有接通，所以这个缺口**不会以任何仿真失败的形式暴露**。

同一个缺口在模型侧的表现是 `codesign.py` 的

    cycles = sparse_macs / (lanes * utilisation)

——**一项和访存有关的都没有**，等于假设带宽无限。于是 `sram_bytes`、
`double_buffer`、bank 数这些维度对周期数的影响全是零。

### 关键结构改动：bank 要能独立寻址

上游把 bank 做成「一个地址、选一个输出」，那只是个分块的单口存储，带宽和
不分块完全一样。要一拍拿到 `regWidth` 个**任意**列，bank 必须各自有地址。
`KeyFeeder` 因此不复用 `SRAM`（那份是上游镜像，要保持可对照），而是自己
例化 bankCount 个独立的 `SyncReadMem`。

### 实测：bank 冲突（Verilator，真实索引流）

驱动是 TinyLlama L10 真实跑出来的**列索引**（`capture_row_workload.py
--emit-indices`），不是随机数：冲突取决于索引的**分布**不是**个数**。

相对理想取数（`regWidth` 个请求散在不同 bank 上、一步发完）的减速倍数，
按**每个请求**归一：

| bank 数 | xm | nm:16:64 | topk:64 | sanger |
|---|---|---|---|---|
| 4 | **3.05×** | 2.17× | 2.69× | 2.25× |
| 8 | **2.14×** | 1.19× | 1.79× | 1.28× |
| 16 | 1.53× | 1.08× | 1.34× | 1.08× |
| 32 | 1.13× | 1.01× | 1.19× | 1.07× |

按请求归一而不是按组：按组平均会把「索引散不散得开」和「组填不填得满」
混在一起——只有 1 个请求的组必然零冲突，而 topk 的组大多是空的。按组算
topk 在 8 bank 下是 1.53，按请求算是 1.79。

### 两个否定结果

**一、XOR 散列 bank 映射是负收益。**

观察到 xm 最差，猜想是索引步长和 `col % bankCount` 混叠，于是加了一档 XOR
折叠映射（`hashBanks`）。实测（banks=8）：

| | 取模 | XOR 散列 |
|---|---|---|
| xm | 2.145 | 2.150（**完全没变**）|
| nm:16:64 | 1.186 | 2.014（**大幅变差**）|
| topk:64 | 1.791 | 1.918 |
| sanger | 1.279 | 1.479 |

散列对 xm 没作用，却把 nm 那种规则步长本来就有的优势毁掉了。查回去，xm 的
冲突根源是 **attention sink**：列 0 每一行都保留，而它和簇里的列 40 同余 8。
那不是步长混叠，散列治不了。面积上散列几乎免费（+192 µm²），所以结论是
干净的：**取模映射对结构化稀疏已接近最优，加 bank 数才是手段**。

**二、SRAM 访问时间不是时钟瓶颈。** fakeram45 宏的访问时间是 0.164 ns（56 B）
到 0.435 ns（10 KB），全部远低于执行阵列的 2.23 ns。这个假设可以排除。

### 一个错误的预测，记下来

做之前我判断「xm 索引聚簇 → 连续 → `col % banks` 下完美散开 → 冲突低」。
实测 xm 是**最差**的。两个原因：簇里有空洞（`33,34,35,36,38,39,40`——37 缺失），
以及每行都有的 sink 列 0 和簇尾同余。**聚簇不等于连续，连续才等于均匀跨越 bank。**

### bank 数的面积代价：几乎免费

综合出来的绝对值没有意义——yosys 又把 `SyncReadMem` 映射成触发器
（2048×16 = 32768 个），27 万 µm² 里绝大部分是那个假存储。但假存储在各个
bank 数下相同，所以**差值**就是选择网络的成本：

    4 banks   270774 µm² (基准)
    8 banks   272295      +1521
    16 banks  275195      +4420
    32 banks  综合被 OOM 杀掉（rc=-9）——没有实测值，按趋势外推 +10200

整个 4→32 区间约 1 万 µm²，而 256 KB 的 SRAM 宏是 105 万。**banking 的真实
代价在宏的长宽比上**（bank 越多越窄，µm²/字节越差），那一项由 `plan_sram()`
承担。

### testbench 的判据

前两条测的是**测量自身**，不是被测对象：

1. **取回的数据必须等于写进去的。** 引擎可以在冲突时慢，但不能取错。
   这条抓到了一个真 bug：`done` 由组合的 `nextPending===0` 产生，和最后一个
   `dataReg` 写入同拍，而 `dataReg` 是寄存器——`out_valid` 比 `out_cols` 早
   一拍，整组数据晚一拍（第 1 组槽 4 要列 45，取到的是第 0 组槽 4 的列 36）。
   **而周期数和解析预测精确一致，只看冲突计数完全看不出这个 bug。**
2. **无冲突下界**：bank 数 ≥ regWidth 且索引互不同余时，每组必须正好 2 拍
   （发地址 + `SyncReadMem` 一拍延迟）。对不上说明引擎自身有多余握手开销，
   那个开销会被误记成冲突代价。

    sbatch slurm/kernel/dynax_capture_workload.slurm   # 抓真实列索引
    sbatch slurm/rtl/fast_key_feeder_sweep.slurm       # bank 冲突曲线
    SYNTH_TARGETS="KeyFeeder_S4 ..." sbatch slurm/rtl/fast_synth_sweep.slurm

## SRAM 面积：hammer 的 nangate45 有 SRAM generator，但它是查表

`sram_area_units()` 此前是 `sram_bytes * 0.1`，没有任何支撑。直接综合拿不到
真值：yosys 没有存储器宏编译器。

hammer 的 nangate45 tech plugin **自带** `sram_compiler`，但它不是编译器而是
查表：映射到 OpenROAD-flow-scripts 的 `fakeram45_*` 宏。关键在于那些宏和我们
已经在用的 Nangate45 标准单元库**同一个仓库、同一个节点**，所以面积可以直接
和阵列的面积相加。`flow/platforms/nangate45/` 下有 26 个宏，覆盖 32×32 到
2048×39，`.lib` 里有 `area`、访问时间和 internal power。

**实测出来那个 `0.1` 小了 40 倍**：

| | 旧模型 | 宏拼装实测 | 倍数 |
|---|---|---|---|
| 64 KB 面积 | 6,554 µm² | 262,497 µm² | 40.1× |
| 256 KB 面积 | 26,214 µm² | **1,049,989 µm²** | 40.1× |
| 256 KB 漏电 | 0.26 mW | **51.1 mW** | 197× |

256 KB 的 SRAM 比两个阵列合计（74 万 µm²）还大，此前在模型里是个舍入误差。

面积模型不是一个 µm²/字节系数，而是真实的**宏拼装规划**（`plan_sram()`）——
因为长宽比本身就是成本：同样 4 KB，`1024x32` 是 4.01 µm²/B 而 `128x256` 是
8.30，差一倍。窄而深的宏效率高，宽而浅的差。

证据等级是 `L1-analytical-vendor-model`：`fakeram` 是解析生成的宏，不是硅上
表征的。它是 OpenROAD 自己发布 benchmark 时用的东西，节点对得上，但低于
yosys 实测。取数与解析见 `scripts/fetch_nangate45_srams.py`。

### 顺带修掉的：功耗此前是任意单位

`estimate()` 的功耗项是 `lanes * utilisation * data_width**2 * 1e-4`，32×4
算出 **2.85**，而同一个阵列实测 **398.655 mW**。两者从来没对过账。加 SRAM
漏电时这变成硬伤：把 51（mW）加到 2.85（任意单位）上会让 SRAM 凭空压倒一切。

标定过程中我自己错了一次：先按综合的**翻转率** a=0.078 定系数，再代入 PE
**利用率** 0.83——两者差一个数量级（`a` 是「每个网络在多少比例时钟沿上翻转」，
利用率是「这条 lane 有多少比例周期有活干」），算出 3827 mW。改成以实测点作
满负荷锚点后，32×4 满负荷 398.1 mW vs 实测 398.7。

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
