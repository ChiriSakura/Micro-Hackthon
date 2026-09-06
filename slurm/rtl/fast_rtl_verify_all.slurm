#!/usr/bin/env bash
#SBATCH --job-name=fast-rtl-verify-all
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# Verify every DynaX module against its golden vectors, in one allocation.
#
# One job, not one per module. Each module takes about 30 seconds, but a job
# spends far longer waiting to be scheduled, so eight submissions paid the queue
# eight times. The resource request is sized to the work for the same reason: a
# 4-minute job that asks for 8 CPUs and an hour is ineligible for backfill,
# which is what leaves it sitting behind a 160-deep queue.
#
# The JVM is started once and reused across modules, so elaboration after the
# first is a few hundred milliseconds.
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/rtl_verify_all_${SLURM_JOB_ID}"

export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier"
export SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export TMPDIR=/tmp/fast-rtl-$$
PY="$ROOT/env/dynax-py312/bin/python"
mkdir -p "$TMPDIR" "$OUT"
cd "$REPO/FAST/hardware"
HW_DIR="$PWD"

echo "node=$(hostname) partition=${SLURM_JOB_PARTITION:-?} out=$OUT"

# target | top module | testbench | gen_golden args | sim args
MODULES=(
  "TopK|TopK|tb_topk.cpp||16"
  "ExpUnit|ExpUnitFixPoint|tb_exp.cpp|--module ExpUnit|"
  "PSumSoftmax|PSumSoftmax|tb_psum_softmax.cpp|--module PSumSoftmax|"
  "SRAM|SRAM|tb_sram.cpp|--module SRAM|"
  "RePE|RePE|tb_repe.cpp|--module RePE|"
  "RePERow|RePERow|tb_repe_row.cpp|--module RePERow --pe-count 8 --reg-width 8|"
  "RePEArray_T|RePEArray|tb_repe_array.cpp|--module RePEArray --num-rows 4 --pe-count 2 --reg-width 4|"
  "PrePE_1_2|PrePE_1_2|tb_prepe.cpp|--module PrePE --out-bits 12|"
  "PrePEArray_T|PrePEArray_1_2|tb_prepe_array.cpp|--module PrePEArray --height 2 --width 8 --out-bits 12|"
  "PrePEArray14_T|PrePEArray_1_4|tb_prepe_array14.cpp|--module PrePEArray14 --height 2 --width 8 --out-bits 15|"
)

echo "=== 1. elaborate every target (one JVM) ==="
TARGETS=$(printf "%s\n" "${MODULES[@]}" | cut -d'|' -f1 | paste -sd,)
scala-cli run chisel --server=false --main-class Elaborate -- "LIST:$TARGETS" "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)"

echo
echo "=== 2. verilate and simulate each ==="
declare -a SUMMARY
FAILED=0
for SPEC in "${MODULES[@]}"; do
    IFS='|' read -r TARGET TOP TB GOLDEN SIM <<< "$SPEC"
    WORK="$OUT/$TARGET"
    mkdir -p "$WORK"
    VERILOG="$OUT/rtl/$TARGET/${TOP}.v"
    if [[ ! -f "$VERILOG" ]]; then
        SUMMARY+=("$(printf '  %-14s ELABORATION FAILED' "$TARGET")"); FAILED=1; continue
    fi

    # shellcheck disable=SC2086
    PYTHONPATH="$HW_DIR" "$PY" "$HW_DIR/gen_golden.py" \
        --out "$WORK/golden.json" $GOLDEN > /dev/null || {
        SUMMARY+=("$(printf '  %-14s GOLDEN FAILED' "$TARGET")"); FAILED=1; continue; }

    cp "$HW_DIR/tb/$TB" "$HW_DIR/tb/golden.h" "$WORK/"
    (cd "$WORK" && apptainer exec "$ROOT/containers/verilator.sif" verilator \
        --cc --exe --build -j "${SLURM_CPUS_PER_TASK:-4}" \
        -Wno-fatal --top-module "$TOP" -CFLAGS "-I$WORK" \
        "$VERILOG" "$TB" -o "tb_${TARGET}" > "$WORK/build.log" 2>&1)

    BIN="$WORK/obj_dir/tb_${TARGET}"
    if [[ ! -x "$BIN" ]]; then
        SUMMARY+=("$(printf '  %-14s BUILD FAILED (see %s)' "$TARGET" "$WORK/build.log")")
        FAILED=1; continue
    fi

    echo "--- $TARGET ---"
    # shellcheck disable=SC2086
    RESULT=$(apptainer exec "$ROOT/containers/verilator.sif" "$BIN" "$WORK/golden.json" $SIM)
    echo "$RESULT"
    VERDICT=$(printf '%s' "$RESULT" | grep -E "^(PASSED|FAILED):" | tail -1)
    SUMMARY+=("$(printf '  %-14s %s' "$TARGET" "${VERDICT:-no verdict}")")
    [[ "$VERDICT" == FAILED:* || -z "$VERDICT" ]] && FAILED=1
done

echo
echo "=== summary ==="
printf '%s\n' "${SUMMARY[@]}"
echo "overall: $([[ $FAILED == 0 ]] && echo ALL PASSED || echo FAILURES PRESENT)"
exit $FAILED
