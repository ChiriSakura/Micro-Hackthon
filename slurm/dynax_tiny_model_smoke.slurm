#!/usr/bin/env bash
#SBATCH --job-name=dynax-e2e
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=h200_tandon,l40s_public,h100_tandon,a100_tandon
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ENV_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/dynax-py312
RUN_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/e2e_${SLURM_JOB_ID}
export HF_HOME=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/huggingface
export TMPDIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/tmp

source "$ENV_DIR/bin/activate"
mkdir -p "$RUN_DIR" "$HF_HOME" "$TMPDIR"
cd "$RUN_DIR"

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
python /home/gz2522/Micro-Hackthon/DynaX/smoke_tiny_models.py \
    --output "$RUN_DIR/result.json"
