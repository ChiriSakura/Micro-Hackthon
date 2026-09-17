#!/usr/bin/env bash
#SBATCH --job-name=fast-sys-verify
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 完整系统 + bank 数扫描。
#
# bring-up 判据：阈值设成全部走高档时，分档退化成固定 top-n，语义与 golden
# 抓取的参照一致。先确认这条路径跑通，再谈分档本身对不对。
#
# bank 扫描出的是「冲突 -> 反压 -> 停顿」的实测曲线——代价模型里那个标定
# 出来的 gather_slowdown 系数第一次有实测对照。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/sysv_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/sysv-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"

TILE=""
for f in $(ls -t $ROOT/runs/tile_*/tile.json 2>/dev/null); do
  "$ROOT/env/dynax-py312/bin/python" -c "
import json,sys
p=json.load(open('$f'))['params']
sys.exit(0 if (p['tile_q'],p['tile_k'],p['head_dim'],p['kept'])==(4,32,8,8) else 1)" && { TILE="$f"; break; }
done
[ -z "$TILE" ] && { echo "FAIL: 没有 4x32x8 kept=8 的抓取"; exit 1; }
echo "抓取 $TILE"

cd "$REPO/FAST/hardware"
for BANKS in 4 8 16 32; do
  T="AttentionTileSystem_B$BANKS"
  echo; echo "================ $BANKS banks ================"
  scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
      --main-class Elaborate -- "$T" "$OUT/$T" 2>&1 | grep -E "ELABORATE|error" | tail -2
  V=$(find "$OUT/$T" -name "AttentionTileSystem.v" | head -1)
  [ -z "$V" ] && { echo "  没有产出 Verilog"; continue; }

  W="$OUT/build_$BANKS"; mkdir -p "$W"
  cp "$REPO/FAST/hardware/tb/tb_attention_tile_system.cpp" \
     "$REPO/FAST/hardware/tb/golden.h" "$W/"
  ( cd "$W" && apptainer exec "$ROOT/containers/verilator.sif" verilator \
      --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" -Wno-fatal \
      --top-module AttentionTileSystem -CFLAGS "-I$W" \
      "$V" tb_attention_tile_system.cpp -o tb_sys 2>&1 | tail -6 )
  [ -x "$W/obj_dir/tb_sys" ] || { echo "  构建失败"; continue; }
  apptainer exec "$ROOT/containers/verilator.sif" "$W/obj_dir/tb_sys" "$TILE"
done
