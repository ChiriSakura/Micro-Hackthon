#!/usr/bin/env bash
#SBATCH --job-name=fast-rtl-paper
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 在论文报告的阵列尺寸上做功能验证。
#
#   DynaX-S  PrePEA 32x32 (4-bit, 1:2)  +  RePEA 32x4  (regWidth 8)
#   DynaX-L  PrePEA 64x32 (6-bit, 1:4)  +  RePEA 64x8  (regWidth 16)
#
# 和 fast_rtl_verify_all.slurm 分开，因为这里的 Verilog 大一个数量级
# （PrePEArray_1_4 是 32271 行），verilate 要几分钟而不是几秒。日常迭代
# 用小实例，这个作业回答的是「论文尺寸下是否仍然成立」。
#
# testbench 的端口访问由 tb/gen_ports.py 生成：64x8 阵列光 sel_cols 就有
# 512 个端口。testbench 的逻辑仍是手写的。
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/rtl_paper_${SLURM_JOB_ID}"

export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier"
export SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export TMPDIR=/tmp/fast-paper-$$
PY="$ROOT/env/dynax-py312/bin/python"
mkdir -p "$TMPDIR" "$OUT"
cd "$REPO/FAST/hardware"; HW_DIR="$PWD"

echo "node=$(hostname) out=$OUT"

# 目标 | 顶层模块 | testbench | gen_golden 参数 | gen_ports 参数
MODULES=(
  "RePEArray_S|RePEArray|tb_repe_array.cpp|--module RePEArray --num-rows 32 --pe-count 4 --reg-width 8|--module RePEArray --rows 32 --pes 4 --reg-width 8"
  "RePEArray_L|RePEArray|tb_repe_array.cpp|--module RePEArray --num-rows 64 --pe-count 8 --reg-width 16|--module RePEArray --rows 64 --pes 8 --reg-width 16"
  "PrePEArray_S|PrePEArray_1_2|tb_prepe_array.cpp|--module PrePEArray --height 32 --width 32 --out-bits 12|--module PrePEArray_1_2 --height 32 --width 32"
  "PrePEArray_L|PrePEArray_1_4|tb_prepe_array14.cpp|--module PrePEArray14 --height 64 --width 32 --out-bits 15|--module PrePEArray_1_4 --height 64 --width 32"
)

echo "=== 1. elaborate（一个 JVM）==="
TARGETS=$(printf "%s\n" "${MODULES[@]}" | cut -d'|' -f1 | paste -sd,)
scala-cli run chisel --server=false --main-class Elaborate -- "LIST:$TARGETS" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)"

echo; echo "=== 2. 逐个 verilate 并仿真 ==="
declare -a SUMMARY; FAILED=0
for SPEC in "${MODULES[@]}"; do
    IFS='|' read -r TARGET TOP TB GOLDEN PORTS <<< "$SPEC"
    WORK="$OUT/$TARGET"; mkdir -p "$WORK"
    VERILOG="$OUT/rtl/$TARGET/${TOP}.v"
    [[ -f "$VERILOG" ]] || { SUMMARY+=("  $TARGET ELABORATION FAILED"); FAILED=1; continue; }
    echo "--- $TARGET ($(wc -l < "$VERILOG") 行 Verilog) ---"

    # shellcheck disable=SC2086
    PYTHONPATH="$HW_DIR" "$PY" "$HW_DIR/gen_golden.py" --out "$WORK/golden.json" $GOLDEN || {
        SUMMARY+=("  $TARGET GOLDEN FAILED"); FAILED=1; continue; }
    # shellcheck disable=SC2086
    "$PY" "$HW_DIR/tb/gen_ports.py" --out "$WORK/array_ports.h" $PORTS || {
        SUMMARY+=("  $TARGET PORTS FAILED"); FAILED=1; continue; }

    cp "$HW_DIR/tb/$TB" "$HW_DIR/tb/golden.h" "$WORK/"
    (cd "$WORK" && apptainer exec "$ROOT/containers/verilator.sif" verilator \
        --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-8}" \
        -Wno-fatal --top-module "$TOP" -CFLAGS "-I$WORK" \
        "$VERILOG" "$TB" -o "tb_${TARGET}" > "$WORK/build.log" 2>&1)

    BIN="$WORK/obj_dir/tb_${TARGET}"
    [[ -x "$BIN" ]] || { SUMMARY+=("  $TARGET BUILD FAILED（见 $WORK/build.log）"); FAILED=1; continue; }

    RESULT=$(apptainer exec "$ROOT/containers/verilator.sif" "$BIN" "$WORK/golden.json")
    echo "$RESULT" | tail -12
    VERDICT=$(printf '%s' "$RESULT" | grep -E "^(PASSED|FAILED):" | tail -1)
    SUMMARY+=("$(printf '  %-14s %s' "$TARGET" "${VERDICT:-no verdict}")")
    [[ "$VERDICT" == FAILED:* || -z "$VERDICT" ]] && FAILED=1
done

echo; echo "=== 论文尺寸小结 ==="
printf '%s\n' "${SUMMARY[@]}"
echo "overall: $([[ $FAILED == 0 ]] && echo ALL PASSED || echo FAILURES PRESENT)"
exit $FAILED
