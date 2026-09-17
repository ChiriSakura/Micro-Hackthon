#!/usr/bin/env bash
#SBATCH --job-name=fast-tier-elab
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=00:40:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/tier_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/tier-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"
cd "$REPO/FAST/hardware"
# 三个都要过：固定 top-n（不能被破坏）、分档、以及带 FSM 的顶层。
for T in AttentionTile AttentionTile_Tiered AttentionTileTop AttentionTileSystem; do
  echo; echo "=== $T ==="
  scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
      --main-class Elaborate -- "$T" "$OUT/$T" 2>&1 \
    | grep -E "ELABORATE|error|Exception" | tail -5
done
