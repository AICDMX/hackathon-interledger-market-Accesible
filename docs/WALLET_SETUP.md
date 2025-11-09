# Wallet Setup Guide

This document explains how the Interledger wallet profiles are configured in the marketplace.

## Overview

The marketplace uses three Interledger test wallet profiles with distinct roles:

```
┌─────────────────────────────────────────────────────────┐
│         mvr5656 (Platform/Issuer)                       │
│         Authenticates API calls                         │
│         MXN, Asset Scale: 2                             │
└─────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                  ↓
┌──────────────────────┐      ┌──────────────────────┐
│ edutest (Funder)     │      │ bobtest5656 (Creator)│
│ Sends Payments       │      │ Receives Payments    │
│ EUR, Asset Scale: 2  │      │ EUR, Asset Scale: 2  │
└──────────────────────┘      └──────────────────────┘
```

## Wallet Profiles

### 1. mvr5656 (Emisor/Issuer) - Platform Wallet
- **URL**: `https://ilp.interledger-test.dev/mvr5656`
- **Role**: Platform/Seller (used for API authentication)
- **Asset**: MXN (Mexican Peso), scale 2
- **Key ID**: `fe775339-6ebc-4eb8-a4b4-0811acba3b62`
- **Private Key**: Stored in `services/payments/src/privates/AICDMX_private.key`
- **Purpose**: 
  - Authenticates all Open Payments API calls
  - Used by the payments service to query wallet profiles
  - Acts as the platform's escrow wallet

**Configuration** (already done):
```bash
curl -X POST http://localhost:4001/sellers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "seller-mvr5656",
    "walletAddressUrl": "https://ilp.interledger-test.dev/mvr5656",
    "keyId": "fe775339-6ebc-4eb8-a4b4-0811acba3b62",
    "privateKeyPath": "/app/src/privates/AICDMX_private.key"
  }'
```

### 2. edutest (Remitente/Sender) - Funder Wallet
- **URL**: `https://ilp.interledger-test.dev/edutest`
- **Role**: Funder/Buyer
- **Asset**: EUR (Euro), scale 2
- **Purpose**: 
  - Used by job funders to pay for work
  - Initiates outgoing payments
  - Example user: `default_funder`

**User Setup**:
Users with the "Funder" role should set their profile's `wallet_endpoint` to:
```
https://ilp.interledger-test.dev/edutest
```

### 3. bobtest5656 (Receptor/Receiver) - Creator Wallet
- **URL**: `https://ilp.interledger-test.dev/bobtest5656`
- **Role**: Creator/Worker
- **Asset**: EUR (Euro), scale 2
- **Purpose**: 
  - Used by job creators to receive payment
  - Receives incoming payments for completed work
  - Example user: `joss`

**User Setup**:
Users with the "Creator" role should set their profile's `wallet_endpoint` to:
```
https://ilp.interledger-test.dev/bobtest5656
```

## Wallet Validation Workflow

When a funder clicks "Approve Quote & Pay":

1. **Validation** (`POST /api/wallet/profile`):
   ```json
   Request:
   {
     "walletAddressUrl": "https://ilp.interledger-test.dev/edutest"
   }
   
   Response:
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

2. **Quote Creation** (`POST /offers/:offerId/quotes/start`):
   - Creates incoming payment on seller (mvr5656)
   - Creates quote for buyer (edutest)
   - Requests interactive grant

3. **User Authorization**:
   - User redirected to Interledger auth page
   - Approves the payment in their wallet

4. **Payment Completion** (`GET /payments/finish`):
   - Wallet redirects back to payments service
   - Service completes the outgoing payment

## Docker Configuration

The `docker-compose.yml` mounts necessary directories:

```yaml
payments:
  volumes:
    - ./services/payments/data:/app/dist/data
    - ./services/payments/src/privates:/app/src/privates:ro
```

- `data/` - Stores seller configurations and pending payments
- `src/privates/` - Contains private key files (read-only mount)

## Testing Wallet Profiles

Test each wallet profile:

```bash
# Test edutest (Funder)
curl -X POST http://localhost:4001/api/wallet/profile \
  -H "Content-Type: application/json" \
  -d '{"walletAddressUrl": "https://ilp.interledger-test.dev/edutest"}'

# Test bobtest5656 (Creator)
curl -X POST http://localhost:4001/api/wallet/profile \
  -H "Content-Type: application/json" \
  -d '{"walletAddressUrl": "https://ilp.interledger-test.dev/bobtest5656"}'

# Test mvr5656 (Platform)
curl -X POST http://localhost:4001/api/wallet/profile \
  -H "Content-Type: application/json" \
  -d '{"walletAddressUrl": "https://ilp.interledger-test.dev/mvr5656"}'
```

All should return `"success": true` with wallet details.

## Database Configuration

Users in the Django database are configured with wallet endpoints:

```sql
-- Check current configuration
SELECT id, username, role, wallet_endpoint FROM users_user;

-- Update funder wallet
UPDATE users_user 
SET wallet_endpoint = 'https://ilp.interledger-test.dev/edutest' 
WHERE role IN ('funder', 'both');

-- Update creator wallet
UPDATE users_user 
SET wallet_endpoint = 'https://ilp.interledger-test.dev/bobtest5656' 
WHERE role IN ('creator', 'both');
```

## Security Considerations

- **Private Keys**: Never commit private key files to version control
- **Read-Only Mount**: Private keys are mounted read-only in Docker
- **Seller Configuration**: Seller data persists in `data/sellers.json`
- **Test Wallets Only**: Current setup uses Interledger testnet wallets

## Troubleshooting

### "Please add your wallet address in your profile first"
- User's `wallet_endpoint` field is empty
- Go to Profile → Wallet Endpoint → Enter appropriate URL

### "Could not validate wallet address"
- Wallet profile API call failed
- Check payments service logs: `docker compose logs payments`
- Verify wallet URL is accessible
- Ensure seller (mvr5656) is configured correctly

### "ENOENT: no such file or directory, open '/app/src/privates/...'"
- Private key file not found in Docker container
- Verify the `src/privates/` directory exists on host
- Check Docker volume mount in `docker-compose.yml`

## References

- [Open Payments Specification](https://openpayments.guide/)
- [Interledger Test Network](https://interledger.org/developers/get-started/)
- [Services Payments README](../services/payments/README.md)
