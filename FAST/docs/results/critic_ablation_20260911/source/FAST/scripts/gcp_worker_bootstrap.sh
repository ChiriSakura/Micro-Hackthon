#!/usr/bin/env bash
# Prepare a fresh GCP VM to act as a FAST/CHIA Ray worker.
#
# Idempotent: safe to re-run, and a second run costs a few seconds. CHIA invokes
# it from worker_env_commands before `ray start`, and it can also be run by hand
# or dropped in as a GCE startup-script.
#
# Ray compares the FULL Python version, not just the minor: a head on 3.12.9 and a
# worker on 3.12.3 both satisfy "3.12" and Ray still refuses to join with
# "Version mismatch". Distro packages cannot be relied on to supply an exact
# patch release, so the exact version is fetched with uv (a standalone CPython
# build) whenever the system interpreter does not already match.
#
#   FAST_PYTHON_VERSION Exact X.Y.Z the head runs                 (default 3.12.3)
#   FAST_CHIA_VERSION   chialoops release; it pins Ray itself     (default 1.0.1)
#   FAST_ENV_DIR        virtualenv to create                      (default ~/fast-env)
#   FAST_WITH_VERILATOR install Verilator for L2 evaluation       (default 0)
#   FAST_WITH_CHISEL    install JDK + sbt for Chisel elaboration  (default 0)

set -euo pipefail

PYTHON_VERSION="${FAST_PYTHON_VERSION:-3.12.3}"
PYTHON_MINOR="${PYTHON_VERSION%.*}"
CHIA_VERSION="${FAST_CHIA_VERSION:-1.0.1}"
ENV_DIR="${FAST_ENV_DIR:-$HOME/fast-env}"
WITH_VERILATOR="${FAST_WITH_VERILATOR:-0}"
WITH_CHISEL="${FAST_WITH_CHISEL:-0}"
LOG="$HOME/fast_bootstrap.log"
MARKER="$ENV_DIR/.fast-bootstrap-complete"
STAMP="python=${PYTHON_VERSION} chia=${CHIA_VERSION} verilator=${WITH_VERILATOR} chisel=${WITH_CHISEL}"

log() { printf '[bootstrap] %s %s\n' "$(date -u +%H:%M:%S)" "$*" | tee -a "$LOG"; }
die() { printf '[bootstrap] ERROR %s\n' "$*" | tee -a "$LOG" >&2; exit 1; }

# A completed run with the same requirements is a no-op.
if [[ -f "$MARKER" && "$(cat "$MARKER")" == "$STAMP" ]]; then
    log "already provisioned for: $STAMP"
    exit 0
fi

log "provisioning for: $STAMP"

apt_get() {
    sudo DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 "$@"
}

# The GCE guest agent and unattended-upgrades both hold the dpkg lock at boot.
log "waiting for any boot-time package activity to finish"
for _ in $(seq 1 60); do
    if ! sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then break; fi
    sleep 5
done

log "installing base packages"
apt_get update -qq
apt_get install -y -qq build-essential git curl ca-certificates >>"$LOG" 2>&1

# Fast path: the image already ships the exact interpreter the head runs.
SYSTEM_PY="$(command -v "python${PYTHON_MINOR}" 2>/dev/null || true)"
SYSTEM_VERSION=""
if [[ -n "$SYSTEM_PY" ]]; then
    SYSTEM_VERSION="$("$SYSTEM_PY" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
fi

if [[ "$SYSTEM_VERSION" == "$PYTHON_VERSION" ]]; then
    log "system python${PYTHON_MINOR} is already ${PYTHON_VERSION}"
    apt_get install -y -qq "python${PYTHON_MINOR}-venv" "python${PYTHON_MINOR}-dev" >>"$LOG" 2>&1
    [[ -x "$ENV_DIR/bin/python" ]] || "$SYSTEM_PY" -m venv "$ENV_DIR"
else
    log "system python is ${SYSTEM_VERSION:-absent}; fetching exactly ${PYTHON_VERSION} with uv"
    export UV_INSTALL_DIR="$HOME/.local/bin"
    UV="$UV_INSTALL_DIR/uv"
    if [[ ! -x "$UV" ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh >>"$LOG" 2>&1 ||
            die "could not install uv; the worker needs outbound https to astral.sh"
    fi
    "$UV" python install "$PYTHON_VERSION" >>"$LOG" 2>&1 ||
        die "uv has no CPython ${PYTHON_VERSION}; pick a head interpreter that python-build-standalone publishes"
    rm -rf "$ENV_DIR"
    "$UV" venv --python "$PYTHON_VERSION" "$ENV_DIR" >>"$LOG" 2>&1
fi

ACTUAL_VERSION="$("$ENV_DIR/bin/python" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
[[ "$ACTUAL_VERSION" == "$PYTHON_VERSION" ]] ||
    die "virtualenv runs Python $ACTUAL_VERSION but the head runs $PYTHON_VERSION; Ray compares the full version and will refuse to join. Remove $ENV_DIR and re-run."

log "installing chialoops==${CHIA_VERSION} (it pins the matching Ray release)"
# A uv-created venv has no pip, so bootstrap one before using it.
"$ENV_DIR/bin/python" -m ensurepip --upgrade >>"$LOG" 2>&1 || true
"$ENV_DIR/bin/python" -m pip install --quiet --upgrade pip setuptools wheel >>"$LOG" 2>&1
"$ENV_DIR/bin/python" -m pip install --quiet "chialoops==${CHIA_VERSION}" >>"$LOG" 2>&1

if [[ "$WITH_VERILATOR" == "1" ]]; then
    log "installing Verilator"
    apt_get install -y -qq verilator >>"$LOG" 2>&1
fi

if [[ "$WITH_CHISEL" == "1" ]]; then
    log "installing JDK and sbt"
    apt_get install -y -qq openjdk-17-jdk-headless >>"$LOG" 2>&1
    if ! command -v sbt >/dev/null; then
        curl -fsSL https://scala.jbp.io/sbt/sbt.gpg |
            sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/sbt.gpg
        echo "deb [signed-by=/usr/share/keyrings/sbt.gpg] https://repo.scala-sbt.org/scalasbt/debian all main" |
            sudo tee /etc/apt/sources.list.d/sbt.list >/dev/null
        apt_get update -qq
        apt_get install -y -qq sbt >>"$LOG" 2>&1
    fi
fi

RAY_VERSION="$("$ENV_DIR/bin/python" -c 'import ray; print(ray.__version__)')"
CHIA_OK="$("$ENV_DIR/bin/python" -c 'import chia; print("ok")' 2>&1 | tail -1)"
log "ready: python ${ACTUAL_VERSION}, ray ${RAY_VERSION}, chia import ${CHIA_OK}"
[[ "$CHIA_OK" == "ok" ]] || die "chia is installed but does not import: $CHIA_OK"

printf '%s' "$STAMP" > "$MARKER"
log "bootstrap complete"
