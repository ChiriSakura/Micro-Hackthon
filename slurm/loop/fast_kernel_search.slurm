#!/usr/bin/env bash
#SBATCH --job-name=fast-kernel-search
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# One Kernel Agent search on real DynaX measurements.
#   FAST_PROPOSER=sweep|llm  FAST_BUDGET=8  sbatch --export=ALL slurm/fast_kernel_search.slurm
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
export HF_HOME="$ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
export TMPDIR="$ROOT/tmp"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export GCP_PROJECT=${GCP_PROJECT:-project-842e7b1d-4f04-40b2-9b0}
export GCP_LOCATION=${GCP_LOCATION:-us-central1}

# 算法是**输入**，不是搜索维度：Agent 探索的是这个算法的配置。
# DynaX 自己的是 xm（动态 X:M）。要比较算法就每个跑一次这条流水线——
# 那是一次对照实验，不是一次搜索。
ALGORITHM=${FAST_ALGORITHM:-xm}
PROPOSER=${FAST_PROPOSER:-sweep}
BUDGET=${FAST_BUDGET:-8}
BATCH=${FAST_BATCH:-4}
RUN_DIR="$ROOT/runs/kernel_search_${ALGORITHM}_${PROPOSER}_${SLURM_JOB_ID}"

# The FAST env drives the search; DynaX measurements run in DynaX's own env.
source "$ROOT/env/fast-py312/bin/activate"
cd "$REPO/FAST"
echo "node=$(hostname) 算法=$ALGORITHM proposer=$PROPOSER budget=$BUDGET batch=$BATCH"

python -m fast.cli_kernel \
    --run-dir "$RUN_DIR" \
    --algorithm "$ALGORITHM" \
    --proposer "$PROPOSER" \
    --budget "$BUDGET" \
    --batch "$BATCH" \
    --dynax-python "$ROOT/env/dynax-py312/bin/python" \
    --dynax-device cpu \
    --seq-len 512 --max-samples 8 --epsilon 0.05
