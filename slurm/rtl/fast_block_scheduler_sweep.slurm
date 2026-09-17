#!/usr/bin/env bash
#SBATCH --job-name=fast-bs-sweep
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 量出 PE 利用率随队列深度的**实测**曲线，取代 pe_utilisation() 的一阶模型。
#
# 为什么要测：那个公式的注释自己写着「It is a model, not a measurement」，
# 而 queue_depth 是协同优化器的搜索维度。更糟的是公式对它单调递增、
# area_units() 又不收它的面积——只有收益没有成本，优化器必然选最深的。
# 流水化除法器那次是完全同一个形状的洞。
#
# 驱动用的是真实模型跑出来的逐 tile 行工作量（capture_row_workload.py），
# 不是合成分布：动态稀疏的全部问题就在于行长差异，那个差异假设不出来。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
HW_DIR="$REPO/FAST/hardware"
OUT="$ROOT/runs/bs_sweep_${SLURM_JOB_ID}"
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

export TMPDIR=/tmp/bs-sweep-$$; mkdir -p "$TMPDIR" "$OUT"

# 工作量文件：默认取最近一次抓取的结果。
WORKLOAD_DIR="${WORKLOAD_DIR:-$(ls -dt "$ROOT"/runs/workload_* 2>/dev/null | head -1)}"
if [[ ! -d "$WORKLOAD_DIR" ]]; then
    echo "找不到工作量目录；先跑 slurm/kernel/dynax_capture_workload.slurm"; exit 2
fi
echo "工作量来自 $WORKLOAD_DIR"

DEPTHS="${BS_DEPTHS:-0 2 4 8 16}"
METHODS="${BS_METHODS:-xm nm:16:64 topk:64 sanger}"

echo "=== 1. elaborate ==="
cd "$HW_DIR"
LIST=""
for d in $DEPTHS; do LIST="${LIST}BlockSched_S${d},"; done
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "LIST:${LIST%,}" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)" | tail -20

echo
echo "=== 2. verilate + 用真实工作量仿真 ==="
RESULTS="$OUT/measurements.txt"; : > "$RESULTS"
FAILED=0
for d in $DEPTHS; do
    TARGET="BlockSched_S${d}"
    VERILOG="$OUT/rtl/$TARGET/BlockScheduler.v"
    WORK="$OUT/$TARGET"; mkdir -p "$WORK"
    [[ -f "$VERILOG" ]] || { echo "$TARGET 没有 Verilog"; FAILED=1; continue; }

    "$PY" "$HW_DIR/tb/gen_ports.py" --module BlockScheduler \
        --rows 32 --pes 4 --queue-depth "$d" --col-bits 6 \
        --out "$WORK/array_ports.h" > /dev/null || { FAILED=1; continue; }
    cp "$HW_DIR/tb/tb_block_scheduler.cpp" "$WORK/"
    (cd "$WORK" && apptainer exec "$ROOT/containers/verilator.sif" verilator \
        --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" \
        -Wno-fatal --top-module BlockScheduler -CFLAGS "-I$WORK" \
        "$VERILOG" tb_block_scheduler.cpp -o "tb_${TARGET}" > "$WORK/build.log" 2>&1)
    BIN="$WORK/obj_dir/tb_${TARGET}"
    [[ -x "$BIN" ]] || { echo "$TARGET 构建失败，见 $WORK/build.log"; tail -15 "$WORK/build.log"; FAILED=1; continue; }

    for m in $METHODS; do
        STIM="$WORK/stim_$(echo "$m" | tr ':' '_').txt"
        "$PY" "$HW_DIR/golden/gen_workload_stimulus.py" \
            --workload "$WORKLOAD_DIR/workload_rows32.json" \
            --method "$m" --pe 4 --max-tiles "${BS_MAX_TILES:-256}" \
            --out "$STIM" > /dev/null || { FAILED=1; continue; }
        R=$(apptainer exec "$ROOT/containers/verilator.sif" "$BIN" "$STIM")
        echo "--- depth=$d method=$m ---"; echo "$R"
        echo "$R" | grep '^MEASURE' | sed "s/^MEASURE /method=$m /" >> "$RESULTS"
        echo "$R" | grep -q '^PASSED' || FAILED=1
    done
done

echo
echo "=== 实测汇总 ==="
cat "$RESULTS"
echo "结果文件 $RESULTS"
echo "overall: $([[ $FAILED == 0 ]] && echo ALL PASSED || echo FAILURES PRESENT)"
exit $FAILED
