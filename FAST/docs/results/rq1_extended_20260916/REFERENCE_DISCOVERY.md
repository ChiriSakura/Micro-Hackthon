# Block N:M / Sanger 硬件参考调查与实测

## 已导入的真实源代码

| 来源 | 固定 commit | 新条目 | 适用与限制 |
|---|---|---|---|
| [Sanger 官方](https://github.com/hatsu3/Sanger) | 5d99ba390ed9a81e138271a7776058b45938859a | mask、pack、sparse PE | Chisel 3.4.1/Scala 2.12；原版 unsigned 与近似 exp，不等于本次 signed 精确 LUT 契约 |
| [FLOW / FlexCiM](https://github.com/FLOW-open-project/FLOW) | af604014799d9a0cdf3cb43ff332edeaac4682c1 | N:M distribution | MIT；Verilog，两级选择网络，静态权重稀疏的数据分发，不是动态 attention 排名器 |
| [SpAtten 官方](https://github.com/mit-han-lab/spatten) | a0f1388630590668e09456c4680211c513592e3f | TopK / QuickSelect 及依赖 | MIT；SpinalHDL，不能直接当 Chisel；TopKDummy 不是数值实现，禁止替代真实计算 |
| [通用 bitonic_sorter](https://github.com/mcjtag/bitonic_sorter) | d48b8ab0af4589e5ef10ff82507f67882769cd24 | signed bitonic 网络 | MIT；Verilog，可参考有符号排序；没有 attention mask/index 协议，也不是 DFSS 官方硬件 |

全部导入文件未修改；逐文件清单在 libraries/third_party/manifest.json。Sanger 固定 commit 未发现 LICENSE 文件，不擅自标为 MIT。上游测试一并保留为参考，但不把保留测试文件视为已执行或适配通过。

[DFSS 官方仓库](https://github.com/apuaaChen/DFSS)提供 Ampere sparse Tensor Core/CUDA 实现，适合算法与 GPU 数据布局参考，不是可综合的 ASIC/FPGA RTL，因此未冒充硬件模板导入。[STA 的 N:M 论文](https://arxiv.org/abs/2208.06118)可作架构参考，本次检索未核实其官方 RTL 发布地址。Sanger 论文见[原文](https://liqianglu-zju.github.io/files/conference/2021/MICRO_2021_Sanger.pdf)，SpAtten 见[原文](https://arxiv.org/abs/2012.09852)。

## 导入后实际执行的检查

SLURM 17874127，脚本 scripts/probe_extended_references.py；summary 和完整日志见本目录 reference_probe_summary.json / reference_probes.tar.gz。

| 检查 | 结果 | 解释 |
|---|---|---|
| bitonic，signed 9-bit，8 路，组合 | 100/100 通过 | 含随机与边界数据，独立软件排序 oracle |
| bitonic，同样数据，PIPE_REG=1 | 100/100 通过 | 验证 6 拍输出 |
| FlexCiM distribution 独立模块 | 100/100 通过 | 两级 mux 对独立软件 oracle；未执行参数不一致的上游 Cocotb 测试 |
| FlexCiM 完整 hw 包 Verilator lint | 失败，9 个语法错误 | 完整系统不能直接作为已验证实现 |
| Sanger 原版在 FAST Chisel 3.6.1 / Scala 2.13.12 elaboration | 失败，10 个编译错误 | 旧 Range.Double、asUInt()、andR() 等 API；不代表原指定版本必然失败 |
| 既有原生 TopK，m=8,n=7 | 通过，完成于 14 拍 | rank valid 分别第 8…14 拍；旧 Agent 声称 15 拍不正确 |

这些是参考组件探针，**不是** FAST 新生成的 Block N:M / Sanger E2E 成功，也没有为新系统提供任何 PPA 数值。

## 上轮失败不只源于模板数量

N:M 的旧诊断把 16 个值为 2 的 9-bit packed score 期望值误判为错误。实际整数为 `87282760072526900749650560754005328790530`，等于 `sum(2 << (9*i) for i in range(16))`，oracle 正确。旧诊断还错报 TopK 的完成周期。现在向 Agent 显示 packed 值、hex 和 lane，附加实测 TopK 协议，保持 oracle 不变。

Sanger 旧顶层同时更新 q/k 输入寄存器并拉高其子模块 valid，存在子模块读旧寄存器、V 路径错位的风险；首例 mask 正确但结果 0（期望 -8）。这是静态检查提出的归因假设，还不是波形证明。旧迭代仅把 done 从 40→41→42 拍后移，并未证明修复数据对齐。新提示统一要求用寄存器时钟语义分析，避免仅移动 done。

因此本轮同时修复通用框架并增加规划预算，单独编号；若结果改善，不能把收益全部归因于新模板数量。实际是否读取、分配与使用参考，由运行证据决定。
