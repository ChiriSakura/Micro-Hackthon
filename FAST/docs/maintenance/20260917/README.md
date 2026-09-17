# RQ1与N:M修复后的整理记录

完成日期：2026-09-17。

- 完整复读验证7份保留的实验归档。
- 清理2714个文件，合计4967965981 bytes（约4.97 GB）。
- 范围仅为明确列出的已完成RQ1/修复运行：Verilator obj_dir、Scala/BSP/Python缓存，以及已逐文件校验归档的旧报告生成器副本。
- 不删除生成设计、库、原始日志、失败候选、物理结果、独立验收或其他项目。

详细路径、字节数和归档信息见[cleanup_manifest.json](cleanup_manifest.json)，执行逻辑见[cleanup_verified.py](cleanup_verified.py)。旧报告/生成器保存在[历史归档](../../history/rq1_consolidation_20260917/README.md)，当前源码和数据入口见[RQ1总报告](../../results/rq1_completion_20260917/RQ1_SUMMARY.md)。

当前代码已冻结为[current_code.tar.gz](current_code.tar.gz)，包含`fast/`、`scripts/`、`tests/`、`configs/`共192个文件，逐文件校验见[current_code_verification.json](current_code_verification.json)。实际实验运行版本仍以各实验的源码快照为准。

最终[验收记录](../../results/rq1_completion_20260917/final_acceptance_audit.json)覆盖原始候选未改动、CSV一致性、四个设计源码、七份实验归档和14项报告测试。可在FAST根目录运行`PYTHONDONTWRITEBYTECODE=1 python3 docs/maintenance/20260917/audit_consolidation.py`重新核对。该脚本仅读取证据并更新验收记录，不运行实验或清理。

本次Git同步保留代码、生成设计、报告、指标和校验记录。大型实验二进制归档继续保存在本机，不上传到Git；逐项路径、大小和SHA-256见[local_archive_inventory.json](local_archive_inventory.json)。克隆仓库即可阅读设计和结果，但完整原始工具产物需另行取得这些归档。小型源码快照仍纳入Git。
