#!/usr/bin/env bash
#SBATCH --job-name=fast-tile-top
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=00:50:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 集成层第一步：**把控制收进硬件**。
#
# 评审 P0-4：AttentionTile 的控制和 K/V gather 都在外部，testbench 逐 query
# 复位、只驱动第 0 行、跨趟分子分母在 C++ 里相加——它自己的注释就写着
# 「这正是硬件缺的那层控制」。后果是完整执行时间、多行吞吐、存储停顿三样
# 都证明不了。
#
# 这一步先让状态机自己走完 QK -> exp -> AV -> norm，跨趟累加进寄存器，
# 完成拍数由硬件数出来。golden 测试仍是唯一的正确性锚点。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/tiletop_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="${TMPDIR:-$ROOT/tmp}/scala-build-${SLURM_JOB_ID:-$$}"
mkdir -p "$SCALA_BUILD_WS" "$OUT"
export TMPDIR="$ROOT/tmp/tiletop-$$"; mkdir -p "$TMPDIR"

cd "$REPO/FAST/hardware"
for TARGET in AttentionTileTop AttentionTileTop_MultiPass; do
  echo; echo "=== $TARGET ==="
  scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
      --main-class Elaborate -- "$TARGET" "$OUT/$TARGET" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled|Checking|Checked)" | tail -12
done
echo; echo "产物："; find "$OUT" -name "*.sv" -o -name "*.v" | head
