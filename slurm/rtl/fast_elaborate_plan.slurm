#!/usr/bin/env bash
#SBATCH --job-name=fast-elab-plan
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=00:50:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 「计划 -> 设计」这一步：Elaborate 按 planner 给的参数造完整的 AttentionTile。
#
# 在这一步之前，planner 能说出「32x4、queue 2、8 banks」，但没有任何东西
# 把那句话变成可综合的顶层——系统能规划出 DynaX 尺寸，却造不出它。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/plan_${SLURM_JOB_ID}"
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

export TMPDIR=/tmp/plan-$$; mkdir -p "$TMPDIR" "$OUT"

cd "$REPO/FAST/hardware"
# 三个尺寸：现有 testbench 的（单趟，已验证）、论文 DynaX-S（多趟，没验过）、
# 以及一个 8 位的点——planner 会从 data_widths 里挑 8，而整个验证栈在 16 位。
for SPEC in \
  "PLAN:bits=16,tileQ=4,tileK=32,headDim=8,keptPerRow=8,peCountPerRow=8,dividerStages=8" \
  "PLAN:bits=16,tileQ=32,tileK=64,headDim=64,keptPerRow=16,peCountPerRow=4,dividerStages=8" \
  "PLAN:bits=8,tileQ=32,tileK=64,headDim=64,keptPerRow=16,peCountPerRow=8,dividerStages=8" \
; do
  echo; echo "--- $SPEC ---"
  KEPT=$(echo "$SPEC" | grep -oP 'keptPerRow=\K[0-9]+')
  PE=$(echo "$SPEC" | grep -oP 'peCountPerRow=\K[0-9]+')
  echo "    需要 $(( (KEPT + PE - 1) / PE )) 趟"
  scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "$SPEC" "$OUT/$RANDOM" 2>&1 \
      | grep -vE "^(Download|Downloaded|Compiling|Compiled|Checking|Checked)" | tail -8
done
