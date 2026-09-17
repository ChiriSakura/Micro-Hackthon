#!/usr/bin/env bash
#SBATCH --job-name=fast-tiletop-verify
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=00:50:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 控制收进硬件之后，**结果必须逐字节不变**。
#
# 判据是和 golden 参照逐维一致，用同一份 tile.json、同一个容差口径。
# 附带产出硬件自己数的拍数——那个数原来散在 testbench 的 C++ 循环里。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/tiletopv_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/tiletopv-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"

cd "$REPO/FAST/hardware"
echo "--- elaborate ---"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
    --main-class Elaborate -- AttentionTileTop "$OUT/rtl" 2>&1 \
  | grep -E "ELABORATE|error" | tail -4

SV=$(find "$OUT/rtl" -name "AttentionTileTop.v" | head -1)
[ -z "$SV" ] && { echo "FAIL: 没找到 Verilog"; exit 1; }

echo "--- verilate + build ---"
# verilator 在容器里，不在 PATH 上——和 fast_attention_tile.slurm 同一个用法。
cp "$REPO/FAST/hardware/tb/tb_attention_tile_top.cpp" \
   "$REPO/FAST/hardware/tb/golden.h" "$OUT/"
cd "$OUT"
apptainer exec "$ROOT/containers/verilator.sif" verilator \
    --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" -Wno-fatal \
    --top-module AttentionTileTop -CFLAGS "-I$OUT" \
    "$SV" tb_attention_tile_top.cpp -o tb_top 2>&1 | tail -14
[ -x "$OUT/obj_dir/tb_top" ] || { echo "构建失败"; exit 1; }

TILE=$(ls -t $ROOT/runs/tile_*/tile.json 2>/dev/null | while read f; do
  python3 -c "
import json,sys
p=json.load(open('$f'))['params']
sys.exit(0 if (p['tile_q'],p['tile_k'],p['head_dim'],p['kept'])==(4,32,8,8) else 1)" && echo "$f" && break
done)
[ -z "$TILE" ] && { echo "FAIL: 没有 4x32x8 kept=8 的抓取"; exit 1; }
echo "--- 用 $TILE 验证 ---"
apptainer exec "$ROOT/containers/verilator.sif" "$OUT/obj_dir/tb_top" "$TILE"
echo "退出码 $?"
