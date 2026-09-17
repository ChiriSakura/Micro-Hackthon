# Environment for every FAST/GCP command. Source it, do not execute it.
#   source FAST/scripts/gcp_env.sh
#
# Contains no secrets: only paths and ids. The ADC credential and the private
# keys stay on disk with 600 permissions and are never echoed.

export FAST_ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
export FAST_REPO=/home/gz2522/Micro-Hackthon

# gcloud must be APPENDED. Prepending puts its bundled interpreter ahead of the
# virtualenv and every FAST dependency then looks missing.
export PATH="$FAST_ROOT/env/fast-py312/bin:$PATH:$FAST_ROOT/tools/google-cloud-sdk/bin"

# The head is WHICHEVER login node you are on: CHIA binds its tunnel listeners to
# HEAD_IP on the machine running `chia up`, so an address belonging to a different
# login node fails with "Cannot assign requested address" only after the cloud VM
# exists. Derive it rather than hardcoding it.
#
# `hostname -I` lists the virtual 10.0.2.2 first and `ip route get` reports that
# same virtual address as the source, so both are filtered out; the loopback is
# no good either, since sshd refuses public-key auth there.
# Prefer the cluster's own 10.32.x network: compute nodes also carry container
# and fabric addresses (16.1.x, 10.0.x) that the tunnel cannot use.
export HEAD_IP="${HEAD_IP:-$(hostname -I | tr ' ' '\n' | grep -E '^10\.32\.' | head -1)}"
export HEAD_IP="${HEAD_IP:-$(hostname -I | tr ' ' '\n' | grep -Ev '^(10\.0\.|127\.|$)' | head -1)}"
[[ -n "$HEAD_IP" ]] || echo "WARNING: could not derive HEAD_IP; set it manually" >&2
export FAST_SSH_USER="$USER"
export FAST_HEAD_ENV="$FAST_ROOT/env/fast-py312"
export FAST_HEAD_KEY="$HOME/.ssh/id_ecdsa"

export GCP_PROJECT=project-842e7b1d-4f04-40b2-9b0
export GCP_ZONE=us-central1-a
export GCP_PRIVATE_KEY_PATH="$HOME/.ssh/fast_gcp_ed25519"
export GCP_PUBLIC_KEY_PATH="$HOME/.ssh/fast_gcp_ed25519.pub"

export FAST_CLUSTER="$FAST_REPO/FAST/configs/chia/fast-gcp.yaml"
