#!/usr/bin/env bash
#SBATCH --job-name=fast-gcp-bringup
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# Bring up the FAST/CHIA cluster with the head on THIS compute node.
#
# The head does not belong on a login node: Ray keeps its session directory in
# /tmp, and there /tmp is a 2 GB tmpfs shared by ~140 users that other jobs fill
# ("[Errno 28] No space left on device"), while ~28 contended cores make Ray miss
# its raylet startup deadline. A compute node has a real local disk and dedicated
# CPUs, and this cluster's compute nodes have the outbound 22/443 and inbound
# public-key SSH that CHIA needs (verified by slurm/fast_egress_probe.slurm).
#
# Submit WITHOUT --yes to stop after the dry-run and create nothing:
#   sbatch slurm/fast_gcp_bringup.slurm
# Submit with it to actually provision, verify and tear down:
#   FAST_BRINGUP_YES=1 sbatch --export=ALL slurm/fast_gcp_bringup.slurm

set -uo pipefail

REPO=/home/gz2522/Micro-Hackthon
# HEAD_IP must be this node, so let gcp_env.sh derive it here rather than
# inheriting whatever the submitting login node exported.
unset HEAD_IP
source "$REPO/FAST/scripts/gcp_env.sh"

# The login node exports TMPDIR=/scratch/... and sbatch --export=ALL carries it in
# here. Ray would then put its session directory under /scratch, and since the
# head's session path is reused verbatim by every worker, the GCP worker fails
# with "Permission denied: '/scratch'". Keep Ray on a path both sides have.
export TMPDIR=/tmp
export RAY_TMPDIR=/tmp/ray

export FAST_RUN_DIR=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/gcp_bringup_slurm_${SLURM_JOB_ID}

echo "head node : $(hostname) / $HEAD_IP"
echo "run dir   : $FAST_RUN_DIR"
df -h /tmp | tail -1

cd "$REPO"
if [[ "${FAST_BRINGUP_YES:-0}" == "1" ]]; then
    bash FAST/scripts/gcp_bringup_test.sh --yes
else
    bash FAST/scripts/gcp_bringup_test.sh
fi
code=$?

# Belt and braces: the script tears down from its own EXIT trap, but a Slurm
# timeout kills the job outright, so confirm the zone independently here too.
echo "=== final zone check ==="
python "$REPO/FAST/scripts/gcp_list_instances.py" || {
    echo "instances survived; deleting by label"
    python "$REPO/FAST/scripts/gcp_delete_instances.py" --cluster fast-gcp --yes
}
exit $code
