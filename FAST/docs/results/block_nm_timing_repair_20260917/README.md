# Block N:M 后续时序修复

**已完成并通过独立验收。** 先读[最终报告](RESULTS.md)，实际代码变化见[top_change.diff](top_change.diff)。

原始RQ1的五轮失败结果保留在[原报告](../rq1_completion_20260917/RQ1_SUMMARY.md)。本目录记录单独的工程修复，不能回写为原实验自主成功。

- `PROTOCOL.json`：约束、原始源码/结果哈希、冻结框架。
- `diagnosis.txt`：交给FAST组装UArch的外部诊断。
- `paths.json`：计算作业和结果路径。
- `repair_control_tests.xml`：保存检查点和Critic输入的故障注入测试。
- `RESULTS.md`、`RESULTS.json`：完成验证后生成的结果。
- `top_change.diff`：实际顶层代码差异。
- `validation/`：最终数值测试、RTL/网表验证及完整归档。

初始方案：将串行15级最大值比较改成4层平衡树，保留70拍调度。实际周期数和PPA以结果为准。
