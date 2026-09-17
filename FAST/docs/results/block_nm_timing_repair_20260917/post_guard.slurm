#!/bin/bash
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -eu
export PATH=/share/apps/openjdk/21.0.3/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export CCACHE_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/user-ccache-20260913
export TMPDIR=/tmp/fast-nm-repair-guard-${SLURM_JOB_ID}
mkdir -p "$TMPDIR"
export APPTAINER_TMPDIR="$TMPDIR"
if /scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python /home/gz2522/Micro-Hackthon/FAST/docs/results/block_nm_timing_repair_20260917/post_completion_guard.py /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_validation_v1_20260917/rq1_block_nm /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_v1_20260917/rq1_block_nm; then
  post_output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_validation_v1_20260917/rq1_block_nm
else
  post_output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_validation_guard_v1_20260917/rq1_block_nm
  /scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/scripts/finalize_rq1_run.py --run /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_v1_20260917/rq1_block_nm --catalog /scratch/gz2522/gz2522/tmp/micro-hackthon/snapshots/block_nm_timing_repair_v1_20260917/libraries/rq1_extended_catalog.json --output /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/block_nm_timing_repair_validation_guard_v1_20260917/rq1_block_nm --tool-root /scratch/gz2522/gz2522/tmp/micro-hackthon --holdout-seed 2026091801 --holdout-count 8192
fi
rsync -a --exclude=obj_dir --exclude=.scala-build --exclude=.bsp --exclude=__pycache__ --exclude='*.tmp' "$post_output/" /home/gz2522/Micro-Hackthon/FAST/docs/results/block_nm_timing_repair_20260917/validation/
/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python - "$post_output" <<'PYMETA'
from pathlib import Path
import json,sys,os
p=Path('/home/gz2522/Micro-Hackthon/FAST/docs/results/block_nm_timing_repair_20260917/paths.json')
d=json.loads(p.read_text());d["output"]=sys.argv[1];d["post_guard_completed"]=os.environ["SLURM_JOB_ID"];p.write_text(json.dumps(d,indent=2)+"\n")
PYMETA
