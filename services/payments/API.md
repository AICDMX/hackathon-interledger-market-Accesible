# Payments Service API Documentation

## Overview

The Payments Service is a Node.js/TypeScript microservice that integrates Interledger Open Payments with the Django marketplace application. It handles payment quotes, interactive grant flows, and payment completion notifications.

## Base URL

- **Development**: `http://localhost:4001`
- **Docker**: `http://payments:3000`

## Configuration

See `.env.example` for all configuration options:

```bash
PORT=3000
BASE_URL=http://localhost:4001
DJANGO_BASE_URL=http://web:8000
SELLER_ID=default-seller
SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/mvr5656
SELLER_KEY_ID=<your-key-id>
SELLER_PRIVATE_KEY_PATH=./privates/mvr5656.key
```

## Endpoints

### Health Check

**GET** `/health`

Check service health and availability.

**Response:**
```json
{
  "status": "ok",
  "service": "payments",
  "time": "2025-11-09T08:36:51.000Z"
}
```

---

### Seller Management

#### List Sellers

**GET** `/sellers`

Retrieve all registered sellers.

**Response:**
```json
{
  "sellers": [
    {
      "id": "default-seller",
      "walletAddressUrl": "https://ilp.interledger-test.dev/mvr5656",
      "keyId": "fe775339-6ebc-4eb8-a4b4-0811acba3b62",
      "privateKeyPath": "./privates/mvr5656.key"
    }
  ]
}
```

#### Register/Update Seller

**POST** `/sellers`

Register a new seller or update an existing one.

**Request Body:**
```json
{
  "id": "default-seller",
  "walletAddressUrl": "https://ilp.interledger-test.dev/mvr5656",
  "keyId": "fe775339-6ebc-4eb8-a4b4-0811acba3b62",
  "privateKeyPath": "./privates/mvr5656.key"
}
```

**Response:**
```json
{
  "ok": true,
  "id": "default-seller"
}
```

---

### Payment Flow

#### Start Quote

**POST** `/offers/:offerId/quotes/start`

Initiate a payment quote for a buyer. This creates an incoming payment, quote, and interactive grant.

**Path Parameters:**
- `offerId` - The job/offer ID

**Request Body:**
```json
{
  "sellerId": "default-seller",
  "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
  "amount": "100"
}
```

**Response:**
```json
{
  "pendingId": "01JCEXAMPLE123456",
  "redirectUrl": "https://ilp.interledger-test.dev/interact/..."
}
```

**Usage:**
1. Django calls this endpoint when a buyer wants to fund a job
2. Redirect the user to `redirectUrl` to approve the payment
3. After approval, user is redirected to the finish URL

#### Finish Payment

**GET** `/payments/finish`

Complete the payment after buyer approval. Called by wallet redirect.

**Query Parameters:**
- `pendingId` - The pending payment ID
- `interact_ref` - Interaction reference from wallet
- `hash` - Security hash from wallet

**Response:**
```json
{
  "ok": true,
  "outgoingPayment": {
    "id": "https://ilp.interledger-test.dev/outgoing-payments/...",
    "walletAddress": "https://ilp.interledger-test.dev/edutest",
    "receiveAmount": { "value": "100", "assetCode": "USD", "assetScale": 2 }
  }
}
```

**Webhook Notification:**
Upon success, Django is automatically notified via webhook at `/api/webhooks/payments`:
```json
{
  "type": "payment.completed",
  "pendingId": "01JCEXAMPLE123456",
  "offerId": "123",
  "status": "paid",
  "outgoingPaymentId": "https://...",
  "timestamp": "2025-11-09T08:36:51.000Z"
}
```

---

### Payment Status & Queries

#### Get Payment Status

**GET** `/payments/:pendingId/status`

Query the status of a specific payment.

**Path Parameters:**
- `pendingId` - The pending payment ID

**Response:**
```json
{
  "pendingId": "01JCEXAMPLE123456",
  "offerId": "123",
  "status": "paid",
  "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
  "incomingPaymentId": "https://ilp.interledger-test.dev/incoming-payments/...",
  "outgoingPaymentId": "https://ilp.interledger-test.dev/outgoing-payments/...",
  "quoteId": "https://ilp.interledger-test.dev/quotes/..."
}
```

**Status values:**
- `pending` - Payment initiated, awaiting buyer approval
- `paid` - Payment completed successfully
- `failed` - Payment failed

#### List All Pending Payments

**GET** `/payments/pending`

List all payments in the system.

**Response:**
```json
{
  "payments": [
    {
      "pendingId": "01JCEXAMPLE123456",
      "offerId": "123",
      "status": "paid",
      "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
      "incomingPaymentId": "https://...",
      "outgoingPaymentId": "https://..."
    }
  ]
}
```

#### Get Offer Payments

**GET** `/offers/:offerId/payments`

Get all payments for a specific offer/job.

**Path Parameters:**
- `offerId` - The job/offer ID

**Response:**
```json
{
  "offerId": "123",
  "payments": [
    {
      "pendingId": "01JCEXAMPLE123456",
      "status": "paid",
      "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
      "incomingPaymentId": "https://...",
      "outgoingPaymentId": "https://...",
      "quoteId": "https://..."
    }
  ]
}
```

---

### Django Integration Endpoints

#### Create Incoming Payment

**POST** `/api/payments/incoming`

Create an incoming payment for escrow/job funding (used by Django for pre-approved payments).

**Request Body:**
```json
{
  "amount": "100",
  "description": "Job funding for developer position",
  "sellerId": "default-seller"
}
```

**Response:**
```json
{
  "success": true,
  "paymentId": "https://ilp.interledger-test.dev/incoming-payments/...",
  "payment_id": "https://...",
  "data": {
    "incomingPaymentId": "https://...",
    "walletAddress": "https://ilp.interledger-test.dev/mvr5656",
    "amount": "100",
    "assetCode": "USD",
    "assetScale": 2
  }
}
```

---

## Error Handling

All endpoints return errors in the following format:

```json
{
  "error": "Error message",
  "details": { /* optional additional context */ }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (missing or invalid parameters)
- `404` - Not Found
- `500` - Internal Server Error

In development mode, errors include stack traces.

---

## Django Integration Guide

### 1. Start Payment Flow

```python
from jobs.payments_utils import start_quote

result = start_quote(
    offer_id=job.id,
    seller_id='default-seller',
    buyer_wallet_address_url=user.wallet_address,
    amount=job.budget
)

if result['success']:
    redirect_url = result['redirect_url']
    # Redirect user to approve payment
```

### 2. Handle Webhook Notifications

Create a webhook endpoint in Django to receive payment completion notifications:

```python
# In your Django views
@csrf_exempt
@require_POST
def payment_webhook(request):
    data = json.loads(request.body)
    
    if data['type'] == 'payment.completed':
        pending_id = data['pendingId']
        offer_id = data['offerId']
        # Update job status, mark as funded, etc.
    
    return JsonResponse({'ok': True})
```

Add to `urls.py`:
```python
path('api/webhooks/payments', views.payment_webhook, name='payment_webhook'),
```

### 3. Query Payment Status

```python
import requests

response = requests.get(
    f'{PAYMENTS_SERVICE_URL}/payments/{pending_id}/status'
)
payment = response.json()
print(f"Payment status: {payment['status']}")
```

---

## Development

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev:api
```

### Build for Production

```bash
npm run build
npm start
```

### Docker

```bash
docker compose up payments
```

---

## Data Persistence

The service uses file-based JSON storage in the `data/` directory:
- `data/sellers.json` - Registered sellers
- `data/pending.json` - Pending payment records

In production, consider migrating to a proper database (PostgreSQL, MongoDB, etc.).

---

## Security Considerations

1. **Private Keys**: Store wallet private keys securely. Never commit them to version control.
2. **Webhook Authentication**: Add authentication to webhook endpoints in production.
3. **CORS**: Configure CORS properly for your domain in production.
4. **HTTPS**: Always use HTTPS in production.
5. **Environment Variables**: Use proper secret management for production credentials.

---

## Testing

Test the service with curl:

```bash
# Health check
curl http://localhost:4001/health

# List sellers
curl http://localhost:4001/sellers

# Start quote
curl -X POST http://localhost:4001/offers/123/quotes/start \
  -H "Content-Type: application/json" \
  -d '{
    "sellerId": "default-seller",
    "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
    "amount": "100"
  }'
```

---

## Support

For issues or questions:
1. Check the logs: `docker compose logs payments`
2. Verify environment configuration
3. Ensure private keys are accessible
4. Check Interledger wallet connectivity
