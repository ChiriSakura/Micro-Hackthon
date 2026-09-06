#!/usr/bin/env bash
#SBATCH --job-name=dynax-pytest-cpu
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ENV_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/dynax-py312
RUN_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/pytest_cpu_${SLURM_JOB_ID}
export HF_HOME=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/huggingface
export TMPDIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/tmp

source "$ENV_DIR/bin/activate"
mkdir -p "$RUN_DIR" "$TMPDIR"
cd /home/gz2522/Micro-Hackthon/DynaX

pytest -m "not gpu" --junitxml="$RUN_DIR/junit.xml" -q
