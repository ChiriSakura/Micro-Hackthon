#!/usr/bin/env bash
#SBATCH --job-name=dynax-eval-cpu
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

set -euo pipefail

ENV_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/dynax-py312
RUN_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/tiny_eval_cpu_${SLURM_JOB_ID}
export HF_HOME=/scratch/gz2522/gz2522/tmp/micro-hackthon/cache/huggingface
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export TMPDIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/tmp
export DYNAX_CONFIG_PATH="$RUN_DIR/dynax_config.json"

source "$ENV_DIR/bin/activate"
mkdir -p "$RUN_DIR" "$HF_HOME" "$TMPDIR"
cp /home/gz2522/Micro-Hackthon/DynaX/configs/xm_sparse_config.json "$DYNAX_CONFIG_PATH"
cd "$RUN_DIR"

python /home/gz2522/Micro-Hackthon/DynaX/eval_llama3.py \
    --model_name_or_path hf-internal-testing/tiny-random-LlamaForCausalLM \
    --dataset wiki \
    --max_seq_len 64 \
    --max_samples 2
