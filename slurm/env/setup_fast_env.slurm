#!/usr/bin/env bash
#SBATCH --job-name=setup-fast-env
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ENV_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312
RUN_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fast_chia_setup_${SLURM_JOB_ID}
export PIP_CACHE_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/pip
export TMPDIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/tmp
mkdir -p "${ENV_DIR%/*}" "$RUN_DIR" "$PIP_CACHE_DIR" "$TMPDIR"

if [ ! -x "$ENV_DIR/bin/python" ]; then
    python3.12 -m venv "$ENV_DIR"
elif [ "$("$ENV_DIR/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" != "3.12" ]; then
    # This exact task-owned environment may have been created by an older
    # compute-node default Python; rebuild it to satisfy CHIA's >=3.10 bound.
    python3.12 -m venv --clear "$ENV_DIR"
fi

source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e /home/gz2522/Micro-Hackthon/chia -e '/home/gz2522/Micro-Hackthon/FAST[test]'

cd /home/gz2522/Micro-Hackthon/FAST
python -m pytest --junitxml="$RUN_DIR/junit.xml"
python -m fast.runtime.chia_smoke --output "$RUN_DIR/report.json"
