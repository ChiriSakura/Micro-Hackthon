#!/usr/bin/env bash
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=00:45:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/critic_ablation_20260911/slurm/%x_%A_%a.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/critic_ablation_20260911/slurm/%x_%A_%a.err
#SBATCH --job-name=critic-ablate
#SBATCH --array=0-23%6
set -euo pipefail
FAST_ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
export HF_HOME="$FAST_ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PATH="/share/apps/openjdk/21.0.3/bin:$FAST_ROOT/tools:$PATH"
export COURSIER_CACHE="$FAST_ROOT/cache/coursier"
export SCALA_CLI_HOME="$FAST_ROOT/cache/scala-cli"
export TMPDIR="$FAST_ROOT/tmp/critic-ablation-${SLURM_JOB_ID}-${SLURM_ARRAY_TASK_ID:-prep}"
mkdir -p "$TMPDIR"
cd "$FAST_ROOT/snapshots/critic_ablation_20260911/FAST"
"$FAST_ROOT/env/fast-py312/bin/python" scripts/run_critic_ablation.py --study "$FAST_ROOT/runs/critic_ablation_20260911" --index "$SLURM_ARRAY_TASK_ID" --gcp-project project-842e7b1d-4f04-40b2-9b0 --dynax-python "$FAST_ROOT/env/dynax-py312/bin/python" --containers "$FAST_ROOT/containers" --liberty "$FAST_ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
