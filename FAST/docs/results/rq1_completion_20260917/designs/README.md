# 最终已验收设计代码

这些是已验证运行的逐字节副本；`manifest.json`记录原路径与SHA256。`generated/`含Agent生成的Chisel/Verilog，`rtl/`含用于验证的展开RTL，`linked_library/`保留实际链接的只读源码。没有重新修改或生成硬件。

| 目录 | 来源 | 软件配置 | 顶层 |
|---|---|---|---|
| [dynax_R5](dynax_R5/) | original_trajectory | `{"n1": 7, "n2": 4, "t0_quarters": 2, "t1_quarters": 0}` | `Rq1DynaXm` |
| [topk_R5](topk_R5/) | original_trajectory | `{"k": 15}` | `rq1_global_topk` |
| [sanger_R1](sanger_R1/) | original_trajectory | `{"threshold_256": 3}` | `SangerThresholdTop` |
| [block_nm_A1](block_nm_A1/) | assisted_repair | `{"n": 7}` | `Rq1BlockNmTop` |

完整仿真testbench、原始工具日志、网表/寄生数据及Agent调用仍在对应验证目录的`artifacts.tar.gz`，不要仅凭源码副本声称重新验证。修复A1独立于原RQ1五轮。
