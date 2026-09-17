#!/usr/bin/env bash
#SBATCH --job-name=fast-rediscover
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -euo pipefail
FAST_ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
FAST_REPO=${FAST_REPO:-/home/gz2522/Micro-Hackthon}
export HF_HOME="$FAST_ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-16}"
export PATH="/share/apps/openjdk/21.0.3/bin:$FAST_ROOT/tools:$PATH"
export COURSIER_CACHE="$FAST_ROOT/cache/coursier"
export SCALA_CLI_HOME="$FAST_ROOT/cache/scala-cli"
export TMPDIR="$FAST_ROOT/tmp/rediscovery-$SLURM_JOB_ID"
mkdir -p "$TMPDIR"
cd "$FAST_REPO/FAST"
"$FAST_ROOT/env/fast-py312/bin/python" scripts/run_dynax_rediscovery.py \
  --config "${FAST_CONFIG:-configs/experiments/dynax_rediscovery.json}" \
  --out "$FAST_ROOT/runs/rediscovery_${FAST_METHOD:-llm}_${SLURM_JOB_ID}" \
  --method "${FAST_METHOD:-llm}" --seed "${FAST_SEED:-0}" \
  --critic "${FAST_CRITIC:-auto}" \
  --dynax-python "$FAST_ROOT/env/dynax-py312/bin/python" \
  --gcp-project "${GCP_PROJECT:-project-842e7b1d-4f04-40b2-9b0}" \
  --validate-frontier --containers "$FAST_ROOT/containers" \
  --liberty "$FAST_ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
