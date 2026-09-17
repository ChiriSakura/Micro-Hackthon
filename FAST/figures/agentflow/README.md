# FAST Agent flow — paper figure

此图对应当前 `fast/fullstack/` 的 Critic-enabled 主流程，采用 Hammer 物理后端。图中不包含旧 FiveAgentFlow、参数搜索/修正实验或尚未实现的工作流。

## 文件

- `fast_agentflow.pdf`：矢量 PDF，嵌入 TrueType 字体，推荐论文双栏通栏使用。
- `fast_agentflow.svg`：矢量 SVG，保留文字对象，可在 Illustrator、Inkscape 或支持 SVG 的排版工具中编辑。
- `fast_agentflow.png`：300 dpi 预览，可插入 PPT。
- `draw_agentflow.py`：可编辑绘图源码，仅依赖 Matplotlib；运行 `python figures/agentflow/draw_agentflow.py` 重新生成三种格式。
- `figure.tex`：LaTeX 插图片段与英文图注。
- `provenance.json`：核对时的框架源码及绘图文件哈希。

建议以约 180 mm 宽度放入论文，避免缩成单栏。复杂图注、实现限制和具体实验数字放正文；图内保持架构信息。

## 图的含义

实线表示设计与验证证据流；灰色点线表示只读参考输入；橙色虚线表示局部修复/重规划；紫色长虚线表示 Critic 的跨层优化反馈。

1. Kernel 从可信执行得到的画像中选择合法、满足质量约束的算法配置。
2. Compiler 检索模板和 golden 示例，定义模块接口、行为测试与参考绑定，并准备独立模块任务。
3. UArch 可生成 Chisel 或 Verilog，兼容原生 Chisel IP 可只读链接，不要求重写全部参考子模块。图中的多个卡片表示独立模块会话；当前默认串行，调度器支持依赖感知并发。
4. 每个模块先通过 elaboration/Verilator 检查，全部所需模块接受后才进行独立顶层组装。
5. 系统 golden 来自只读算法插件。Compiler 声明的局部测试与最终独立 E2E 属于不同证据层。
6. 普通局部失败反馈给当前 UArch；重复失败、模块契约冲突及组装失败可进入 CompilerDiagnosis，给出 repair 或 replan。它不是 PPA 优化 Critic。
7. E2E 成功后进行 Hammer/Yosys/OpenROAD 物理评估。只有 PPA 完整才进入 Critic；PPA 完整不意味着物理约束可行，Critic 也可分析完整但不可行的候选。
8. Critic 的选择是重入 Kernel、Compiler、UArch 或停止。UArch 重入先保留当前接口/拓扑；这不等于仅重建单个目标模块，当前实现仍会遍历计划，必要时升级 Compiler。
9. 停止或预算结束时输出历史中满足约束的非支配设计。纵向目标为 energy efficiency（queries/J），横向目标为 latency；不表示全局最优。

框架会保存全部尝试、源码/参考哈希及工具记录。为控制图复杂度，未逐一展开 API 格式重试、预算耗尽/工具错误的终止分支、Critic-off 对照分支和共同起点导入分支；这些均以代码与原始记录为准。

## 代码对应

| 图中模块 | 当前实现 |
|---|---|
| Kernel、Compiler、Critic 与外层重入 | `fast/fullstack/flow.py`：`kernel`、`compile_plan`、`build`、`run` |
| 各 LLM 角色与诊断角色 | `fast/fullstack/agents.py` |
| 模块任务、依赖屏障、独立组装和局部修复 | `fast/fullstack/dispatch.py`：`DesignDispatcher` |
| 只读参考、原生 IP 和哈希 | `fast/fullstack/library.py`：`Library` |
| 模块行为测试 | `fast/fullstack/behavior.py` |
| 编译与独立 E2E | `fast/fullstack/tools.py` |
| 物理 PPA | `fast/fullstack/physical.py`、`hammer_driver.py` |
| 可行点筛选与 Pareto | `fast/fullstack/contracts.py`：`pareto` |

## Suggested caption

**Overview of FAST.** The Kernel Agent selects an algorithm configuration from measured profiles. The Compiler Agent plans module interfaces and tests and binds read-only references to isolated UArch tasks. Accepted modules are assembled and validated against an independent algorithm golden before physical evaluation. Local failures trigger bounded repair or compiler diagnosis. Complete PPA evidence enables the Critic to select Kernel, Compiler, or UArch re-entry. On termination, feasible nondominated designs are retained in the latency–energy-efficiency space. Module dispatch is dependency-aware and serial by default.
