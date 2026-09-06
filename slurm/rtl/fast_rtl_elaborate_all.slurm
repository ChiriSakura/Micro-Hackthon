#!/usr/bin/env bash
#SBATCH --job-name=fast-rtl-all
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# Elaborate every DynaX module, then Verilator-lint each emitted design.
#
# This is the gate the DynaX release does not pass on its own: five of its eight
# sources import exp_unit.ExpUnitFixPoint, which the release does not contain.
# FAST supplies that module (FAST/hardware/src/main/scala/exp_unit/exp_unit.scala),
# so a green sweep here means "DynaX + one reconstructed unit", not "DynaX".
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/rtl_all_${SLURM_JOB_ID}"

export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier"
export SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export TMPDIR=/tmp/fast-rtl-$$
mkdir -p "$TMPDIR" "$OUT"

echo "node=$(hostname) out=$OUT"

echo "=== 1. elaborate every module (one JVM) ==="
cd "$REPO/FAST/hardware"
rm -rf chisel/.scala-build
scala-cli run chisel --server=false --main-class Elaborate -- ALL "$OUT" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)"
ELAB_RC=${PIPESTATUS[0]}
echo "elaboration exit: $ELAB_RC"

echo
echo "=== 2. verilator lint each emitted design ==="
LINT_FAIL=0
for V in "$OUT"/*/*.v; do
    [[ -e "$V" ]] || continue
    NAME=$(basename "$V" .v)
    TARGET=$(basename "$(dirname "$V")")
    ERRS=$(apptainer exec "$ROOT/containers/verilator.sif" \
        verilator --lint-only -Wno-fatal --top-module "$NAME" "$V" 2>&1 \
        | grep -cE "^%Error" || true)
    printf "  LINT %-16s (%s) %6s lines  %s errors\n" "$TARGET" "$NAME" "$(wc -l < "$V")" "$ERRS"
    [[ "$ERRS" != "0" ]] && LINT_FAIL=1
done

echo
echo "=== 3. summary ==="
echo "verilog files emitted: $(ls -1 "$OUT"/*/*.v 2>/dev/null | wc -l)"
echo "elaboration rc=$ELAB_RC  lint_fail=$LINT_FAIL"
