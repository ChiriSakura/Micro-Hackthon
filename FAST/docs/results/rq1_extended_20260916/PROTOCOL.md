# RQ1 扩展参考库重跑（2026-09-16 UTC）

目标：让 FAST 在新增只读硬件参考下，从零自主生成 Block N:M 与 Sanger 概率阈值行级系统，并尝试完成各 5 个外层设计轮次，包括每轮真实 E2E、Hammer PPA 和 Critic 分析。

这是 **扩展库＋通用框架修正＋增加规划预算** 的独立 cohort，不能作为仅增加模板或 Critic ON/OFF 的因果消融。旧版失败、调用和结果保留在 [v1](../rq1_20260915/RESULTS.md)。两次运行预算不同，不能直接比较成功率来归因。

## 不变条件

沿用 [v1 数学与评估协议](../rq1_20260915/PROTOCOL.md)：16 keys、Q/K dim=2、V dim=1；同样的 signed Q/K/V、精确 exp LUT、低索引平局规则、截断除法、软件搜索空间和 workload。算法文件哈希与 v1 一致，在 source_freeze.json 中核对。

- 校准相对输出 RMSE ≤5%，2048 随机＋4 边界，seed=20260915；共同 float dense-softmax 参考。不是模型任务准确率。
- 留出 4096 随机，seed=20260916；只在搜索结束后评估，不反馈给 Agent。
- 300 MHz，单元面积 ≤200000 µm²，Nangate45 TT；setup/hold ≥0、route DRC=0。
- 每轮独立可信 RTL E2E 100 条，随后通过完整 Hammer/Yosys/OpenROAD 布线、OpenRCX、OpenSTA 提取 PPA。功耗基于统一 activity=0.1，不是芯片实测或波形驱动功耗。
- 延迟与 queries/J 能效构成 Pareto；96 dense-equivalent ops/query 仅作统一换算。
- 搜索结束后检查留出精度，对搜索 Pareto 点额外进行 5 个种子 RTL 验证与布线后零延时门级功能验证；通过后才称独立合格。
- gemini-2.5-pro、temperature=0.2、max-output-tokens=48000、LLM timeout=600s、工具 timeout=3600s、seed=17；模块逐个实现，独立 UArch 组装。无预制计划、旧 RTL 或人工按失败修改生成模块。

## 新增条件

- 两个任务使用同一个扩展 catalog 和同一段新增提示词；6 个新模板条目来自 4 个固定 commit 的仓库，文件逐字保留，带来源、兼容性与 SHA-256。详情见 [参考库调查](REFERENCE_DISCOVERY.md)。
- min_loops=max_loops=5。这里指含初始设计的 5 个外层设计轮次；R5 的 Critic 建议记录但不追加 R6。Critic 提前 stop 会被要求给出下一步建议；生成或工具错误仍可能让运行中止，不把失败修复次数冒充 5 个完整设计轮次。
- Compiler 规划预算 3→5 次；参考读取预算 2→3 次。模块/组装预算仍各 5 次。主作业上限 4h→8h，独立后验证 4h。
- 通用框架增加语言/native_linkable 校验，防止 SpinalHDL、旧 API 或参考用途源码被误当可直接链接的 Chisel IP。
- 行为诊断展示最多 1024 bit 的实际值与 packed lane 解码，修正旧版 >128 bit 输出只显示位宽、诱发错误归因的问题；不修改可信 oracle。
- Compiler/组装提示明确同一时钟沿的寄存器与 valid 对齐语义；加入原 TopK 实测协议参考（8:7 完成时间是 14 拍，非上轮 Agent 猜测的 15 拍）。

参考库探针、单元测试不计入生成系统的成功率。新参考均标记 reference-only；Agent 可读取、参考、翻译并新建模块，不能修改库源文件或将不兼容源码强行链接。compatible 原生旧 IP 仍允许链接。库读取/模块分配/请求链接分别在 DESIGNS.md 中审计；被读取不等于被有效复用。

## 产物与结论边界

jobs.json 记录独立作业、后验证作业和运行位置；source.tar.gz 保存冻结输入与哈希；每算法目录保存自动报告、失败日志、原始调用、源码、物理结果与完整归档。RESULTS.md / metrics.csv / DESIGNS.md 随实际证据更新，无 PPA 的失败点保持为空。

这一小规模合成实验只能证明指定契约下的跨层适配。Sanger 契约是概率阈值注意力，不声称复现原论文全部近似数值、规模和架构；Block N:M 是动态索引选择，不等同于静态权重 N:M CiM。尚需真实模型 QKV、扩展规模、重复运行与等预算对照才能支持更广泛的 RQ1 结论。
