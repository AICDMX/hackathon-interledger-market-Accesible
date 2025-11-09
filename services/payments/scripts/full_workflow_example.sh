#!/usr/bin/env bash
set -euo pipefail

# Full workflow example demonstrating the complete Interledger payment flow
# This script shows all steps from adding a seller to completing a payment

BASE_URL="${BASE_URL:-http://localhost:4001}"

echo "=========================================="
echo "Interledger Payment Workflow Example"
echo "=========================================="
echo ""

# Step 1: List existing sellers
echo "Step 1: Listing existing sellers..."
curl -sS "${BASE_URL}/sellers" | jq .
echo ""

# Step 2: Add a new seller (using project seller info)
echo "Step 2: Adding seller-aicdmx..."

SELLER_ID="seller-aicdmx"
WALLET_ADDRESS="https://ilp.interledger-test.dev/aicdmx"
KEY_ID="d405beb8-f84a-4449-b989-93d0c7e38f02"
PRIVATE_KEY_PATH="private.key"

curl -sS -X POST "${BASE_URL}/sellers" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${SELLER_ID}\",
    \"walletAddressUrl\": \"${WALLET_ADDRESS}\",
    \"keyId\": \"${KEY_ID}\",
    \"privateKeyPath\": \"${PRIVATE_KEY_PATH}\"
  }" | jq .
echo ""

# Step 3: Start a quote (create incoming payment, quote, and grant request)
echo "Step 3: Starting a quote for an offer..."
echo "NOTE: Replace OFFER_ID and BUYER_WALLET with actual values"
echo ""

# Example quote data - uncomment and modify to use:
OFFER_ID="offer-123"
SELLER_ID="seller-aicdmx"
BUYER_WALLET="https://ilp.interledger-test.dev/buyer"
AMOUNT="100"

echo "Uncomment the following lines to execute:"
echo "# RESP=\$(curl -sS -X POST \"\${BASE_URL}/offers/\${OFFER_ID}/quotes/start\" \\"
echo "#   -H \"Content-Type: application/json\" \\"
echo "#   -d \"{"
echo "#     \\\"sellerId\\\": \\\"\${SELLER_ID}\\\","
echo "#     \\\"buyerWalletAddressUrl\\\": \\\"\${BUYER_WALLET}\\\","
echo "#     \\\"amount\\\": \\\"\${AMOUNT}\\\""
echo "#   }\")"
echo ""

# RESP=$(curl -sS -X POST "${BASE_URL}/offers/${OFFER_ID}/quotes/start" \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"sellerId\": \"${SELLER_ID}\",
#     \"buyerWalletAddressUrl\": \"${BUYER_WALLET}\",
#     \"amount\": \"${AMOUNT}\"
#   }")

# echo "${RESP}" | jq .
# echo ""

# PENDING_ID=$(echo "${RESP}" | jq -r '.pendingId')
# REDIRECT_URL=$(echo "${RESP}" | jq -r '.redirectUrl')

# echo "Pending ID: ${PENDING_ID}"
# echo "Redirect URL: ${REDIRECT_URL}"
# echo ""
# echo "Next step: Open the redirect URL in a browser to authorize the payment"
# echo "The wallet will redirect back to /payments/finish with interact_ref and hash"
# echo ""

# Step 4: Finish payment (normally called by wallet redirect)
echo "Step 4: Finishing payment..."
echo "NOTE: This is normally called automatically by the wallet's redirect"
echo "You'll need the pendingId, interact_ref, and hash from the wallet callback"
echo ""

# Example finish data - uncomment and modify to use:
# PENDING_ID="01HZZ..."
# INTERACT_REF="abc123..."
# HASH="xyz789..."

# curl -sS "${BASE_URL}/payments/finish?pendingId=${PENDING_ID}&interact_ref=${INTERACT_REF}&hash=${HASH}" | jq .
# echo ""

echo "=========================================="
echo "Workflow Complete"
echo "=========================================="
echo ""
echo "For testing individual steps, use:"
echo "  - scripts/00_list_sellers.sh"
echo "  - scripts/01_add_seller.sh <sellerId> <walletUrl> <keyId> <keyPath>"
echo "  - scripts/02_start_quote.sh <offerId> <sellerId> <buyerWallet> <amount>"
echo "  - scripts/03_finish_payment.sh <pendingId> <interact_ref> <hash>"
echo ""

