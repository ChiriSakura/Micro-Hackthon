#!/usr/bin/env bash
#SBATCH --job-name=fast-egress-probe
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err
set -uo pipefail
# Can a compute node act as the CHIA head? It needs local disk for Ray, an
# address the tunnel can bind, public-key SSH in, and outbound 22/443 to GCP.
echo "host      : $(hostname)"
echo "addresses : $(hostname -I)"
echo "cpus      : $(nproc)"
echo "--- /tmp (Ray's session dir lives here) ---"
df -h /tmp /dev/shm | tail -2
echo "--- outbound 443 to Google APIs ---"
timeout 20 bash -c 'exec 3<>/dev/tcp/compute.googleapis.com/443' && echo "443 OK" || echo "443 BLOCKED"
echo "--- outbound 22 to a public host ---"
timeout 20 bash -c 'exec 3<>/dev/tcp/github.com/22' && echo "22 OK" || echo "22 BLOCKED"
echo "--- inbound public-key SSH to this node from itself ---"
timeout 25 ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    -o PreferredAuthentications=publickey -i "$HOME/.ssh/id_ecdsa" \
    "$(hostname -I | tr ' ' '\n' | grep -Ev '^(10\.0\.|127\.|$)' | head -1)" \
    'echo "publickey SSH OK on $(hostname)"' 2>&1 | tail -2
