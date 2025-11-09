#!/usr/bin/env bash
set -euo pipefail

# Script for aicdmx acting as BUYER
# This demonstrates the buyer's perspective in the payment flow

BASE_URL="${BASE_URL:-http://localhost:4001}"

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <offerId> <sellerId> <amount>"
  echo ""
  echo "Example:"
  echo "  $0 offer-123 seller-mvr5656 100"
  echo ""
  echo "This will initiate a payment from aicdmx (buyer) to the specified seller"
  exit 1
fi

OFFER_ID="$1"
SELLER_ID="$2"
AMOUNT="$3"

# aicdmx buyer wallet details
BUYER_WALLET="https://ilp.interledger-test.dev/aicdmx"

echo "==========================================="
echo "Initiating Payment as Buyer (aicdmx)"
echo "==========================================="
echo ""
echo "Offer ID:      ${OFFER_ID}"
echo "Seller ID:     ${SELLER_ID}"
echo "Buyer Wallet:  ${BUYER_WALLET}"
echo "Amount:        ${AMOUNT}"
echo ""

echo "Starting quote..."
RESP=$(curl -sS -X POST "${BASE_URL}/offers/${OFFER_ID}/quotes/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"sellerId\": \"${SELLER_ID}\",
    \"buyerWalletAddressUrl\": \"${BUYER_WALLET}\",
    \"amount\": \"${AMOUNT}\"
  }")

echo "${RESP}" | jq .
echo ""

PENDING_ID=$(echo "${RESP}" | jq -r '.pendingId')
REDIRECT_URL=$(echo "${RESP}" | jq -r '.redirectUrl')

echo "==========================================="
echo "Payment Initiated Successfully"
echo "==========================================="
echo ""
echo "Pending ID:   ${PENDING_ID}"
echo ""
echo "NEXT STEP:"
echo "Open this URL in your browser to authorize the payment:"
echo ""
echo "${REDIRECT_URL}"
echo ""
echo "After authorization, the wallet will redirect back automatically"
echo "to complete the payment."
echo ""
