#!/usr/bin/env bash

# Preflight checks for the connector demo:
# - Docker CLI + daemon
# - Image presence
# - .env / credentials.json availability
# - Host out/ writeability
# - Receiver port availability (default 8010)

set -euo pipefail

IMAGE="${IMAGE:-meiro-connector}"
PORT="${PORT:-8010}"
OUT_DIR="${OUT_DIR:-$PWD/out}"

# --- tiny helpers -----------------------------------------------------------
ok()   { echo -e "✅  $*"; }
warn() { echo -e "⚠️  $*" >&2; }
err()  { echo -e "❌  $*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

port_in_use() {
  # Prefer lsof if available
  if have lsof; then
    lsof -iTCP:"$PORT" -sTCP:LISTEN -n -P >/dev/null 2>&1
    return $?
  fi
  # Fallbacks: bash /dev/tcp or nc
  if [[ -e /dev/tcp/127.0.0.1/$PORT ]]; then
    # shellcheck disable=SC2086
    : >/dev/tcp/127.0.0.1/$PORT && return 0 || return 1
  fi
  if have nc; then
    nc -z 127.0.0.1 "$PORT" >/dev/null 2>&1 && return 0 || return 1
  fi
  # If we can't check, assume free
  return 1
}

# --- checks -----------------------------------------------------------------
# Docker CLI
have docker || err "Docker CLI not found. Install Docker Desktop or CLI."

# Docker daemon
docker info >/dev/null 2>&1 || err "Cannot connect to Docker daemon. Start Docker Desktop (or 'systemctl start docker' on Linux)."

ok "Docker is available"

# Image present?
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  ok "Image '$IMAGE' is present"
else
  warn "Image '$IMAGE' not found. Build it with:  docker build -t $IMAGE ."
fi

# .env file (used by scripts and docker runs)
if [[ -f ".env" ]]; then
  ok ".env found"
else
  warn ".env not found (RandomUser demos still work; Sheets demos will need env vars)."
fi

# credentials.json (needed for Sheets read/write)
if [[ -f "credentials.json" ]]; then
  ok "credentials.json found (Sheets integrations enabled)"
else
  warn "credentials.json not found (Sheets read/write will be skipped)."
fi

# out/ writeability (for HTTP receiver bind-mount)
mkdir -p "$OUT_DIR" || err "Cannot create OUT_DIR at '$OUT_DIR'."
if ( echo "probe" > "$OUT_DIR/.write_test" ) 2>/dev/null; then
  rm -f "$OUT_DIR/.write_test"
  ok "OUT_DIR is writable ($OUT_DIR)"
else
  warn "OUT_DIR not writable: $OUT_DIR (HTTP demo will not be able to write here)."
fi

# Receiver port availability
if port_in_use; then
  warn "Host port $PORT is already in use. Either stop the process or run with: PORT=<free_port> ./scripts/run_randomuser_http.sh"
else
  ok "Host port $PORT is free for the receiver"
fi

echo
ok "Healthcheck complete"
echo "• RandomUser→HTTP:  ./scripts/run_randomuser_http.sh"
echo "• Sheets→Sheets:    ./scripts/run_sheets_to_sheets.sh"
echo "• Unit tests:       ./scripts/run_unit_tests.sh"
echo "• Integration:      ./scripts/run_integration_tests.sh"
