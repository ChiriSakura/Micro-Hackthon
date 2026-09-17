#!/usr/bin/env bash
#SBATCH --job-name=dynax-capture-workload
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 抓真实的逐 tile 行工作量分布，给 block scheduler 的利用率测量当输入。
#
# 这是 queue_depth 这个搜索维度目前唯一缺的东西：pe_utilisation() 的
# 注释自己写着「这是模型不是测量」。要判定这个模型对不对，得先有真实的
# 负载不均衡度——而不均衡度是模型和数据决定的，合成不出来。
#
# tile 按 RePEArray 的实际形状切（rows x block），因为不均衡度只在共享
# 同一个阵列的那几行之间才是硬件真正面对的东西。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/workload_${SLURM_JOB_ID}"
export TMPDIR=/tmp/workload-$$; mkdir -p "$TMPDIR" "$OUT"
export HF_HOME="$ROOT/cache/hf" TRANSFORMERS_OFFLINE=0
cd "$REPO/DynaX"

# 两种阵列高度都抓：DynaX-S 是 32 行，DynaX-L 是 64 行，
# 不均衡度随 tile 高度变化，这正是 queue_depth 要对付的量。
for rows in 32 64; do
  "$ROOT/env/dynax-py312/bin/python" -u capture_row_workload.py \
      --layer "${WORKLOAD_LAYER:-10}" \
      --seq-len "${WORKLOAD_SEQ:-512}" \
      --methods "${WORKLOAD_METHODS:-xm,xm:32:16:64,nm:16:64,topk:64,sanger}" \
      --rows "$rows" --block 64 --emit-indices "${WORKLOAD_INDICES:-256}" \
      --out "$OUT/workload_rows${rows}.json"
  echo "rows=$rows 退出码 $?"
done
ls -l "$OUT"
