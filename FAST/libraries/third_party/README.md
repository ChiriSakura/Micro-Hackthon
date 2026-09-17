# 固定版本的上游参考代码

manifest.json 与各目录 PROVENANCE.json 记录来源、commit、许可事实和逐文件 SHA-256。源码逐字导入并设为只读，修改应在 Agent 新生成模块中完成。Agent 运行还会创建独立只读快照并检查哈希。

当前引入 Sanger（旧版 Chisel）、FLOW/FlexCiM（Verilog）、SpAtten（SpinalHDL）和通用 bitonic_sorter（Verilog）。所有新增条目均为 reference-only，不是已适配本项目数值契约的即插即用核心。不得以 TopKDummy 模拟正确硬件，或用近似 exp 替代精确 LUT。

具体来源、实测兼容性和失败结果见 [调查报告](../../docs/results/rq1_extended_20260916/REFERENCE_DISCOVERY.md)。
