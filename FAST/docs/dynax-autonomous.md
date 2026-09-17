# DynaX 运行与归档复现

[最终两轮结果](results/dynax_autonomous_20260913/RESULTS.md)。默认验收范围为 8-key X:M 查询行，完整模型与更大规模另行扩展。

## 1. 环境

在 FAST 根目录运行。Python ≥3.10，安装项目与测试依赖；真实生成还需要 Vertex SDK/ADC。工具根目录应包含：

```text
<tool-root>/
  containers/{verilator,yosys,opensta,openroad-flow}.sif
  tools/scala-cli
  env/hammer-py312/bin/python
  pdk/nangate45/NangateOpenCellLibrary_typical.lib
  pdk/hammer45/                 Nangate45 Liberty、LEF、RC 与 Hammer 配置
```

PATH 中需要 Apptainer；Chisel 需要 Java（本次 OpenJDK 21）。当前 `physical.py` 使用上述 Hammer Python 位置。`--tool-root` 应指向你已配置的工具目录；容器、PDK、外部 Python 环境不包含在实验归档中，版本和关键 PDK 哈希在原始物理结果里。

本机已验证的工具根为 `/scratch/gz2522/gz2522/tmp/micro-hackthon`，Python 为其 `env/fast-py312/bin/python`。首次配置可参考 `scripts/setup_hammer_nangate45.py` 及既有 Slurm 环境脚本。

## 2. 启动新的自主实验

```bash
export FAST_TOOL_ROOT=/path/to/micro-hackthon-tools
export FAST_RUN_ROOT=/path/to/new-experiments
export FAST_VERTEX_PROJECT=your-project-id
python -m fast.fullstack.cli \
  --task configs/fullstack/dynax_autonomous.json \
  --catalog libraries/catalog.json \
  --run-dir "$FAST_RUN_ROOT/dynax-001" \
  --tool-root "$FAST_TOOL_ROOT" \
  --project "$FAST_VERTEX_PROJECT" \
  --model gemini-2.5-pro --location us-central1 \
  --timeout 600 --tool-timeout 3600 \
  --max-output-tokens 48000 --critic on
```

运行目录必须不存在。任务默认两轮、3 次 Compiler 设计机会、每模块/组装各 5 次尝试，模块串行。LLM 与硬件工具超时分开。原始运行启动脚本保存在报告目录 `launch/`，其中机器路径仅供追溯，不直接当作跨机器命令。

重新运行 LLM 可能产生不同设计，不能承诺重现相同探索轨迹。要重现已保存设计，使用下面的无 LLM 复验。

## 3. 校验并提取独立归档

```bash
export FAST_EVIDENCE=/path/to/new-evidence-directory
python scripts/archive_generated_run.py \
  --verify docs/results/dynax_autonomous_20260913/artifacts.tar.gz \
  --record /tmp/dynax-archive-verification.json
mkdir -p "$FAST_EVIDENCE"
tar -xzf docs/results/dynax_autonomous_20260913/artifacts.tar.gz -C "$FAST_EVIDENCE"
```

压缩包内有 `run/`、`source/`、`validation/` 和逐文件清单。原始 JSON/日志保留执行时的路径；不要对整个归档做字符串替换，这会改变证据哈希。

## 4. 重建第二轮并提取 PPA

使用**当前工程**的复验脚本，算法与 IP 使用归档内冻结的 catalog。当前入口已修复原生 IP 快照依赖旧绝对路径的问题；归档的执行源码保留原样。

```bash
python scripts/revalidate_generated_design.py \
  --run "$FAST_EVIDENCE/run" --round 2 \
  --catalog "$FAST_EVIDENCE/source/libraries/catalog.json" \
  --output "$FAST_RUN_ROOT/dynax-round2-recheck" \
  --tool-root "$FAST_TOOL_ROOT" \
  --ppa-backend hammer_openroad --timeout 3600
```

此入口校验生成源码及原生 IP 哈希后重新 elaboration、E2E 和 PPA。若只做较快的源码重建检查，可选择 `yosys_opensta`；此时 PPA 属于另一个后端，不能替换报告中的 Hammer 结果。`passed` 表示功能和测量流程完成，物理约束是否满足仍须检查 `evaluation.feasible`。

整理时已经执行一次从解压新目录出发的真实复验：作业 `17721095`，无 LLM，100/100 E2E、17 cycles 通过；使用 `yosys_opensta` 做快速重建检查，没有重跑 Hammer。见 [整理验证记录](cleanup-2026-09-13.md)。

## 5. 额外种子与原始 routed 网表

```bash
python scripts/verify_generated_holdout.py \
  --run "$FAST_EVIDENCE/run" --round 2 \
  --catalog "$FAST_EVIDENCE/source/libraries/catalog.json" \
  --output "$FAST_RUN_ROOT/dynax-round2-holdout" \
  --tool-root "$FAST_TOOL_ROOT" --ppa-backend yosys_opensta --timeout 600
python scripts/verify_routed_design.py \
  --run "$FAST_EVIDENCE/run" --round 2 \
  --catalog "$FAST_EVIDENCE/source/libraries/catalog.json" \
  --output "$FAST_RUN_ROOT/dynax-round2-gate" \
  --tool-root "$FAST_TOOL_ROOT"
```

前者检验重新生成的 RTL；后者按原测量的哈希核对归档内 routed.v，再做零延时功能仿真。工具/库版本变化可能改变 PPA，跨机器不能承诺完全相同的物理数字。

## 6. 保存今后的实验

```bash
python scripts/archive_generated_run.py \
  --input "run=$FAST_RUN_ROOT/dynax-001" \
  --input source=/path/to/frozen-source \
  --input validation=/path/to/verification-results \
  --output /path/to/dynax-001.tar.gz \
  --record /path/to/dynax-001.verify.json
python scripts/report_generated_run.py \
  --run "$FAST_RUN_ROOT/dynax-001" --output /path/to/report
```

归档工具保留所有非缓存文件并拒绝覆盖已有压缩包，完整读取归档后核对每个哈希；不会自动删除输入。报告工具按实际算法与后端导出逐轮指标，缺失测量保持为空。删除缓存或退休实验应另行记录清理清单。
