#!/usr/bin/env bash
#SBATCH --job-name=fast-rtl-verify
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# Elaborate one DynaX module and simulate it against golden vectors.
#
# Parameterised over (elaboration target, emitted top module, testbench,
# golden generator) so every module shares one flow. Runs on a compute node, not the login node: scala-cli's build server and
# the JVM both need more than a contended shared box gives them.
#
# Use fast_rtl_verify_all.slurm (same directory) to check every module; this one is for iterating
# on a single testbench. The resource request is sized to the work (a module
# takes about 30 seconds) because an over-request is what makes a short job
# ineligible for backfill and leaves it queued for far longer than it runs.
#
#   FAST_RTL_TARGET   Elaborate.scala entry, e.g. TopK / ExpUnit
#   FAST_RTL_TOP      module name in the emitted Verilog (differs when one
#                     Chisel class is elaborated at several configurations)
#   FAST_RTL_TB       testbench source in FAST/hardware
#   FAST_RTL_GOLDEN   extra args for gen_golden.py
#   FAST_RTL_SIM      extra args for the simulator binary
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
TARGET=${FAST_RTL_TARGET:-TopK}
TOP=${FAST_RTL_TOP:-$TARGET}
TB=${FAST_RTL_TB:-tb_topk.cpp}
GOLDEN_ARGS=${FAST_RTL_GOLDEN:-}
SIM_ARGS=${FAST_RTL_SIM:-16}
OUT="$ROOT/runs/rtl_${TARGET,,}_${SLURM_JOB_ID}"

export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier"
export SCALA_CLI_HOME="$ROOT/cache/scala-cli"
# 每个作业用自己的 .scala-build。
#
# 共享的后果撞到过三次：所有作业都从同一个仓库路径跑 `scala-cli run chisel`，
# 于是并发提交时它们编译进**同一个** FAST/hardware/chisel/.scala-build。
# 表现是随机一两个作业报 `FAIL: predict_unit/PrePEArray_1_2` 或干脆不产出
# ELABORATE 行——看起来像 RTL 坏了，串行重跑就全过。
export SCALA_BUILD_WS="${TMPDIR:-/tmp}/scala-build-${SLURM_JOB_ID:-$$}"
mkdir -p "$SCALA_BUILD_WS"

# Node-local: VAST cannot host the JVM's or Verilator's scratch files well, and
# apptainer cannot even unpack a layer there (system.nfs4_dacl is unremovable).
export TMPDIR=/tmp/fast-rtl-$$
mkdir -p "$TMPDIR" "$OUT"

echo "node=$(hostname) target=$TARGET top=$TOP tb=$TB out=$OUT"

echo "=== 1. elaborate Chisel -> Verilog ==="
cd "$REPO/FAST/hardware"
HW_DIR="$PWD"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "$TARGET" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)"

VERILOG="$OUT/rtl/$TARGET/${TOP}.v"
if [[ ! -f "$VERILOG" ]]; then
    echo "ELABORATION FAILED: no $VERILOG"; ls -R "$OUT/rtl" | head -20; exit 1
fi
echo "verilog lines: $(wc -l < "$VERILOG")"

echo "=== 2. golden vectors ==="
# shellcheck disable=SC2086
# PYTHONPATH so the golden/ package resolves regardless of the working
# directory the step happens to be in.
PYTHONPATH="$HW_DIR" "$ROOT/env/dynax-py312/bin/python" \
    "$HW_DIR/gen_golden.py" --out "$OUT/golden.json" $GOLDEN_ARGS

echo "=== 3. verilate + build the testbench ==="
cp "$HW_DIR/tb/$TB" "$HW_DIR/tb/golden.h" "$OUT/"
cd "$OUT"
# -Wno-fatal keeps generated Chisel style warnings (WIDTH, UNOPTFLAT) from
# stopping a functional check; lint is reported separately by the ALL sweep.
apptainer exec "$ROOT/containers/verilator.sif" verilator \
    --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" \
    -Wno-fatal --top-module "$TOP" -CFLAGS "-I$OUT" \
    "$VERILOG" "$(basename "$TB")" -o "tb_${TARGET}" 2>&1 | tail -25

BIN="$OUT/obj_dir/tb_${TARGET}"
if [[ ! -x "$BIN" ]]; then echo "BUILD FAILED: no $BIN"; exit 1; fi

echo "=== 4. simulate against golden vectors ==="
# shellcheck disable=SC2086
apptainer exec "$ROOT/containers/verilator.sif" "$BIN" "$OUT/golden.json" $SIM_ARGS
echo "simulation exit: $?"
