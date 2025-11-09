# Payments Service (Interledger Open Payments)

Express-based microservice implementing a buyer → quote → interactive grant → outgoing payment flow, mirroring the Python reference in Hop Sauna.

Reference: Hop Sauna OpenPaymentsProcessor https://codeberg.org/whythawk/hop-sauna/src/branch/main/backend/app/app/crud/openpayments/crud_open_payments.py

## What this service does

- Stores sellers (merchant accounts) with their Open Payments credentials (wallet address URL, keyId, private key path).
- Starts a buyer quote flow:
  - Create seller incoming payment (escrow-like)
  - Create buyer quote (receiver = seller incoming payment)
  - Request interactive outgoing-payment grant (redirect browser to wallet)
- Completes payment when the wallet redirects to `/payments/finish`.

No Django changes required. Django should call the `start` endpoint and then redirect the user to the wallet. After completion, Django can poll or listen for a webhook (webhook not implemented yet).

## Requirements

- Node 18+
- Install dependencies:
  - `cd services/payments && npm install`
- Open Payments test wallets for:
  - Seller(s): merchant accounts you control (store their key material here)
  - Buyer: the end-user’s wallet address URL (no keys stored here)

## Configure environment

Copy and adjust:

```bash
cp ENV.sample .env
```

- `PORT`: default 4001
- `BASE_URL`: public URL for this service (used in interactive finish redirect). If developing locally, use a tunnel (e.g., `http://localhost:4001` or an ngrok URL).

## Seller keys

For each seller, you need:
- `walletAddressUrl`: e.g., `https://ilp.interledger-test.dev/alice`
- `keyId`: created in the wallet UI or API
- `privateKeyPath`: absolute path to the seller’s private key (PEM/PKCS8). Keep keys out of Git.

Add sellers via API:

```bash
curl -sS -X POST http://localhost:4001/sellers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "seller-1",
    "walletAddressUrl": "https://ilp.interledger-test.dev/alice",
    "keyId": "YOUR_KEY_ID",
    "privateKeyPath": "/ABSOLUTE/PATH/TO/private.key"
  }'
```

Example using a specific seller:

```bash
curl -sS -X POST http://localhost:4001/sellers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "seller-mvr5656",
    "walletAddressUrl": "https://ilp.interledger-test.dev/mvr5656",
    "keyId": "fe775339-6ebc-4eb8-a4b4-0811acba3b62",
    "privateKeyPath": "private.key"
  }'
```

List sellers:

```bash
curl -sS http://localhost:4001/sellers | jq
```

Data persists in `services/payments/data/`.

## Run the service

```bash
cd services/payments
npm run dev:api
# or build+start
npm run build && npm start
```

## API

### POST /offers/:offerId/quotes/start

Start buyer flow: create seller incoming payment, buyer quote, and interactive grant redirect.

Body:
```json
{
  "sellerId": "seller-1",
  "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/buyer",
  "amount": "100"
}
```

Response:
```json
{
  "pendingId": "01HZZ…",
  "redirectUrl": "https://wallet.example/grants/…"
}
```

Redirect the browser to `redirectUrl`.

### GET /payments/finish

Called by the buyer’s wallet after authentication.

Query params:
- `pendingId`
- `interact_ref`
- `hash` (currently not validated; see TODO)

Completes the grant continuation and creates an outgoing payment using the stored `quoteId`.

Response:
```json
{
  "ok": true,
  "outgoingPayment": { "id": "…" }
}
```

## Django integration (no code changes)

- Offer creation UI stores:
  - `buyerWalletAddressUrl`
  - `amount`
  - candidate `sellerId`s
- “Approve quote” button:
  - Django calls `POST /offers/:offerId/quotes/start` with `sellerId`, `buyerWalletAddressUrl`, `amount`
  - Receive `{ redirectUrl }` and redirect the browser
- Success page:
  - After `/payments/finish`, you can poll a status endpoint (add later) or handle a webhook (add later).

## Test with curl

The `scripts/` directory contains curl-based scripts for testing each endpoint:

### List all sellers
```bash
bash scripts/00_list_sellers.sh
```

### Add a seller
```bash
bash scripts/01_add_seller.sh <sellerId> <walletAddressUrl> <keyId> <privateKeyPath>
```

Example:
```bash
bash scripts/01_add_seller.sh \
  seller-mvr5656 \
  https://ilp.interledger-test.dev/mvr5656 \
  fe775339-6ebc-4eb8-a4b4-0811acba3b62 \
  private.key
```

### Start a quote
```bash
bash scripts/02_start_quote.sh <offerId> <sellerId> <buyerWalletAddressUrl> <amount>
```

Example:
```bash
bash scripts/02_start_quote.sh \
  offer-123 \
  seller-mvr5656 \
  https://ilp.interledger-test.dev/buyer \
  100
```

Follow the printed `redirectUrl` in a browser to authenticate.

### Finish payment
In real flow, the wallet calls `/payments/finish`. For local testing (without a wallet), you can simulate:
```bash
bash scripts/03_finish_payment.sh <pendingId> <interact_ref> <hash>
```

Example:
```bash
# NOTE: This won't actually continue the grant without a real wallet's interact_ref/hash.
bash scripts/03_finish_payment.sh 01HZZ... TEST TEST
```

### Full workflow example
To see the complete flow with documentation:
```bash
bash scripts/full_workflow_example.sh
```

## New Features (2025 Update)

### ✅ Payment Status Endpoints
- `GET /payments/:pendingId/status` - Query individual payment status
- `GET /payments/pending` - List all payments
- `GET /offers/:offerId/payments` - Get all payments for a job

### ✅ Django Integration Endpoint
- `POST /api/payments/incoming` - Create incoming payment for escrow/pre-approved payments

### ✅ Webhook Notifications
- Automatic Django notifications on payment completion
- Configurable via `DJANGO_BASE_URL` environment variable
- Sends events to `/api/webhooks/payments` endpoint

### ✅ Error Handling
- Comprehensive error middleware
- Structured error responses
- Development mode stack traces

### ✅ Documentation
- Complete API documentation in [API.md](./API.md)
- Django integration examples
- Testing guide with curl examples

## Configuration (Updated)

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Key configuration options:
```bash
PORT=3000
BASE_URL=http://localhost:4001
DJANGO_BASE_URL=http://web:8000  # For webhook notifications

# Optional: Auto-register default seller on startup
SELLER_ID=default-seller
SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/mvr5656
SELLER_KEY_ID=fe775339-6ebc-4eb8-a4b4-0811acba3b62
SELLER_PRIVATE_KEY_PATH=./privates/mvr5656.key
```

## Notes and TODOs

- Hash verification: implement verification of `hash` against `finishId`/wallet per your wallet provider. The Python reference uses a `verify_response_hash` helper.
- ~~Webhooks/status: add `/offers/:offerId/status` and a webhook to notify Django when payments finalize.~~ ✅ **COMPLETED**
- Key rotation: store `privateKeyPath` securely; consider a secrets manager in production.
- Consider migrating from file-based storage to database for production use.


