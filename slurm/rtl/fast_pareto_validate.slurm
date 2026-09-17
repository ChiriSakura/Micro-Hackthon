#!/usr/bin/env bash
#SBATCH --job-name=fast-pareto-validate
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:25:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -euo pipefail
FAST_ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
FAST_REPO=/home/gz2522/Micro-Hackthon
: "${WORKLOAD_JSON:?set an explicit frozen WORKLOAD_JSON}"
export PATH="/share/apps/openjdk/21.0.3/bin:$FAST_ROOT/tools:$PATH"
export COURSIER_CACHE="$FAST_ROOT/cache/coursier"
export SCALA_CLI_HOME="$FAST_ROOT/cache/scala-cli"
export TMPDIR="$FAST_ROOT/tmp/pareto-${SLURM_JOB_ID}"
mkdir -p "$TMPDIR"
cd "$FAST_REPO/FAST"
"$FAST_ROOT/env/fast-py312/bin/python" scripts/validate_pareto_scheduler.py \
  --workload "$WORKLOAD_JSON" --method "${TRACE_METHOD:-xm}" \
  --tile-offset "${TILE_OFFSET:-256}" --tile-count "${TILE_COUNT:-128}" \
  --depths 0 2 4 --frequency-mhz 350 \
  --out "$FAST_ROOT/runs/pareto_validation_${SLURM_JOB_ID}" \
  --containers "$FAST_ROOT/containers" \
  --liberty "$FAST_ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
