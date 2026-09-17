# Critic 消融预注册协议

实验开始前固定以下配置；机器可读网格见 `protocol.json`。

- 主实验：32-row 困难起点，随机 proposer；off、rule、LLM、LLM shadow、LLM 无独立反馈、单字段 local random，共 6 组 × 3 次。
- 确认实验：16-row 起点，LLM proposer；off、LLM，共 2 组 × 3 次。该实验同时改变起点与 proposer，仅用于条件外确认，不能单独归因到其中一个因素。
- 每次最多 5 个 loop、5 次解析模型候选评估，通过后继续，不给 Critic 额外候选预算。规则/LLM 干预最多一个字段，占一个已有候选槽。记录非法提案、无提案、L1 拒绝、独立验证失败及 API 错误。
- 固定算法 `xm:16:8:32:0.75:0.05`，沿用已有 32-window 质量确认；不重新搜索算法。约束 epsilon=5%，350 MHz，PE≤256，SRAM≤524288B，L1 area≤4e6µm²，16-bit 数据。保持原参数域。
- 两个 parent 均重新运行完整 scheduler workload 功能仿真、Yosys、OpenSTA，必须确实不满足 350 MHz，方可进入修复实验。
- seed=0/1/2 只控制随机 proposer/随机干预。LLM 为 Gemini 2.5 Pro、temperature=0.2，不支持固定 seed；规则组重复主要检查复现性，LLM 组是随机重复。
- shadow 不执行 Critic 动作、不把其文本传给 proposer。无独立反馈组只对 Critic 及其规则回退屏蔽 independent observations 和派生可行性标记；验收门仍照常使用独立结果。
- 复用同一任务的冻结 trace，校验 SHA256、模型、seed、layer/head、完整任务覆盖、rows/M；不复用硬件结果。相同硬件也重新跑工具，记录重复验证。
- 记录原始 API prompt/reply/error/wall time（后端未提供 token usage 时为 null），每次 Critic context/decision/action/fallback/outcome，每个工具命令、日志、设计和验证 SHA。
- 首要指标：5 轮内约束恢复率、首次通过轮次、最优已验证 latency、最后候选与保留 incumbent。辅助指标：子模块面积、假定统一活动率的功耗/能量估计、调用次数、wall time。
- 能量仅是 scheduler uniform-activity proxy；不是工作负载驱动功耗、整机能量或完整 attention PPA。探索性 proxy hypervolume 固定参考点 (10µs,1µJ)，只纳入独立通过点；没有点时为 0。
- 逐组/逐运行披露，不合并两种 proposer 计算总效果。n=3 仅探索性证据，不声称统计显著或已替代通用人工优化。等候选预算不等于等 wall time/API 成本。
