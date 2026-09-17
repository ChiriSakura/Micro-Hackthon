#!/usr/bin/env bash
#SBATCH --job-name=fast-mut-symptom
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 症状检查：LLM 改出来的 RTL 真的把关键路径降下来了吗。
#
# **通过门 != 有效。** XOR 散列通过了全部的门却是负收益。所以症状检查必须
# 独立于门存在，而且判据是 Critic 派发变异时给出的那个可检验目标——
# 这里是「32 行实例的关键路径 <= 2.230 ns」。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/mutsym_${SLURM_JOB_ID}"
MODULE="$REPO/FAST/hardware/chisel/src/main/scala/predict_unit/block_scheduler.scala"
BACKUP="$OUT/block_scheduler.original.scala"
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

export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export TMPDIR=/tmp/mutsym-$$; mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache

cp "$MODULE" "$BACKUP"
restore() { cp "$BACKUP" "$MODULE"; echo "已还原 block_scheduler.scala"; }
trap restore EXIT

cp "${MUTATED:-/tmp/mutated_block_scheduler.scala}" "$MODULE"
echo "换上 LLM 改写的版本"

cd "$REPO/FAST/hardware"
echo; echo "=== 1. elaborate ==="
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- \
    "LIST:BlockSched_S0,BlockSched_S2,BlockSched_S8,BlockSched_L8" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)" | tail -12

echo; echo "=== 2. 综合 + 时序（症状检查）==="
cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u scripts/synthesize_modules.py \
    --rtl "$OUT/rtl" --container "$ROOT/containers/yosys.sif" \
    --liberty "$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib" \
    --sta-container "$ROOT/containers/opensta.sif" --period-ns 2.0 \
    --only BlockSched_S0 BlockSched_S2 BlockSched_S8 BlockSched_L8 \
    --out "$OUT/synthesis.json" --log-dir "$OUT/logs" 2>&1 | grep -E "BlockSched|时序|综合退出"

echo; echo "=== 目标：32 行实例关键路径 <= 2.230 ns（阵列的路径）==="
echo "   对照：改坏前的线性 reduce 版本是 19.0 ns（32 行）/ 36.6 ns（64 行）"
