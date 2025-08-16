#!/usr/bin/env bash
# Resets the local demo: stops receiver, removes stray containers, clears ./out files.
# Optional knobs (env vars):
#   IMAGE=meiro-connector           # which image's containers to clean
#   RECEIVER_NAME=ingest-receiver   # receiver container name
#   OUT_DIR=$PWD/out                # where results are written
#   CLEAR_OUT=1                     # 1=delete out/ingested.jsonl & out/customers.csv
#   REMOVE_CONTAINERS=1             # 1=remove containers created from IMAGE
#   REMOVE_IMAGE=0                  # 1=also remove the IMAGE itself (careful)
#   PRUNE=0                         # 1= docker system prune -af (aggressive)


set -euo pipefail

IMAGE="${IMAGE:-meiro-connector}"
RECEIVER_NAME="${RECEIVER_NAME:-ingest-receiver}"
OUT_DIR="${OUT_DIR:-$PWD/out}"
CLEAR_OUT="${CLEAR_OUT:-1}"
REMOVE_CONTAINERS="${REMOVE_CONTAINERS:-1}"
REMOVE_IMAGE="${REMOVE_IMAGE:-0}"
PRUNE="${PRUNE:-0}"

# --- sanity checks ---
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker not found in PATH. Install/launch Docker Desktop and retry."
  exit 1
fi

echo "🧹 Cleaning environment"
echo "  IMAGE=${IMAGE}"
echo "  RECEIVER_NAME=${RECEIVER_NAME}"
echo "  OUT_DIR=${OUT_DIR}"
echo "  CLEAR_OUT=${CLEAR_OUT}  REMOVE_CONTAINERS=${REMOVE_CONTAINERS}  REMOVE_IMAGE=${REMOVE_IMAGE}  PRUNE=${PRUNE}"
echo

# --- stop/remove receiver if running ---
if docker ps -a --format '{{.Names}}' | grep -q "^${RECEIVER_NAME}$"; then
  echo "▶ Stopping receiver '${RECEIVER_NAME}'"
  docker rm -f "${RECEIVER_NAME}" >/dev/null 2>&1 || true
else
  echo "✓ Receiver '${RECEIVER_NAME}' not running"
fi

# --- remove containers created from IMAGE ---
if [[ "${REMOVE_CONTAINERS}" == "1" ]]; then
  CONTAINERS=$(docker ps -a --filter "ancestor=${IMAGE}" -q || true)
  if [[ -n "${CONTAINERS}" ]]; then
    echo "▶ Removing containers created from image '${IMAGE}'"
    echo "${CONTAINERS}" | xargs -r docker rm -f >/dev/null
  else
    echo "✓ No containers found for image '${IMAGE}'"
  fi
else
  echo "↷ Skipping container removal (REMOVE_CONTAINERS=0)"
fi

# --- optionally remove the image itself ---
if [[ "${REMOVE_IMAGE}" == "1" ]]; then
  IDS=$(docker images "${IMAGE}" -q || true)
  if [[ -n "${IDS}" ]]; then
    echo "▶ Removing image '${IMAGE}'"
    echo "${IDS}" | xargs -r docker rmi -f >/dev/null
  else
    echo "✓ Image '${IMAGE}' not present (nothing to remove)"
  fi
else
  echo "↷ Skipping image removal (REMOVE_IMAGE=0)"
fi

# --- clear output files ---
if [[ "${CLEAR_OUT}" == "1" ]]; then
  mkdir -p "${OUT_DIR}"
  echo "▶ Clearing output files in ${OUT_DIR}"
  rm -f "${OUT_DIR}/ingested.jsonl" "${OUT_DIR}/customers.csv"
  # rm -f "${OUT_DIR}"/*   # uncomment to wipe all files in OUT_DIR
else
  echo "↷ Skipping output cleanup (CLEAR_OUT=0)"
fi

# --- optional docker prune (aggressive) ---
if [[ "${PRUNE}" == "1" ]]; then
  echo "⚠ Running 'docker system prune -af' (this removes unused images/containers/networks)"
  docker system prune -af >/dev/null
else
  echo "↷ Skipping docker prune (PRUNE=0)"
fi

echo
echo "✅ Cleanup complete"



# How to use
# # Make it executable once
# chmod +x scripts/clean_up.sh

# # Typical reset (keeps the image, clears outputs)
# ./scripts/clean_up.sh

# # Remove the image too
# REMOVE_IMAGE=1 ./scripts/clean_up.sh

# # Be extra aggressive (prunes all unused Docker artifacts)
# PRUNE=1 ./scripts/clean_up.sh
