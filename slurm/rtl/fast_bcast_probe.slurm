#!/usr/bin/env bash
#SBATCH --job-name=fast-bcast-probe
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=48G --time=01:30:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 试三种 yosys 写法，看哪一种真的能保住广播树。
#
# `setattr -set keep 1 w:*ctrl_bcast*` 选的是**线网**，而 `opt_merge` 合并的
# 是**单元**——实测名字在网表里（2192 处）但 DFF 只多了 8 个，树被合光了。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/bprobe_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/bprobe-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"

cd "$REPO/FAST/hardware"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
    --main-class Elaborate -- PrePEArray_S_Buffered "$OUT/rtl" 2>&1 | grep -E "ELABORATE|error" | tail -2
V=$(find "$OUT/rtl" -name "*.v" | head -1)
TOP=$(grep -oP '^module \K\w+' "$V" | tail -1)
echo "顶层 $TOP"

run_variant () {
  local name="$1" keep="$2"
  echo; echo "--- $name ---"
  apptainer exec "$ROOT/containers/yosys.sif" yosys -p "
    read_verilog $V
    hierarchy -check -top $TOP
    proc
    $keep
    synth -top $TOP
    dfflibmap -liberty $LIB
    abc -liberty $LIB
    opt_clean
    stat -liberty $LIB
    write_verilog $OUT/$name.mapped.v" 2>&1 | grep -E "Chip area|Number of cells:" | tail -2
  echo -n "  DFF 数: "; grep -c "DFF_X1" "$OUT/$name.mapped.v"
}

run_variant "A_none"      ""
run_variant "B_wire_keep" "setattr -set keep 1 w:*ctrl_bcast*"
run_variant "C_cell_keep" "select -set bc w:*ctrl_bcast* %ci; setattr -set keep 1 @bc"
run_variant "D_nomerge"   "setattr -set keep 1 w:*ctrl_bcast* %ci*"
