#!/usr/bin/env bash
#SBATCH --job-name=fast-critic-verify
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -euo pipefail
FAST_ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
export HF_HOME="$FAST_ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PATH="/share/apps/openjdk/21.0.3/bin:$FAST_ROOT/tools:$PATH"
export COURSIER_CACHE="$FAST_ROOT/cache/coursier"
export SCALA_CLI_HOME="$FAST_ROOT/cache/scala-cli"
export TMPDIR="$FAST_ROOT/tmp/critic-$SLURM_JOB_ID"
mkdir -p "$TMPDIR"
cd "$FAST_ROOT/snapshots/critic_integration_20260911_v2/FAST"
"$FAST_ROOT/env/fast-py312/bin/python" scripts/refine_rediscovery.py \
 --source "$FAST_ROOT/runs/rediscovery_llm_17355007" \
 --out "$FAST_ROOT/runs/critic_verify_$SLURM_JOB_ID" \
 --method random --critic llm --budget 2 \
 --dynax-python "$FAST_ROOT/env/dynax-py312/bin/python" \
 --gcp-project "${GCP_PROJECT:-project-842e7b1d-4f04-40b2-9b0}" \
 --containers "$FAST_ROOT/containers" \
 --liberty "$FAST_ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
