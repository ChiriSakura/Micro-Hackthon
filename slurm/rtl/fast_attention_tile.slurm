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
# 默认取**最近一次**抓取，而不是写死一个作业号。
#
# 写死的后果这一轮撞到过：脚本默认指向 tile_17086373，而上一次通过的运行用的
# 是 tile_17090354——两份 capture 的 Q/K/V 和 PyTorch 参照都不同，于是「新代码
# 对旧数据」被误读成「新代码把已验证的路径改坏了」，我为此查错了两轮。

OUT="$ROOT/runs/attn_${SLURM_JOB_ID}"
export APPTAINER_TMPDIR=/tmp PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
# 每个作业用自己的 .scala-build。
#
# 共享的后果撞到过三次：所有作业都从同一个仓库路径跑 `scala-cli run chisel`，
# 于是并发提交时它们编译进**同一个** FAST/hardware/chisel/.scala-build。
# 表现是随机一两个作业报 `FAIL: predict_unit/PrePEArray_1_2` 或干脆不产出
# ELABORATE 行——看起来像 RTL 坏了，串行重跑就全过。
export SCALA_BUILD_WS="${TMPDIR:-/tmp}/scala-build-${SLURM_JOB_ID:-$$}"
mkdir -p "$SCALA_BUILD_WS"

export TMPDIR=/tmp/at-$$; mkdir -p "$TMPDIR" "$OUT"
cd "$REPO/FAST/hardware"; HW=$PWD

# 尺寸由环境变量给，默认是已验证过的单趟配置。
# TILE_KEPT > TILE_PE 就走**多趟**路径——DynaX-S 是 kept=16 / pe=4，论文尺寸
# 必然走它，而它此前从没验证过。
TQ=${TILE_Q:-4}; TK=${TILE_K:-32}; HD=${TILE_HEADDIM:-8}
KEPT=${TILE_KEPT:-8}; PE=${TILE_PE:-8}
PASSES=$(( (KEPT + PE - 1) / PE ))
echo "尺寸 tileQ=$TQ tileK=$TK headDim=$HD kept=$KEPT pe=$PE -> $PASSES 趟"

# 挑**形状匹配**的最近一次抓取，匹配不上就明确失败。
#
# 这一步踩过两次同一个坑：先是写死作业号（拿新代码对旧数据），改成「取最近
# 一次」之后又撞上「最近一次是 kept=16 而测试是 kept=8」——两次都表现为
# 「已验证的路径突然全挂」，两次都不是被测对象的问题。
#
# **形状不匹配时不要退而求其次去找别的**：静默换一份数据正是这个坑本身。
if [ -z "${TILE_JSON:-}" ]; then
  TILE=""
  for cand in $(ls -dt "$ROOT"/runs/tile_*/tile.json 2>/dev/null); do
    # **四个维度全都要匹配**，不只是 kept。只比 kept 的版本刚好留着这个洞：
    # tile_17222412 是 headDim=8、tile_17221830 是 headDim=64，两份都 kept=16，
    # `ls -dt` 会给 headDim=64 的测试挑到 headDim=8 的数据——而那表现为
    # 「几乎每个维度都错」，看起来像被测对象坏了。
    ok=$("$ROOT/env/dynax-py312/bin/python" -c "
import json
p=json.load(open('$cand')).get('params') or {}
want=dict(tile_q=$TQ, tile_k=$TK, head_dim=$HD, kept=$KEPT)
print('yes' if all(p.get(k)==v for k,v in want.items()) else 'no')" 2>/dev/null)
    if [ "$ok" = "yes" ]; then TILE="$cand"; break; fi
  done
  [ -n "$TILE" ] || {
    echo "找不到 tileQ=$TQ tileK=$TK headDim=$HD kept=$KEPT 的抓取。跑："
    echo "  sbatch --export=ALL,TILE_Q=$TQ,TILE_K=$TK,TILE_HEADDIM=$HD,TILE_KEPT=$KEPT \\"
    echo "      slurm/kernel/dynax_capture_tile.slurm"
    exit 2; }
else
  TILE="$TILE_JSON"
fi
echo "金标准 $TILE（tileQ=$TQ tileK=$TK headDim=$HD kept=$KEPT）"

echo "=== 1. elaborate AttentionTile ==="
# psumBits 显式给，不让 Elaborate 从 width 推。见下面的实验：推出来的 10 位
# 和写死的 12 位在同一份激励上给出不同结果。
PSUM=${TILE_PSUM:-12}
SPEC="PLAN:bits=16,tileQ=$TQ,tileK=$TK,headDim=$HD,keptPerRow=$KEPT,peCountPerRow=$PE,psumBits=$PSUM,dividerStages=8"
echo "  psumBits=$PSUM"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "$SPEC" "$OUT/rtl" 2>&1 \
  | grep -E "^ELABORATE|FAIL"
V="$OUT/rtl/Plan/AttentionTile.v"
[ -f "$V" ] || { echo "elaborate 失败"; ls -R "$OUT/rtl" | head; exit 1; }
echo "Verilog $(wc -l < "$V") 行"

echo; echo "=== 2. verilate ==="
# 端口访问器按尺寸生成：手写的版本把「行 * 8 + k」写死了，kept=16 时索引
# 全错，而且是**静默**地读到另一个 lane。
"$ROOT/env/dynax-py312/bin/python" "$HW/tb/gen_ports.py" --module AttentionTile \
    --tile-q "$TQ" --tile-k "$TK" --head-dim "$HD" --kept "$KEPT" --pe "$PE" \
    --out "$OUT/tile_ports.h"
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
