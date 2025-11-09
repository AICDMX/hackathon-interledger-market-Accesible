#!/usr/bin/env bash
set -euo pipefail

# Complete buyer workflow for aicdmx
# Demonstrates purchasing offers from various sellers in the marketplace

BASE_URL="${BASE_URL:-http://localhost:4001}"

# aicdmx buyer credentials
BUYER_WALLET="https://ilp.interledger-test.dev/aicdmx"
BUYER_KEY_ID="0227b90b-ee4d-4184-b8a9-6befcc9fa812"

echo "=============================================="
echo "Buyer Workflow: aicdmx"
echo "=============================================="
echo ""
echo "Buyer Wallet: ${BUYER_WALLET}"
echo ""

# Step 1: List available sellers
echo "Step 1: Viewing available sellers..."
echo "----------------------------------------------"
curl -sS "${BASE_URL}/sellers" | jq .
echo ""

# Step 2: Example - Purchase from seller-mvr5656
echo "Step 2: Example Purchase Flow"
echo "----------------------------------------------"
echo ""
echo "To purchase an offer, use:"
echo ""
echo "  ./buyer_aicdmx_payment.sh <offerId> <sellerId> <amount>"
echo ""
echo "Example purchases:"
echo ""
echo "  # Purchase offer-web-dev from seller-mvr5656 for 50 USD"
echo "  ./buyer_aicdmx_payment.sh offer-web-dev seller-mvr5656 50"
echo ""
echo "  # Purchase offer-design from seller-mvr5656 for 100 USD"
echo "  ./buyer_aicdmx_payment.sh offer-design seller-mvr5656 100"
echo ""

# Step 3: Show how to check payment status (if implemented)
echo "Step 3: After Payment Authorization"
echo "----------------------------------------------"
echo ""
echo "After clicking the redirect URL and authorizing in your wallet:"
echo "1. The Interledger wallet will process your payment"
echo "2. You'll be redirected back to the marketplace"
echo "3. The payment will be completed automatically"
echo ""

echo "=============================================="
echo "Buyer Information"
echo "=============================================="
echo ""
echo "Wallet Address: ${BUYER_WALLET}"
echo "Key ID:         ${BUYER_KEY_ID}"
echo ""
echo "To fund your wallet, visit:"
echo "https://rafiki.money"
echo ""
echo "To view your wallet details, visit:"
echo "https://ilp.interledger-test.dev/aicdmx"
echo ""
