#!/usr/bin/env bash
#SBATCH --job-name=fast-kf-sweep
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 量出真实稀疏索引流下的 bank 冲突代价——周期模型里完全缺失的那一项。
#
# `cycles = sparse_macs / (lanes * utilisation)` 一项和访存都没有，等于假设
# 带宽无限。而缺口是结构性的：阵列每拍要 regWidth 个新 K 标量（DynaX-S
# 128 位/拍），上游的 SRAM 是单地址端口、每拍 64 位。
#
# 用真实索引而不是随机数：冲突取决于索引的分布不是个数。xm 按块保留
# （索引聚簇），topk 全局取大（索引分散），`bank = col % bankCount` 下
# 两者撞 bank 的方式完全不同。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
HW_DIR="$REPO/FAST/hardware"
OUT="$ROOT/runs/kf_sweep_${SLURM_JOB_ID}"
PY="$ROOT/env/dynax-py312/bin/python"

export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
# 每个作业用自己的 .scala-build。
#
# 共享的后果撞到过三次：所有作业都从同一个仓库路径跑 `scala-cli run chisel`，
# 于是并发提交时它们编译进**同一个** FAST/hardware/chisel/.scala-build。
# 表现是随机一两个作业报 `FAIL: predict_unit/PrePEArray_1_2` 或干脆不产出
# ELABORATE 行——看起来像 RTL 坏了，串行重跑就全过。
export SCALA_BUILD_WS="${TMPDIR:-/tmp}/scala-build-${SLURM_JOB_ID:-$$}"
mkdir -p "$SCALA_BUILD_WS"

export TMPDIR=/tmp/kf-sweep-$$; mkdir -p "$TMPDIR" "$OUT"

WORKLOAD_DIR="${WORKLOAD_DIR:-$(ls -dt "$ROOT"/runs/workload_* 2>/dev/null | head -1)}"
WORKLOAD="$WORKLOAD_DIR/workload_rows32.json"
[[ -f "$WORKLOAD" ]] || { echo "找不到 $WORKLOAD；先跑 dynax_capture_workload.slurm"; exit 2; }
"$PY" -c "
import json,sys
d=json.load(open('$WORKLOAD'))
if not any('tile_indices' in m for m in d['methods'].values()):
    sys.exit('工作量文件里没有 tile_indices——重跑抓取时要加 --emit-indices')
" || exit 2
echo "工作量来自 $WORKLOAD_DIR"

BANKS="${KF_BANKS:-4 8 16 32}"
METHODS="${KF_METHODS:-xm nm:16:64 topk:64 sanger}"
REGW="${KF_REGW:-8}"
VARIANT="${KF_VARIANT:-S}"

echo "=== 1. elaborate ==="
cd "$HW_DIR"
LIST=""; for b in $BANKS; do LIST="${LIST}KeyFeeder_${VARIANT}${b},"; done
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "LIST:${LIST%,}" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)" | tail -12

echo; echo "=== 2. verilate + 真实索引流仿真 ==="
RESULTS="$OUT/measurements.txt"; : > "$RESULTS"
FAILED=0
for b in $BANKS; do
    TARGET="KeyFeeder_${VARIANT}${b}"
    VERILOG="$OUT/rtl/$TARGET/KeyFeeder.v"
    WORK="$OUT/$TARGET"; mkdir -p "$WORK"
    [[ -f "$VERILOG" ]] || { echo "$TARGET 没有 Verilog"; FAILED=1; continue; }

    "$PY" "$HW_DIR/tb/gen_ports.py" --module KeyFeeder \
        --reg-width2 "$REGW" --banks "$b" --col-bits 11 \
        --out "$WORK/array_ports.h" > /dev/null || { FAILED=1; continue; }
    cp "$HW_DIR/tb/tb_key_feeder.cpp" "$WORK/"
    (cd "$WORK" && apptainer exec "$ROOT/containers/verilator.sif" verilator \
        --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" \
        -Wno-fatal --top-module KeyFeeder -CFLAGS "-I$WORK" \
        "$VERILOG" tb_key_feeder.cpp -o "tb_${TARGET}" > "$WORK/build.log" 2>&1)
    BIN="$WORK/obj_dir/tb_${TARGET}"
    [[ -x "$BIN" ]] || { echo "$TARGET 构建失败"; tail -15 "$WORK/build.log"; FAILED=1; continue; }

    for m in $METHODS; do
        STIM="$WORK/stim_$(echo "$m" | tr ':' '_').txt"
        "$PY" "$HW_DIR/golden/gen_gather_stimulus.py" \
            --workload "$WORKLOAD" --method "$m" --reg-width "$REGW" --banks "$b" \
            --total-cols 2048 --max-groups "${KF_MAX_GROUPS:-2048}" \
            --out "$STIM" || { FAILED=1; continue; }
        R=$(apptainer exec "$ROOT/containers/verilator.sif" "$BIN" "$STIM")
        echo "--- banks=$b method=$m ---"; echo "$R"
        echo "$R" | grep '^MEASURE' | sed "s/^MEASURE /method=$m /" >> "$RESULTS"
        echo "$R" | grep -q '^PASSED' || FAILED=1
    done
done

echo; echo "=== 实测汇总 ==="
cat "$RESULTS"
echo "结果文件 $RESULTS"
echo "overall: $([[ $FAILED == 0 ]] && echo ALL PASSED || echo FAILURES PRESENT)"
exit $FAILED
