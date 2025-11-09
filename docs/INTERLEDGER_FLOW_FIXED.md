# Interledger Payment Flow - Implementation Guide

## Overview

This document explains the correct Interledger Open Payments flow based on the official peer-to-peer example.

## Key Concepts

### 1. Single Authenticated Client
- **One authenticated client** (seller/platform) can perform operations on behalf of other wallets
- The client authenticates with its own private key but can request grants for OTHER wallets
- Buyer's private key is **never needed** - grants are either auto-finalized or user-interactive

### 2. Amount Format (CRITICAL)
Interledger expects amounts in **smallest units** (uint64 format):
- ✅ Correct: `"10000"` (10000 cents = 100.00 EUR with assetScale=2)
- ❌ Wrong: `"100.00"` (decimals not allowed)
- ❌ Wrong: `100` (must be string)

**Formula**: `amountInSmallestUnit = amount × 10^assetScale`

Example:
- 100.00 EUR, assetScale=2 → `"10000"` (cents)
- 5.50 USD, assetScale=2 → `"550"` (cents)

## Payment Flow Steps

### Step 1: Get Wallet Addresses
```typescript
// Seller (receiver) wallet
const sellerWallet = await client.walletAddress.get({
  url: SELLER_WALLET_ADDRESS_URL
});

// Buyer (sender) wallet
const buyerWallet = await client.walletAddress.get({
  url: BUYER_WALLET_ADDRESS_URL
});
```

### Step 2: Create Incoming Payment (on Seller's Wallet)
```typescript
// Request grant for incoming payment on seller's auth server
const incomingPaymentGrant = await client.grant.request(
  { url: sellerWallet.authServer },
  {
    access_token: {
      access: [{
        type: 'incoming-payment',
        actions: ['read', 'complete', 'create']
      }]
    }
  }
);

// Convert amount to smallest unit
const amountInSmallestUnit = (amount * Math.pow(10, sellerWallet.assetScale)).toString();

// Create incoming payment
const incomingPayment = await client.incomingPayment.create(
  {
    url: sellerWallet.resourceServer,
    accessToken: incomingPaymentGrant.access_token.value
  },
  {
    walletAddress: sellerWallet.id,
    incomingAmount: {
      assetCode: sellerWallet.assetCode,
      assetScale: sellerWallet.assetScale,
      value: amountInSmallestUnit
    }
  }
);
```

### Step 3: Create Quote (on Buyer's Wallet)
```typescript
// Request grant for quote on buyer's auth server
const quoteGrant = await client.grant.request(
  { url: buyerWallet.authServer },
  {
    access_token: {
      access: [{
        type: 'quote',
        actions: ['create', 'read']
      }]
    }
  }
);

// Create quote
const quote = await client.quote.create(
  {
    url: buyerWallet.resourceServer,
    accessToken: quoteGrant.access_token.value
  },
  {
    walletAddress: buyerWallet.id,
    receiver: incomingPayment.id,
    method: 'ilp'
  }
);
```

### Step 4: Request Interactive Outgoing Payment Grant
```typescript
// Request interactive grant for outgoing payment on buyer's auth server
const outgoingPaymentGrant = await client.grant.request(
  { url: buyerWallet.authServer },
  {
    access_token: {
      access: [{
        type: 'outgoing-payment',
        actions: ['read', 'create'],
        limits: {
          debitAmount: {
            assetCode: quote.debitAmount.assetCode,
            assetScale: quote.debitAmount.assetScale,
            value: quote.debitAmount.value
          }
        },
        identifier: buyerWallet.id
      }]
    },
    interact: {
      start: ['redirect'],
      finish: {
        method: 'redirect',
        uri: 'https://yourapp.com/payments/finish',
        nonce: pendingId
      }
    }
  }
);

// Redirect user to approve
console.log('Redirect user to:', outgoingPaymentGrant.interact.redirect);
```

### Step 5: User Authorizes Payment
- User clicks "Approve Quote & Pay"
- Redirected to: `outgoingPaymentGrant.interact.redirect`
- User approves payment in their wallet UI
- Wallet redirects back to: `https://yourapp.com/payments/finish?interact_ref=XXX&hash=YYY`

### Step 6: Continue Grant and Create Outgoing Payment
```typescript
// Continue the grant using interact_ref from redirect
const finalizedGrant = await client.grant.continue({
  url: outgoingPaymentGrant.continue.uri,
  accessToken: outgoingPaymentGrant.continue.access_token.value
}, {
  interact_ref: interact_ref_from_redirect
});

// Create outgoing payment
const outgoingPayment = await client.outgoingPayment.create(
  {
    url: buyerWallet.resourceServer,
    accessToken: finalizedGrant.access_token.value
  },
  {
    walletAddress: buyerWallet.id,
    quoteId: quote.id
  }
);

// Payment complete! Funds move from buyer to seller over ILP
```

## Our Implementation

### Configuration (docker-compose.yml)
```yaml
environment:
  - SELLER_ID=seller-mvr5656
  - SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/mvr5656
  - SELLER_KEY_ID=3f722728-a2c1-44d3-add9-ad4ac3ce11b1
  - SELLER_PRIVATE_KEY_PATH=/app/src/privates/mvr5656.key
```

### Flow in Our Code

1. **Django → startQuote()** (`POST /offers/{offerId}/quotes/start`)
   - Input: offerId, sellerId, buyerWalletAddressUrl, amount
   - Creates: incoming payment + quote + interactive grant
   - Returns: redirect URL for user approval

2. **User approves** in browser at Interledger wallet

3. **Wallet → finishPayment()** (`GET /payments/finish?pendingId=X&interact_ref=Y&hash=Z`)
   - Continues grant with interact_ref
   - Creates outgoing payment
   - Notifies Django of completion

## Common Errors

### ❌ "invalid signature"
- Wrong key ID or private key
- Private key not registered with auth server
- Check: SELLER_KEY_ID matches registered public key

### ❌ "must match format uint64"
- Amount contains decimal point
- Solution: Convert to smallest unit (amount × 10^assetScale)

### ❌ "invalid_client"
- Client wallet URL doesn't match key registration
- Check: SELLER_WALLET_ADDRESS_URL matches key registration

## Testing

```bash
# Test wallet profile fetch
curl -X POST http://localhost:4001/api/wallet/profile \
  -H "Content-Type: application/json" \
  -d '{"walletAddressUrl": "https://ilp.interledger-test.dev/edutest"}'

# Start a payment (will return redirect URL)
curl -X POST http://localhost:4001/offers/123/quotes/start \
  -H "Content-Type: application/json" \
  -d '{
    "sellerId": "seller-mvr5656",
    "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
    "amount": "100"
  }'
```

## References

- [Interledger Open Payments Node](https://github.com/interledger/open-payments-node)
- [Peer-to-Peer Example](https://github.com/interledger/open-payments-node/blob/main/examples/peer-to-peer/index.js)
- [Open Payments Specification](https://openpayments.guide/)
