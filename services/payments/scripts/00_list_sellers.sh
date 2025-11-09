#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:4001}"

echo "Fetching all sellers..."
curl -sS "${BASE_URL}/sellers" | jq .

