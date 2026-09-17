# 只读参考库

`catalog.json` 注册可信算法与硬件参考。运行时先复制并计算 SHA-256，Agent 只能读取材料并在新运行目录生成设计。

- `algorithms/`：用户维护的算法契约、合法配置、画像测量和独立 E2E golden。
- `hardware/`：小型通用模板；注册表也可引用 `../hardware/chisel/` 中的完整原生 IP。
- 硬件条目的 `support_sources` 包含依赖，`test_references` 携带 golden/testbench 示例。
- Compiler 为模块分配 `reference_ids`；兼容的原生 Chisel 可通过 `linked_reference_ids` 直接链接，只生成适配层。

扩展库由维护者新增算法或模板并修改注册表，然后检查契约、依赖和 golden。Agent 执行期间不能修改这些文件。未知算法没有默认回退；库扩展说明见 [生成约定](../docs/fullstack-generation.md)。

`third_party/` 保存固定 commit 的上游材料与来源清单。`language` 明确区分 Chisel / SpinalHDL / Verilog；`native_linkable=false` 的参考只能读取和适配，不能直接链接。详情见 [上游参考说明](third_party/README.md)。

`rq1_catalog.json` 保留原四算法实验输入；`rq1_extended_catalog.json` 为 N:M / Sanger 新 cohort 增加 6 个条目，避免改变原实验。

`rq1_dynax_recovery_catalog.json` 仅用于工程恢复实验，额外注册 `generated_verified/dynax_rq1_round1/` 中两个原样保存的历史生成组件。它们有模块/E2E验证来源，旧完整设计没有通过最终精度；新设计必须重新选参、组装、验证及提取PPA。
