# Payment Service Test Scripts

Quick reference for testing the Interledger payment service endpoints.

## Environment Variables

All scripts respect the `BASE_URL` environment variable:

```bash
export BASE_URL=http://localhost:4001
# or for remote testing:
export BASE_URL=https://your-payments-service.com
```

## Scripts Overview

### `00_list_sellers.sh`
List all registered sellers.

```bash
./00_list_sellers.sh
```

### `01_add_seller.sh`
Register a new seller with their Open Payments credentials.

```bash
./01_add_seller.sh <sellerId> <walletAddressUrl> <keyId> <privateKeyPath>
```

**Example:**
```bash
./01_add_seller.sh \
  seller-mvr5656 \
  https://ilp.interledger-test.dev/mvr5656 \
  fe775339-6ebc-4eb8-a4b4-0811acba3b62 \
  private.key
```

### `02_start_quote.sh`
Initiate a payment quote for an offer. Returns a `redirectUrl` that the buyer must visit to authorize the payment.

```bash
./02_start_quote.sh <offerId> <sellerId> <buyerWalletAddressUrl> <amount>
```

**Example:**
```bash
./02_start_quote.sh \
  offer-123 \
  seller-mvr5656 \
  https://ilp.interledger-test.dev/buyer \
  100
```

The output includes:
- `pendingId`: Transaction identifier for completion
- `redirectUrl`: URL to redirect the buyer's browser for wallet authorization

### `03_finish_payment.sh`
Complete a payment after wallet authorization (normally called automatically by wallet redirect).

```bash
./03_finish_payment.sh <pendingId> <interact_ref> <hash>
```

**Example:**
```bash
./03_finish_payment.sh 01HZZ... abc123ref xyz789hash
```

**Note:** In production, this endpoint is called automatically by the buyer's wallet after authorization. The `interact_ref` and `hash` values come from the wallet's callback.

### `full_workflow_example.sh`
Demonstrates the complete payment flow with inline documentation. Run this to understand the full workflow.

```bash
./full_workflow_example.sh
```

## Complete Workflow

1. **Register a seller** (one-time setup):
   ```bash
   ./01_add_seller.sh seller-1 https://ilp.test/seller key123 ./keys/seller.key
   ```

2. **List sellers** to verify:
   ```bash
   ./00_list_sellers.sh
   ```

3. **Start a quote** for a buyer:
   ```bash
   ./02_start_quote.sh offer-abc seller-1 https://ilp.test/buyer 50
   ```
   
   Save the `pendingId` and copy the `redirectUrl`.

4. **Redirect buyer** to the `redirectUrl` in a browser where they authorize the payment.

5. **Wallet completes** payment by calling `/payments/finish` (automatic).

## Testing Tips

- **Local development:** Use `http://localhost:4001` as BASE_URL
- **Docker Compose:** Service runs on port 4001 by default
- **Remote testing:** Set BASE_URL to your deployed service
- **Dependencies:** All scripts require `jq` for JSON formatting

## Troubleshooting

**Script not executable:**
```bash
chmod +x scripts/*.sh
```

**Missing jq:**
```bash
# macOS
brew install jq

# Ubuntu/Debian
apt-get install jq
```

**Connection refused:**
- Verify service is running: `curl http://localhost:4001/sellers`
- Check Docker containers: `docker compose ps`
- Check logs: `docker compose logs payments`
