#!/usr/bin/env bash
#SBATCH --job-name=fast-synth-sweep
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 只综合 BlockScheduler 的深度扫描——queue_depth 的**成本侧**。
#
# 全量综合要跑十几分钟，而这条曲线在调 RTL 期间要重测好几次：改了 tile
# 屏障，寄存器数就变了，面积跟着变。单独拎出来，改一次测一次。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
SIF="$ROOT/containers/yosys.sif"
STA="$ROOT/containers/opensta.sif"
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
OUT="$ROOT/runs/synth_sweep_${SLURM_JOB_ID}"
export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
# 每个作业用自己的 .scala-build。
#
# 共享的后果撞到过三次：所有作业都从同一个仓库路径跑 `scala-cli run chisel`，
# 于是并发提交时它们编译进**同一个** FAST/hardware/chisel/.scala-build。
# 表现是随机一两个作业报 `FAIL: predict_unit/PrePEArray_1_2` 或干脆不产出
# ELABORATE 行——看起来像 RTL 坏了，串行重跑就全过。
export SCALA_BUILD_WS="${TMPDIR:-/tmp}/scala-build-${SLURM_JOB_ID:-$$}"
mkdir -p "$SCALA_BUILD_WS"

export TMPDIR=/tmp/fast-synth-sweep-$$
mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache

# 默认综合工作队列的深度扫描；SYNTH_TARGETS 可以换成任意一组 elaborate 目标
# （取数引擎的 bank 扫描也走这里）。
TARGETS="${SYNTH_TARGETS:-BlockSched_S0 BlockSched_S2 BlockSched_S4 BlockSched_S8 \
BlockSched_S16 BlockSched_L0 BlockSched_L8 BlockSched_L16}"

echo "=== 1. elaborate ==="
cd "$REPO/FAST/hardware"
LIST=$(echo "$TARGETS" | tr ' ' ',')
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "LIST:$LIST" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)" | tail -12

echo; echo "=== 2. 综合 ==="
cd "$REPO/FAST"
# shellcheck disable=SC2086
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u scripts/synthesize_modules.py \
    --rtl "$OUT/rtl" --container "$SIF" --liberty "$LIB" \
    --sta-container "$STA" --period-ns 2.0 \
    --only $TARGETS \
    --out "$OUT/synthesis.json" --log-dir "$OUT/logs"
echo "综合退出码: $?"
echo "结果 $OUT/synthesis.json"
