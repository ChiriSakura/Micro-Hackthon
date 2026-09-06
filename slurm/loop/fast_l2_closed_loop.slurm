#!/usr/bin/env bash
#SBATCH --job-name=fast-l2-loop
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# Run the co-design loop and confirm its winner by simulating the RTL.
#
# Needs a compute node rather than the login node because step 3 shells out to
# fast_rtl_verify.slurm, which starts a JVM, elaborates Chisel and builds a
# Verilator model. Those #SBATCH lines are comments when the script is sourced
# inline like this; SLURM_JOB_ID is inherited from this allocation.
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
TEMPLATE=${FAST_L2_TEMPLATE:-topk}

export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier"
export SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export TMPDIR=/tmp/fast-l2-$$
mkdir -p "$TMPDIR"

echo "node=$(hostname) template=$TEMPLATE"
cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/dynax-py312/bin/python" \
    scripts/l2_closed_loop.py --repo-root "$REPO" --template "$TEMPLATE"
echo "closed loop exit: $?"
