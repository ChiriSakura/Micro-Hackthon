#!/usr/bin/env bash
#SBATCH --job-name=fast-chia-smoke
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:10:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ENV_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312
RUN_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fast_chia_smoke_${SLURM_JOB_ID}
mkdir -p "$RUN_DIR"
source "$ENV_DIR/bin/activate"
cd /home/gz2522/Micro-Hackthon/FAST

python -m pytest --junitxml="$RUN_DIR/junit.xml"
python -m fast.runtime.chia_smoke --output "$RUN_DIR/report.json"
