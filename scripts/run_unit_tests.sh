#!/usr/bin/env bash

# Runs unit tests only inside the built image.

set -euo pipefail

IMAGE="${IMAGE:-meiro-connector}"

echo "▶ Running unit tests"
docker run --rm "${IMAGE}" pytest -v tests/unit -ra
