#!/usr/bin/env bash
#SBATCH --job-name=fast-bcast-fanout
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=48G --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 预测阵列控制广播扇出的**对照实验**。
#
# `pes_state` 从单个端口直驱最多 2048 个 PE 的 state 口，中间无缓冲。
# 实测后果：PrePEArray_1_4 里一个 NOR2_X1 报出 196 ns（真实约 0.02 ns），
# 起点正是广播给 512 个 PE 的 io_array_state。时序适配器的 timing_credible
# 守卫因此把这类结果整个丢弃——预测阵列从来没有可用的时序数。
#
# 这里同一个阵列跑两次，只改广播树级数，量三件事：
#   时序是否从"不可信"变成可用 / 面积代价 / 延迟代价（stages 拍）
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/bcast_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/bcast-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"

cd "$REPO/FAST/hardware"
for T in PrePEArray_S_Flat PrePEArray_S_Buffered PrePEArray_Plan_Flat PrePEArray_Plan_Buffered; do
  echo; echo "================ $T ================"
  scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
      --main-class Elaborate -- "$T" "$OUT/$T" 2>&1 | grep -E "ELABORATE|error" | tail -3
  V=$(find "$OUT/$T" -name "*.v" | head -1)
  [ -z "$V" ] && { echo "  没有产出 Verilog"; continue; }

  TOP=$(grep -oP '^module \K\w+' "$V" | tail -1)
  apptainer exec "$ROOT/containers/yosys.sif" yosys -p "
    read_verilog $V
    hierarchy -check -top $TOP
    # **保住广播树。** Chisel 的 dontTouch 只管到 FIRRTL；yosys 的 opt_merge
    # 看见一堆功能等价的寄存器会合并回一个——整棵树消失、扇出原样不动，
    # 而且不报任何错。实测撞到过：加了两级树后 STA 仍报一个 DFF 驱动 516 个
    # 负载（= 512 个 PE 的总数）。
    # 选**驱动这些线的单元**（`%ci`），不是线本身。实测：按线网设 keep
    # 之后 DFF 数一个没多（1891，和扁平版相同），树被 opt_merge 合光了；
    # 按驱动单元设 keep 之后是 2523，+632 正好是两棵两级树的规模。
    proc
    select -set bc w:*ctrl_bcast* %ci
    setattr -set keep 1 @bc
    synth -top $TOP
    dfflibmap -liberty $LIB
    abc -liberty $LIB
    opt_clean
    stat -liberty $LIB
    write_verilog $OUT/$T.mapped.v" 2>&1 | grep -E "Chip area|Number of cells" | tail -2

  # STA：**加扇出与转换时间约束**，让违例被报出来而不是静默。
  cat > "$OUT/sta_$T.tcl" <<TCL
read_liberty $LIB
read_verilog $OUT/$T.mapped.v
link_design $TOP
create_clock -name clk -period 2.0 [get_ports clock]
set_input_delay 0.1 -clock clk [all_inputs -no_clocks]
set_output_delay 0.1 -clock clk [all_outputs]
set_max_fanout 16 [current_design]
set_max_transition 0.15 [current_design]
report_checks -path_delay max -digits 4 -fields {slew capacitance fanout}
report_check_types -max_fanout -max_capacitance
exit
TCL
  apptainer exec "$ROOT/containers/opensta.sif" /OpenSTA/build/sta -no_splash -exit "$OUT/sta_$T.tcl" 2>&1 \
    | grep -E "data arrival time|slack \(|\(in\)|DFF_X1\)|NOR2|INV_X1" | head -10
done
