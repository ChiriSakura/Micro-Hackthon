#!/usr/bin/env bash
# One controlled end-to-end GCP bring-up: render, preflight, dry-run, provision,
# verify the five-agent graph really ran on the cloud worker, then tear down.
#
# Teardown runs from an EXIT trap, so an interrupt or a failed verification still
# destroys the instance. Billing stops when the VM is deleted, not when it idles.
#
#   bash FAST/scripts/gcp_bringup_test.sh            # stops after dry-run
#   bash FAST/scripts/gcp_bringup_test.sh --yes      # actually provisions
#
# Requires FAST/scripts/gcp_env.sh to have been sourced, or sources it itself.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
# shellcheck source=/dev/null
[[ -n "${FAST_CLUSTER:-}" ]] || source "$HERE/gcp_env.sh"

PROVISION=0
[[ "${1:-}" == "--yes" ]] && PROVISION=1

RUN_DIR="${FAST_RUN_DIR:-$FAST_ROOT/runs/gcp_bringup_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$RUN_DIR"
TEMPLATE="$REPO/FAST/configs/chia/fast-gcp.yaml.example"

step() { printf '\n=== %s ===\n' "$*"; }
# Deliberately not the gcloud CLI: it takes over a minute to start from shared
# storage, and this runs on the teardown path where confirmation must be prompt.
# One call does both jobs: importing google-cloud-compute is the expensive part
# (about four minutes cold off shared storage), so listing the zone and testing
# whether it is empty separately would pay for it twice.
#   $1 = file to record the listing in; returns 0 when the zone is empty.
list_instances() {
    local file="$1" code
    python "$HERE/gcp_list_instances.py" --project "$GCP_PROJECT" --zone "$GCP_ZONE" >"$file" 2>&1
    code=$?
    cat "$file"
    return $code
}

teardown() {
    local code=$?
    if [[ "$PROVISION" == "1" ]]; then
        step "TEARDOWN (exit code $code)"
        # -y is mandatory: this runs detached with no stdin, and without it
        # `chia down` blocks on its confirmation prompt, hits EOF, and leaves
        # the instance running and billing.
        chia down -y "$FAST_CLUSTER" 2>&1 | tee "$RUN_DIR/down.log" ||
            echo "chia down FAILED - falling back to deleting instances directly"

        echo "remaining instances (must be empty):"
        if ! list_instances "$RUN_DIR/instances_after.txt"; then
            echo "instances survived chia down; deleting them by label"
            python "$HERE/gcp_delete_instances.py" \
                --project "$GCP_PROJECT" --zone "$GCP_ZONE" \
                --cluster "$(awk '/^cluster_name:/{print $2}' "$FAST_CLUSTER")" --yes 2>&1 |
                tee "$RUN_DIR/force_delete.log"
            list_instances "$RUN_DIR/instances_after.txt" || true
        fi

        if list_instances /dev/null; then
            echo "all instances released"
        else
            echo "!!! INSTANCES STILL EXIST AND ARE STILL BILLING !!!"
            echo "!!! delete them: gcloud compute instances delete <name> --project $GCP_PROJECT --zone $GCP_ZONE"
            exit 1
        fi
    fi
    exit $code
}

step "0. preconditions"
echo "run dir : $RUN_DIR"
echo "project : $GCP_PROJECT / $GCP_ZONE"
echo "head    : $FAST_SSH_USER@$HEAD_IP"
echo "pre-existing instances:"
list_instances "$RUN_DIR/instances_before.txt" ||
    echo "NOTE: instances already exist; this script does not touch them."

step "1. render cluster config"
python "$HERE/gcp_render_cluster.py" --template "$TEMPLATE" --out "$FAST_CLUSTER" |
    tee "$RUN_DIR/render.log"

step "2. preflight (creates nothing)"
python "$HERE/gcp_preflight.py" --config "$FAST_CLUSTER" --json "$RUN_DIR/preflight.json" |
    tee "$RUN_DIR/preflight.log"

step "3. dry-run (creates nothing)"
chia up --dry-run "$FAST_CLUSTER" 2>&1 | tee "$RUN_DIR/dryrun.log"
grep -q "Dry run complete" "$RUN_DIR/dryrun.log" || { echo "dry-run did not complete"; exit 1; }

if [[ "$PROVISION" != "1" ]]; then
    step "STOPPING BEFORE PROVISIONING"
    echo "Everything that creates nothing has passed. Re-run with --yes to provision."
    exit 0
fi

trap teardown EXIT INT TERM

step "4. provision and start Ray  (BILLING STARTS HERE)"
date -u +'started %Y-%m-%dT%H:%M:%SZ' | tee "$RUN_DIR/started.txt"
chia up --yes "$FAST_CLUSTER" 2>&1 | tee "$RUN_DIR/up.log"

step "5. cluster status"
list_instances "$RUN_DIR/instances_during.txt" || true
chia status --chia-cluster "$FAST_CLUSTER" 2>&1 | tee "$RUN_DIR/status.log" || true

step "6. verify the graph runs ON THE CLOUD WORKER"
cd "$REPO/FAST"
python -m fast.runtime.cloud_smoke --output "$RUN_DIR/cloud_report.json" |
    tee "$RUN_DIR/cloud_smoke.log"

step "7. done - teardown follows"
