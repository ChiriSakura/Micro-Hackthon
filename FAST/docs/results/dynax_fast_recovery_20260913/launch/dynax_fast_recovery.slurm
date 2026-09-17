#!/bin/bash
#SBATCH --job-name=dynax-fast-recover
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -eu
cd /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/dynax_autonomous_v8r1
export PATH=/share/apps/openjdk/21.0.3/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export CCACHE_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/user-ccache-20260913
export TMPDIR=/tmp/fast-dynax-auto-${SLURM_JOB_ID}
mkdir -p "$TMPDIR"
export APPTAINER_TMPDIR="$TMPDIR"
export PYTHONPATH="$PWD"
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/recover_dynax_fast.py
