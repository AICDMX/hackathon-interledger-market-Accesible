#!/bin/bash
# Test script for payment confirmation endpoints

set -e

echo "=========================================="
echo "Payment Confirmation Test Suite"
echo "=========================================="
echo ""

# Configuration
DJANGO_URL=${DJANGO_URL:-"http://localhost:8000"}
PAYMENTS_URL=${PAYMENTS_URL:-"http://localhost:4001"}

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if Django webhook endpoint exists
echo "Test 1: Django webhook endpoint"
echo "--------------------------------"
response=$(curl -s -w "\n%{http_code}" -X POST "$DJANGO_URL/api/webhooks/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment.completed",
    "pendingId": "test-webhook-001",
    "offerId": "999999",
    "status": "paid",
    "outgoingPaymentId": "https://test.example/payment/001",
    "timestamp": "2025-01-09T12:00:00Z"
  }')

http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 404 ] || [ "$http_code" -eq 200 ]; then
  echo -e "${GREEN}✓ Endpoint is reachable${NC}"
  echo "  Response code: $http_code"
  echo "  Response body: $body"
  if [ "$http_code" -eq 404 ]; then
    echo -e "  ${YELLOW}Note: Job #999999 not found (expected for test)${NC}"
  fi
else
  echo -e "${RED}✗ Unexpected response${NC}"
  echo "  HTTP Code: $http_code"
  echo "  Body: $body"
fi
echo ""

# Test 2: Check Django finish redirect endpoint
echo "Test 2: Django finish redirect endpoint"
echo "----------------------------------------"
response=$(curl -s -w "\n%{http_code}" -L "$DJANGO_URL/payments/finish?pendingId=test-001&interact_ref=abc123&hash=xyz789")

http_code=$(echo "$response" | tail -n 1)

if [ "$http_code" -eq 200 ]; then
  echo -e "${GREEN}✓ Endpoint is reachable${NC}"
  echo "  Response code: $http_code"
else
  echo -e "${RED}✗ Endpoint returned error${NC}"
  echo "  HTTP Code: $http_code"
fi
echo ""

# Test 3: Check if payments service is running
echo "Test 3: Payments service health"
echo "--------------------------------"
response=$(curl -s -w "\n%{http_code}" "$PAYMENTS_URL/sellers")

http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 200 ]; then
  echo -e "${GREEN}✓ Payments service is running${NC}"
  echo "  Response code: $http_code"
  # Try to parse JSON
  seller_count=$(echo "$body" | grep -o '"sellers"' | wc -l)
  if [ "$seller_count" -gt 0 ]; then
    echo "  Sellers endpoint responding correctly"
  fi
else
  echo -e "${RED}✗ Payments service not reachable${NC}"
  echo "  HTTP Code: $http_code"
fi
echo ""

# Test 4: Check environment variables
echo "Test 4: Environment configuration"
echo "----------------------------------"

echo "Checking services/payments/.env file..."
if [ -f "services/payments/.env" ]; then
  echo -e "${GREEN}✓ .env file exists${NC}"
  
  if grep -q "^DJANGO_BASE_URL=" services/payments/.env; then
    django_base=$(grep "^DJANGO_BASE_URL=" services/payments/.env | cut -d'=' -f2-)
    echo "  DJANGO_BASE_URL: $django_base"
  else
    echo -e "  ${YELLOW}⚠ DJANGO_BASE_URL not set${NC}"
  fi
  
  if grep -q "^BASE_URL=" services/payments/.env; then
    base_url=$(grep "^BASE_URL=" services/payments/.env | cut -d'=' -f2-)
    echo "  BASE_URL: $base_url"
  else
    echo -e "  ${YELLOW}⚠ BASE_URL not set${NC}"
  fi
else
  echo -e "${RED}✗ services/payments/.env not found${NC}"
  echo "  Run: cp services/payments/.env.example services/payments/.env"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Endpoints configured:"
echo "  Django:   $DJANGO_URL"
echo "  Payments: $PAYMENTS_URL"
echo ""
echo "Next steps:"
echo "  1. Ensure both services are running"
echo "  2. Set DJANGO_BASE_URL in services/payments/.env"
echo "  3. Test with a real payment flow"
echo ""
echo "For manual testing:"
echo "  curl -X POST $DJANGO_URL/api/webhooks/payments \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"type\":\"payment.completed\",\"pendingId\":\"test\",\"offerId\":\"1\",\"status\":\"paid\",\"timestamp\":\"2025-01-09T00:00:00Z\"}'"
echo ""
