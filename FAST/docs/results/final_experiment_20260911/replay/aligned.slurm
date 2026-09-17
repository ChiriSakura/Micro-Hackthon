#!/usr/bin/env bash
#SBATCH --job-name=fast-aligned-profile
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=00:40:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -euo pipefail
FAST_ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
FAST_REPO=/scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/rediscovery_20260910_v3

export HF_HOME="$FAST_ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export PATH="/share/apps/openjdk/21.0.3/bin:$FAST_ROOT/tools:$PATH"
export COURSIER_CACHE="$FAST_ROOT/cache/coursier"
export SCALA_CLI_HOME="$FAST_ROOT/cache/scala-cli"
export TMPDIR="$FAST_ROOT/tmp/refine-$SLURM_JOB_ID"
mkdir -p "$TMPDIR"
cd "$FAST_REPO/DynaX"
"$FAST_ROOT/env/dynax-py312/bin/python" run_eval_matrix.py --model TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T --dataset wiki --seq-len 512 --max-samples 16 --methods dense,xm:16:8:32:0.75:0.05 --dtype float32 --device cpu --seed 20260903 --run-dir "$FAST_ROOT/runs/final_experiment_20260910/aligned_$SLURM_JOB_ID"
