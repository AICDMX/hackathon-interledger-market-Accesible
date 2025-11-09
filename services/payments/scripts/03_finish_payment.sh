#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:4001}"

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <pendingId> <interact_ref> <hash>"
  exit 1
fi

pendingId="$1"
interactRef="$2"
hashVal="$3"

curl -sS "${BASE_URL}/payments/finish?pendingId=${pendingId}&interact_ref=${interactRef}&hash=${hashVal}" | jq .


