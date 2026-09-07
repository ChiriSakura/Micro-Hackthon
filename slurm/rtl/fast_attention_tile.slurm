#!/usr/bin/env bash
#SBATCH --job-name=fast-attn-tile
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=4 --mem=8G --time=00:25:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 用真实模型的 Q/K/V 驱动完整的 attention tile，对着 PyTorch 验证。
#
# 这是「模型的一部分注意力能不能在这个加速器上跑」的答案。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
TILE=${TILE_JSON:-$ROOT/runs/tile_17086373/tile.json}
OUT="$ROOT/runs/attn_${SLURM_JOB_ID}"
export APPTAINER_TMPDIR=/tmp PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export TMPDIR=/tmp/at-$$; mkdir -p "$TMPDIR" "$OUT"
cd "$REPO/FAST/hardware"; HW=$PWD

echo "=== 1. elaborate AttentionTile ==="
scala-cli run chisel --server=false --main-class Elaborate -- AttentionTile "$OUT/rtl" 2>&1 \
  | grep -E "^ELABORATE|FAIL"
V="$OUT/rtl/AttentionTile/AttentionTile.v"
[ -f "$V" ] || { echo "elaborate 失败"; ls -R "$OUT/rtl" | head; exit 1; }
echo "Verilog $(wc -l < "$V") 行"

echo; echo "=== 2. verilate ==="
cp "$HW/tb/tb_attention_tile.cpp" "$HW/tb/golden.h" "$OUT/"
cd "$OUT"
apptainer exec "$ROOT/containers/verilator.sif" verilator \
    --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" -Wno-fatal \
    --top-module AttentionTile -CFLAGS "-I$OUT" \
    "$V" tb_attention_tile.cpp -o tb_attn 2>&1 | tail -12
[ -x "$OUT/obj_dir/tb_attn" ] || { echo "构建失败"; tail -20 "$OUT/build.log" 2>/dev/null; exit 1; }

echo; echo "=== 3. 用真实 Q/K/V 跑 ==="
apptainer exec "$ROOT/containers/verilator.sif" "$OUT/obj_dir/tb_attn" "$TILE"
echo "退出码 $?"
