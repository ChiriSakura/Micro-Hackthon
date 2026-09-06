#!/usr/bin/env bash
#SBATCH --job-name=fast-dynax-loop
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# One FAST candidate end to end with the real DynaX kernel backend:
# measurement -> quality gate -> schedule -> template gate -> evaluation ->
# critique -> manifest with artifact checksums.

set -euo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
RUN_DIR="$ROOT/runs/fast_dynax_loop_${SLURM_JOB_ID}"

export HF_HOME="$ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TMPDIR="$ROOT/tmp"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

CONFIG=${FAST_LOOP_CONFIG:-configs/experiments/tinyllama_xm.json}

source "$ROOT/env/fast-py312/bin/activate"
mkdir -p "$RUN_DIR" "$TMPDIR"
cd /home/gz2522/Micro-Hackthon/FAST

python -m fast.cli \
    --kernel dynax \
    --config "$CONFIG" \
    --dynax-python "$ROOT/env/dynax-py312/bin/python" \
    --dynax-device cpu \
    --template-id smoke-template \
    --run-dir "$RUN_DIR"

echo "manifest: $(find "$RUN_DIR/candidates" -name manifest.json)"
