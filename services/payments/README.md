# Payments Service (Interledger Open Payments)

Express-based microservice implementing a buyer → quote → interactive grant → outgoing payment flow, mirroring the Python reference in Hop Sauna.

Reference: Hop Sauna OpenPaymentsProcessor https://codeberg.org/whythawk/hop-sauna/src/branch/main/backend/app/app/crud/openpayments/crud_open_payments.py

## What this service does

- Stores sellers (merchant accounts) with their Open Payments credentials (wallet address URL, keyId, private key path).
- **Validates wallet profiles** via Open Payments API before initiating payments.
- Starts a buyer quote flow:
  - Create seller incoming payment (escrow-like)
  - Create buyer quote (receiver = seller incoming payment)
  - Request interactive outgoing-payment grant (redirect browser to wallet)
- Completes payment when the wallet redirects to `/payments/finish`.

Django integration validates wallet addresses via the `/api/wallet/profile` endpoint before starting the quote flow.

## Wallet Profiles Setup

This service uses three Interledger test wallet profiles:

1. **mvr5656 (Emisor/Issuer)** - `https://ilp.interledger-test.dev/mvr5656`
   - Role: Platform/Seller (authenticates API calls)
   - Asset: MXN, scale 2
   - Requires private key stored in `src/privates/AICDMX_private.key`

2. **edutest (Remitente/Sender)** - `https://ilp.interledger-test.dev/edutest`
   - Role: Funder/Buyer (pays for jobs)
   - Asset: EUR, scale 2
   - Assigned to funder users in Django

3. **bobtest5656 (Receptor/Receiver)** - `https://ilp.interledger-test.dev/bobtest5656`
   - Role: Creator/Worker (receives payment)
   - Asset: EUR, scale 2
   - Assigned to creator users in Django

## Requirements

- Node 18+
- Install dependencies:
  - `cd services/payments && npm install`
- Private key file for the platform wallet (mvr5656) in `src/privates/AICDMX_private.key`
- Docker volume mounts configured for:
  - `./services/payments/data` → `/app/dist/data` (persistent storage)
  - `./services/payments/src/privates` → `/app/src/privates:ro` (private keys, read-only)

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

### POST /api/wallet/profile

**Validates a wallet address** by fetching its profile from the Interledger Open Payments API.

This endpoint is called by Django before initiating a payment to ensure the wallet address is valid and reachable.

Body:
```json
{
  "walletAddressUrl": "https://ilp.interledger-test.dev/edutest"
}
```

Response (success):
```json
{
  "success": true,
  "wallet": {
    "id": "https://ilp.interledger-test.dev/edutest",
    "assetCode": "EUR",
    "assetScale": 2,
    "authServer": "https://auth.interledger-test.dev/...",
    "resourceServer": "https://ilp.interledger-test.dev/..."
  }
}
```

Response (error):
```json
{
  "error": "Invalid wallet address or unreachable"
}
```

**Example:**
```bash
curl -X POST http://localhost:4001/api/wallet/profile \
  -H "Content-Type: application/json" \
  -d '{"walletAddressUrl": "https://ilp.interledger-test.dev/edutest"}'
```

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

## Django Integration

The Django marketplace integrates with this service through the `jobs/payments_utils.py` module.

### Wallet Validation Workflow

1. **User Profile Setup**:
   - Funders set `wallet_endpoint` to their Interledger wallet URL (e.g., `https://ilp.interledger-test.dev/edutest`)
   - Creators set `wallet_endpoint` to their wallet URL (e.g., `https://ilp.interledger-test.dev/bobtest5656`)

2. **"Approve Quote & Pay" Flow** (`jobs/views.py::approve_quote`):
   - ✅ Check if user has `wallet_endpoint` configured
   - ✅ **Call `POST /api/wallet/profile`** to validate the wallet address
   - ✅ If validation fails, show error and redirect back
   - ✅ Call `POST /offers/:offerId/quotes/start` to initiate payment
   - ✅ Redirect browser to Interledger auth page

3. **Payment Completion**:
   - After user approves in wallet, Interledger redirects to `/payments/finish`
   - Service completes the outgoing payment
   - Django can poll payment status (future: webhook support)

### Django Helper Functions

```python
# jobs/payments_utils.py

# Validate wallet profile
get_wallet_profile(wallet_address_url)
# Returns: {"success": True, "wallet": {...}} or {"success": False, "error": "..."}

# Start payment quote
start_quote(offer_id, seller_id, buyer_wallet_address_url, amount)
# Returns: {"success": True, "redirect_url": "..."} or {"success": False, "error": "..."}

# Create incoming payment (escrow)
create_incoming_payment(amount, description)
# Returns: {"success": True, "payment_id": "..."} or {"success": False, "error": "..."}
```

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


