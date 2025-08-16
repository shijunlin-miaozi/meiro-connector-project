#!/usr/bin/env bash

# Runs integration tests inside Docker.
# - HTTP test: no secrets needed.
# - RandomUser: opt-in.
# - Google Sheets read/write: needs credentials.json + .env values.

set -euo pipefail

IMAGE="${IMAGE:-meiro-connector}"

PYTEST_FLAGS="${PYTEST_FLAGS:- -q --no-header}"
# -vv: very verbose test names
# -ra: show skip/xpass reasons summary
# -s : show print()/stdout
# --log-cli-level=INFO : stream logging from your code into pytest output

# Always safe to run: HTTP ingestion (uses TestClient)
echo "▶ Integration: HTTP ingestion"
docker run --rm "${IMAGE}" pytest $PYTEST_FLAGS tests/integration/test_http_upload.py

# Optional: RandomUser network fetch (enable with RUN_RANDOMUSER_INTEGRATION=1 in .env)
if grep -qE '^RUN_RANDOMUSER_INTEGRATION=1' .env; then
  echo "▶ Integration: RandomUser fetch (network)"
  docker run --rm --env-file .env \
      -e RUN_RANDOMUSER_INTEGRATION=1 \
    "${IMAGE}" pytest $PYTEST_FLAGS tests/integration/test_random_user_fetch.py
else
  echo "⏭ Skipping RandomUser fetch (RUN_RANDOMUSER_INTEGRATION=1 not set in .env)"
fi

# Google Sheets read
if [[ -f "./credentials.json" && -f "./.env" ]]; then
  if grep -qE '^SHEET_URL_OR_ID=' .env; then
    echo "▶ Integration: Google Sheets READ"
    docker run --rm --env-file .env \
      -e RUN_SHEETS_INTEGRATION=1 \
      -v "$PWD/credentials.json:/app/credentials.json:ro" \
      "${IMAGE}" pytest $PYTEST_FLAGS tests/integration/test_gsheets_read.py
  else
    echo "⏭ Skipping Sheets READ (SHEET_URL_OR_ID not set in .env)"
  fi

  # Google Sheets write
  if grep -qE '^UPLOAD_SHEET_URL_OR_ID=' .env; then
    echo "▶ Integration: Google Sheets WRITE"
    docker run --rm --env-file .env \
      -e RUN_SHEETS_WRITE=1 \
      -v "$PWD/credentials.json:/app/credentials.json:ro" \
      "${IMAGE}" pytest $PYTEST_FLAGS tests/integration/test_gsheets_write.py
  else
    echo "⏭ Skipping Sheets WRITE (UPLOAD_SHEET_URL_OR_ID not set in .env)"
  fi
else
  echo "⏭ Skipping Sheets integrations (missing credentials.json or .env)"
fi
