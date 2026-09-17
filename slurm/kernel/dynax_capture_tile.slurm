#!/usr/bin/env bash
#SBATCH --job-name=dynax-capture-tile
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 从真实模型抓一个 attention tile，给硬件验证当输入。
#
# 判据不是「RTL 自洽」——那只能证明 RTL 等于它自己——而是同一组真实
# Q/K/V 下，硬件的输出和 PyTorch 的稀疏注意力对不对得上。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/tile_${SLURM_JOB_ID}"
export TMPDIR=/tmp/tile-$$; mkdir -p "$TMPDIR" "$OUT"
export HF_HOME="$ROOT/cache/hf" TRANSFORMERS_OFFLINE=0
cd "$REPO/DynaX"
"$ROOT/env/dynax-py312/bin/python" -u capture_attention_tile.py \
    --layer "${TILE_LAYER:-10}" --head "${TILE_HEAD:-0}" \
    --tile-q ${TILE_Q:-4} --tile-k ${TILE_K:-32} --head-dim ${TILE_HEADDIM:-8} --kept ${TILE_KEPT:-8} \
    --out "$OUT/tile.json"
echo "退出码 $?"
