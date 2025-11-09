#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:4001}"

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <offerId> <sellerId> <buyerWalletAddressUrl> <amount>"
  exit 1
fi

offerId="$1"
sellerId="$2"
buyer="$3"
amount="$4"

resp="$(curl -sS -X POST "${BASE_URL}/offers/${offerId}/quotes/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"sellerId\": \"${sellerId}\",
    \"buyerWalletAddressUrl\": \"${buyer}\",
    \"amount\": \"${amount}\"
  }")"

echo "${resp}" | jq .

redirectUrl="$(echo "${resp}" | jq -r '.redirectUrl')"
echo ""
echo "Open this URL to continue (interactive grant):"
echo "${redirectUrl}"
echo ""


