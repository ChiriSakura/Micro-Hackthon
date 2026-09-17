#!/bin/bash
#SBATCH --job-name=dynax-recovery-holdout
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:45:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -eu
cd /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/dynax_autonomous_v8r1
export PATH=/share/apps/openjdk/21.0.3/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/tmp/dynax-recovery-holdout-${SLURM_JOB_ID}
mkdir -p "$TMPDIR"
export APPTAINER_TMPDIR="$TMPDIR"
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python scripts/verify_generated_holdout.py --run /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/dynax_fast_recovery_17709206 --round "$1" --ppa-backend yosys_opensta --catalog /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/dynax_autonomous_v8r1/libraries/catalog.json --output /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/dynax_recovery_holdout_${SLURM_JOB_ID} --tool-root /scratch/gz2522/gz2522/tmp/micro-hackthon
