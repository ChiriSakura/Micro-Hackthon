#!/usr/bin/env bash
#SBATCH --job-name=dynax-plot-masks
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
export HF_HOME="$ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TMPDIR="$ROOT/tmp"
export MPLCONFIGDIR="$ROOT/tmp/mpl"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

MODEL=${FAST_PLOT_MODEL:-TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T}
SEQ_LEN=${FAST_PLOT_SEQ_LEN:-512}
LAYER=${FAST_PLOT_LAYER:-10}
HEAD=${FAST_PLOT_HEAD:-0}
METHODS=${FAST_PLOT_METHODS:-xm,xm:32:16:64,xm:8:4:64,nm:16:64,topk:64,sanger,salo}
OUT=${FAST_PLOT_OUT:-/home/gz2522/Micro-Hackthon/FAST/figures}

source "$ROOT/env/dynax-py312/bin/activate"
mkdir -p "$TMPDIR" "$MPLCONFIGDIR" "$OUT"
cd /home/gz2522/Micro-Hackthon/DynaX

python plot_attention_masks.py \
    --model "$MODEL" --seq-len "$SEQ_LEN" --layer "$LAYER" --head "$HEAD" \
    --methods "$METHODS" --out "$OUT" --device cpu
