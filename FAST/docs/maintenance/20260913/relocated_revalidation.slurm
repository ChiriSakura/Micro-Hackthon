#!/bin/bash
#SBATCH --job-name=fast-archive-check
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/archives/maintenance_20260913/relocation_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/archives/maintenance_20260913/relocation_%j.err
set -eu
cd /home/gz2522/Micro-Hackthon/FAST
export PATH=/share/apps/openjdk/21.0.3/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR=/tmp/fast-archive-${SLURM_JOB_ID}
mkdir -p "$TMPDIR"
export APPTAINER_TMPDIR="$TMPDIR"
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python scripts/revalidate_generated_design.py --run /scratch/gz2522/gz2522/tmp/micro-hackthon/archives/dynax_relocated_validation/run --round 2 --catalog /scratch/gz2522/gz2522/tmp/micro-hackthon/archives/dynax_relocated_validation/source/libraries/catalog.json --output /scratch/gz2522/gz2522/tmp/micro-hackthon/archives/maintenance_20260913/relocated_recheck --tool-root /scratch/gz2522/gz2522/tmp/micro-hackthon --ppa-backend yosys_opensta --timeout 600
