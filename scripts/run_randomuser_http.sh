#!/usr/bin/env bash

# Starts the receiver in Docker on a non-conflicting port.
# Runs the sender (RandomUser → HTTP). 
# Writes to ./out/ingested.jsonl on your host.

set -euo pipefail

# --- Config (override via env) ----------------------------------------------
IMAGE="${IMAGE:-meiro-connector}"       # Docker image tag to use
PORT="${PORT:-8010}"                    # Host port exposed -> container :8000
RECEIVER_NAME="${RECEIVER_NAME:-ingest-receiver}"  # Receiver container name
OUT_DIR="${OUT_DIR:-$PWD/out}"          # Host folder to store ingested.jsonl
KEEP_RECEIVER="${KEEP_RECEIVER:-1}"     # 1=keep receiver running after demo

mkdir -p "$OUT_DIR"                     # Ensure output folder exists

# --- Start (or reuse) the receiver container --------------------------------
if docker ps --format '{{.Names}}' | grep -q "^${RECEIVER_NAME}$"; then
  echo "▶ Receiver already running (container: ${RECEIVER_NAME})"
else
  # Remove a stopped container with same name (if any)
  if docker ps -a --format '{{.Names}}' | grep -q "^${RECEIVER_NAME}$"; then
    docker rm -f "${RECEIVER_NAME}" >/dev/null 2>&1 || true
  fi

  echo "▶ Starting receiver on host port ${PORT} → writes to ${OUT_DIR}/ingested.jsonl"
  docker run -d --rm --name "${RECEIVER_NAME}" \
    -p "${PORT}:8000" \
    -v "${OUT_DIR}:/data" \
    -e INGEST_OUT=/data/ingested.jsonl \
    "${IMAGE}" \
    uvicorn common.ingestion_api:app --host 0.0.0.0 --port 8000

  sleep 1                                # Tiny grace period to bind the port
fi

# --- Run the sender (RandomUser → HTTP) -------------------------------------
echo "▶ Running sender (RandomUser → HTTP) → POST to http://host.docker.internal:${PORT}/ingest"
docker run --rm --env-file .env \
  -e CONNECTOR=randomuser \
  -e UPLOAD_URL="http://host.docker.internal:${PORT}/ingest" \
  "${IMAGE}" python main.py --uploader http

# --- Show a quick result preview --------------------------------------------
# echo "▶ Result preview (host file): ${OUT_DIR}/ingested.jsonl"
# wc -l "${OUT_DIR}/ingested.jsonl" || true
# tail -n 3 "${OUT_DIR}/ingested.jsonl" || true

# --- Stop receiver (optional) -----------------------------------------------
if [[ "${KEEP_RECEIVER}" != "1" ]]; then
  echo "▶ Stopping receiver"
  docker stop "${RECEIVER_NAME}" >/dev/null
else
  echo "ℹ Receiver left running (KEEP_RECEIVER=1)."
  echo "  - Re-run this script to append more rows."
  echo "  - Stop it later with:  docker stop ${RECEIVER_NAME}"
fi
