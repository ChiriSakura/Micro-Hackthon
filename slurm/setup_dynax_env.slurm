#!/usr/bin/env bash
#SBATCH --job-name=dynax-setup
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ENV_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/dynax-py312
export PIP_CACHE_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/pip
export TMPDIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/tmp

mkdir -p "$PIP_CACHE_DIR" "$TMPDIR" "${ENV_DIR%/*}"
if [[ ! -x "$ENV_DIR/bin/python" ]]; then
    python3.12 -m venv "$ENV_DIR" || python3 -m venv "$ENV_DIR"
fi

source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
python -m pip install \
    numpy==1.26.4 \
    transformers==4.48.3 \
    datasets==3.2.0 \
    peft==0.14.0 \
    accelerate==1.2.1 \
    pytest==8.3.4 \
    tqdm==4.67.1
python - <<'PY'
import numpy
import torch
import transformers
print("numpy", numpy.__version__)
print("torch", torch.__version__, "cuda_build", torch.version.cuda)
print("transformers", transformers.__version__)
PY
