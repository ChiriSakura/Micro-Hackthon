#!/usr/bin/env bash
#SBATCH --job-name=fast-activity-power
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=48G --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# **用真实激励的活动轨迹算功耗**，替掉那个拍脑袋的 0.2。
#
# 现在功耗模型的两个标定锚点里，RePEArray_L 明确记录用的是**默认常数
# 0.200** 而不是激励文件——只有 _S 是金标准激励数出来的真实翻转率。把两个
# 来源不一的数凑一起，正是我拒绝把预测阵列功耗加进目标函数的理由。
#
# OpenSTA 支持 read_vcd / read_saif / read_power_activities，所以这条路是通的：
#
#     Verilator --trace 跑真实 tile  ->  VCD
#     OpenSTA read_vcd 标注到映射后网表  ->  report_power
#
# **匹配是有限的**：VCD 来自 RTL 仿真，STA 跑在综合后的网表上，内部网名大多
# 对不上，只有端口和寄存器能匹配。所以这是"比 0.2 好很多"，不是"逐网精确"。
# 报告里必须说清楚匹配了多少。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/actpwr_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/actpwr-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"

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
T=AttentionTileTop
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
    --main-class Elaborate -- "$T" "$OUT/rtl" 2>&1 | grep -E "ELABORATE|error" | tail -2
V=$(find "$OUT/rtl" -name "$T.v" | head -1)
[ -z "$V" ] && { echo "FAIL: 没有 Verilog"; exit 1; }

# ---- 1. 带 VCD 的仿真：真实 Q/K/V ---------------------------------------
W="$OUT/sim"; mkdir -p "$W"
cp "$REPO/FAST/hardware/tb/tb_attention_tile_top.cpp" "$REPO/FAST/hardware/tb/golden.h" "$W/"
( cd "$W" && apptainer exec "$ROOT/containers/verilator.sif" verilator \
    --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" -Wno-fatal --trace \
    --top-module "$T" -CFLAGS "-I$W -DDUMP_VCD" \
    "$V" tb_attention_tile_top.cpp -o tb_act 2>&1 | tail -4 )
[ -x "$W/obj_dir/tb_act" ] || { echo "FAIL: 构建失败"; exit 1; }
( cd "$W" && apptainer exec "$ROOT/containers/verilator.sif" ./obj_dir/tb_act "$TILE" )
VCD=$(find "$W" -name "*.vcd" | head -1)
echo "VCD: ${VCD:-（没有产出——testbench 需要加 dump 代码）}"

# ---- 2. 综合 -------------------------------------------------------------
apptainer exec "$ROOT/containers/yosys.sif" yosys -p "
  read_verilog $V
  hierarchy -check -top $T
  proc
  select -set bc w:*ctrl_bcast* %ci
  setattr -set keep 1 @bc
  synth -top $T
  dfflibmap -liberty $LIB
  abc -liberty $LIB
  opt_clean
  stat -liberty $LIB
  write_verilog $OUT/$T.mapped.v" 2>&1 | grep -E "Chip area" | tail -1

# ---- 3. 两次功耗：假设的 0.2 vs 真实轨迹 ---------------------------------
for MODE in assumed measured; do
  echo; echo "--- 功耗（$MODE）---"
  {
    echo "read_liberty $LIB"
    echo "read_verilog $OUT/$T.mapped.v"
    echo "link_design $T"
    echo "create_clock -name clk -period 2.0 [get_ports clock]"
    if [ "$MODE" = assumed ]; then
      echo "set_power_activity -input -activity 0.2 -duty 0.5"
    else
      [ -z "$VCD" ] && { echo "puts \"没有 VCD，跳过\""; echo "exit"; } || \
        echo "read_vcd $VCD"
    fi
    echo "report_power -digits 6"
    echo "exit"
  } > "$OUT/pwr_$MODE.tcl"
  apptainer exec "$ROOT/containers/opensta.sif" /OpenSTA/build/sta -no_splash -exit \
      "$OUT/pwr_$MODE.tcl" 2>&1 | grep -vE "^Warning" | tail -10
done
