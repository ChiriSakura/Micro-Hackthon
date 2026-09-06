#!/usr/bin/env bash
#SBATCH --job-name=dynax-eval-matrix-cpu
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
ENV_DIR="$ROOT/env/dynax-py312"
RUN_DIR="$ROOT/runs/eval_matrix_cpu_${SLURM_JOB_ID}"

export HF_HOME="$ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TMPDIR="$ROOT/tmp"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

MODEL=${FAST_EVAL_MODEL:-TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T}
DATASET=${FAST_EVAL_DATASET:-wiki}
SEQ_LEN=${FAST_EVAL_SEQ_LEN:-512}
SAMPLES=${FAST_EVAL_SAMPLES:-8}
METHODS=${FAST_EVAL_METHODS:-dense,xm,xm:8:4:64,xm:32:16:64,nm:16:64,nm:8:64,topk:128,sanger,salo}
DTYPE=${FAST_EVAL_DTYPE:-float32}

source "$ENV_DIR/bin/activate"
mkdir -p "$RUN_DIR" "$TMPDIR"
cd /home/gz2522/Micro-Hackthon/DynaX

lscpu | grep -E "^Model name|^CPU(s)"

python run_eval_matrix.py \
    --model "$MODEL" \
    --dataset "$DATASET" \
    --seq-len "$SEQ_LEN" \
    --max-samples "$SAMPLES" \
    --methods "$METHODS" \
    --dtype "$DTYPE" \
    --device cpu \
    --run-dir "$RUN_DIR"

echo "results: $RUN_DIR/results.json"
