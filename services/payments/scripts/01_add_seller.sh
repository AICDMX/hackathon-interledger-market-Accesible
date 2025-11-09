#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:4001}"

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <sellerId> <walletAddressUrl> <keyId> <privateKeyPath>"
  exit 1
fi

sellerId="$1"
wallet="$2"
keyId="$3"
keyPath="$4"

curl -sS -X POST "${BASE_URL}/sellers" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${sellerId}\",
    \"walletAddressUrl\": \"${wallet}\",
    \"keyId\": \"${keyId}\",
    \"privateKeyPath\": \"${keyPath}\"
  }" | jq .


