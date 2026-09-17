#!/usr/bin/env bash
#SBATCH --job-name=fast-power-recal
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=48G --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# **用修好的流程重测全部功耗锚点。**
#
# 现有标定全部来自 `set_power_activity -input -activity 0.2`，而实测证明：
#
#   1. `-input` 对内部网没有控制力 —— α 从 0.02 扫到 0.9（45 倍），总功耗
#      在 0.1079-0.1183 W 之间**非单调抖动**（±5%）。`-global` 是单调近似
#      线性的（0.0137 -> 0.0566 -> 0.2234 W）。
#   2. α=0.2 是个从未验证的假设 —— 真实 VCD 数出来是 **0.0213**。
#
#   叠加后同一个设计报 113.4 mW 而正确值 14.05 mW，**高估 8.07 倍**。
#
# 这里对每个锚点模块同时报三组数，让「换了什么导致了多少差别」可分离：
#
#   旧流程   -input  α=0.2     （复现历史值，验证我们在比同一个东西）
#   仅换旋钮 -global α=0.2     （隔离出 -input 的影响）
#   全修正   -global α=0.0213  （新的标定值）
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/pwrrecal_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/pwrrecal-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"

cd "$REPO/FAST/hardware"
printf "%-22s %14s %14s %14s\n" "模块" "旧(-input .2)" "-global .2" "-global .0213"
for T in RePEArray_S PrePEArray_S ExpUnit TopK BlockSched_S4 Divider; do
  scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
      --main-class Elaborate -- "$T" "$OUT/$T" >/dev/null 2>&1
  V=$(find "$OUT/$T" -name "*.v" 2>/dev/null | head -1)
  [ -z "$V" ] && { printf "%-22s %s\n" "$T" "（elaborate 失败，跳过）"; continue; }
  TOP=$(grep -oP '^module \K\w+' "$V" | tail -1)
  apptainer exec "$ROOT/containers/yosys.sif" yosys -p "
    read_verilog $V
    hierarchy -check -top $TOP
    proc
    select -set bc w:*ctrl_bcast* %ci
    setattr -set keep 1 @bc
    synth -top $TOP
    dfflibmap -liberty $LIB
    abc -liberty $LIB
    opt_clean
    write_verilog $OUT/$T.mapped.v" >/dev/null 2>&1
  [ -f "$OUT/$T.mapped.v" ] || { printf "%-22s %s\n" "$T" "（综合失败，跳过）"; continue; }

  VALS=""
  for CFG in "input 0.2" "global 0.2" "global 0.0213"; do
    set -- $CFG
    cat > "$OUT/p.tcl" <<TCL
read_liberty $LIB
read_verilog $OUT/$T.mapped.v
link_design $TOP
create_clock -name clk -period 2.0 [get_ports clock]
set_power_activity -$1 -activity $2 -duty 0.5
report_power -digits 6
exit
TCL
    W=$(apptainer exec "$ROOT/containers/opensta.sif" /OpenSTA/build/sta -no_splash -exit "$OUT/p.tcl" 2>/dev/null \
        | grep "^Total" | awk '{print $5}')
    MW=$("$ROOT/env/dynax-py312/bin/python" -c "print(f'{float('${W:-0}')*1000:.2f} mW')" 2>/dev/null || echo "n/a")
    VALS="$VALS $MW"
  done
  printf "%-22s %14s %14s %14s\n" "$T" $VALS
done
