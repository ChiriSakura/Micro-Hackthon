#!/bin/bash
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -eu
export PATH=/share/apps/openjdk/21.0.3/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export CCACHE_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/user-ccache-20260913
export TMPDIR=/tmp/fast-nm-repair-${SLURM_JOB_ID}
mkdir -p "$TMPDIR"
export APPTAINER_TMPDIR="$TMPDIR"
cd /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917
set +e
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/scripts/repair_generated_assembly.py --run /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_sta_v4_20260917/rq1_block_nm --build round_05/build_01 --previous-top /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_sta_v4_20260917/rq1_block_nm/round_05/build_01/Rq1BlockNmTop/Rq1BlockNmTop.scala --diagnosis /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/diagnosis.txt --catalog /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/libraries/rq1_extended_catalog.json --output /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_v1_20260917/rq1_block_nm --tool-root /scratch/gz2522/gz2522/tmp/micro-hackthon --project project-842e7b1d-4f04-40b2-9b0 --tool-timeout 7200 --critic on
repair_status=$?
set -e
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/scripts/finalize_rq1_run.py --run /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_v1_20260917/rq1_block_nm --catalog /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/libraries/rq1_extended_catalog.json --output /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_validation_v1_20260917/rq1_block_nm --tool-root /scratch/gz2522/gz2522/tmp/micro-hackthon --holdout-seed 2026091801 --holdout-count 8192
rsync -a --exclude=obj_dir --exclude=.scala-build --exclude=.bsp --exclude=__pycache__ '--exclude=*.tmp' /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_validation_v1_20260917/rq1_block_nm/ /home/gz2522/Micro-Hackthon/FAST/docs/results/block_nm_timing_repair_20260917/validation/
exit "$repair_status"
