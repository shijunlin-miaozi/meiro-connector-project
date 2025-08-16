#!/usr/bin/env bash

# Runs Google Sheets → Google Sheets in Docker (service-account auth). 
# Requires credentials.json and .env.

set -euo pipefail

IMAGE="${IMAGE:-meiro-connector}"         # Docker image tag to run

# Fail fast if required files are missing
[[ -f "./credentials.json" ]] || { echo "❌ credentials.json not found in repo root."; exit 1; }
[[ -f "./.env" ]] || { echo "❌ .env not found. Copy .env.example and fill in your values."; exit 1; }

# Validate that both source and destination identifiers exist in .env
need_vars=(SHEET_URL_OR_ID UPLOAD_SHEET_URL_OR_ID)
for v in "${need_vars[@]}"; do
  if ! grep -qE "^${v}=" .env; then
    echo "❌ ${v} is missing in .env"; exit 1
  fi
done

# - Use .env for tabs/URLs
# - Force CONNECTOR=sheets so this script is deterministic even if .env differs
# - Mount credentials.json read-only at /app/credentials.json (path expected by the app)
echo "▶ Running Sheets → Sheets pipeline (forcing CONNECTOR=sheets)"
docker run --rm --env-file .env \
  -e CONNECTOR=sheets \
  -v "$PWD/credentials.json:/app/credentials.json:ro" \
  "${IMAGE}" python main.py --uploader gsheets
