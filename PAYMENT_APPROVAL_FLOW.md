# Interactive Payment Approval Flow

## Overview

This document explains the interactive payment approval flow based on Interledger Open Payments step 7-8. This allows funders (buyers) to approve payments through their wallet's interactive interface.

## Interledger Flow (8 Steps)

Based on the [Interledger peer-to-peer example](https://github.com/interledger/open-payments-node/blob/main/examples/peer-to-peer/index.js):

### Steps 1-6: Automated Setup
1. **Fetch wallet addresses** - Get buyer and seller wallet info
2. **Request incoming payment grant** - Seller gets permission to receive
3. **Create incoming payment** - Escrow/destination for funds
4. **Request quote grant** - Buyer gets permission to quote
5. **Create quote** - Calculate exact costs for transfer
6. *(Internal)* - Prepare for interactive approval

### Steps 7-8: Interactive Approval ⭐ (Implemented)
7. **Request interactive outgoing grant** - Ask buyer's wallet for payment permission
   - Returns a redirect URL for the buyer
   - Includes payment limits and details
   - Wallet shows approval interface
   
8. **Buyer approves in wallet** - User authorizes payment
   - Wallet redirects back with approval token
   - System continues the grant
   - Creates outgoing payment
   - Transfers funds

## Implementation in Django

### Flow Diagram

```
┌─────────────────┐
│  Job Funder     │
│  (Buyer)        │
└────────┬────────┘
         │ 1. Click "Pre-Approve Payment"
         ↓
┌─────────────────────────────┐
│  Django: pre_approve_       │
│  payments() view            │
└────────┬────────────────────┘
         │ 2. Validates wallet address
         │ 3. Calls payments service
         ↓
┌─────────────────────────────┐
│  Payments Service           │
│  startQuoteFlow()           │
│  • Creates incoming payment │
│  • Creates quote            │
│  • Requests interactive     │
│    outgoing grant           │
└────────┬────────────────────┘
         │ 4. Returns redirect URL
         ↓
┌─────────────────────────────┐
│  Django: Stores payment_url │
│  Shows "Approve Payment"    │
│  button                     │
└────────┬────────────────────┘
         │ 5. User clicks button
         ↓
┌─────────────────────────────┐
│  Buyer's Wallet             │
│  (e.g., Rafiki testnet)     │
│  • Shows payment details    │
│  • User approves/rejects    │
└────────┬────────────────────┘
         │ 6. Redirects with interact_ref
         ↓
┌─────────────────────────────┐
│  Django: /payments/finish   │
│  • Proxies to payments      │
│    service                  │
│  • Completes grant          │
│  • Creates outgoing payment │
└────────┬────────────────────┘
         │ 7. Webhook notification
         ↓
┌─────────────────────────────┐
│  Django: Updates job        │
│  • contract_completed=True  │
│  • status='complete'        │
└─────────────────────────────┘
```

### Code Implementation

#### 1. Pre-Approve Payment View (`jobs/views.py`)

```python
@login_required
@require_POST
def pre_approve_payments(request, pk):
    """Start interactive payment approval flow"""
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    # Validate prerequisites
    if not request.user.wallet_address:
        messages.error(request, 'Configure wallet address first')
        return redirect('jobs:detail', pk=job.pk)
    
    # Validate wallet
    wallet_result = get_wallet_profile(request.user.wallet_address)
    if not wallet_result.get('success'):
        messages.error(request, 'Invalid wallet address')
        return redirect('jobs:detail', pk=job.pk)
    
    # Start quote flow
    result = start_quote(
        offer_id=str(job.pk),
        seller_id=settings.DEFAULT_SELLER_ID,
        buyer_wallet_address_url=request.user.wallet_address,
        amount=str(job.budget)
    )
    
    if result.get('success'):
        # Store payment URL for user to approve
        job.payment_url = result.get('payment_url')
        job.payment_id = result.get('pending_id')
        job.save()
        
        messages.success(request, 'Ready to approve payment!')
        return redirect('jobs:detail', pk=job.pk)
```

#### 2. Payments Service (`services/payments/src/workflow/paymentsService.ts`)

The service handles steps 1-7 automatically:

```typescript
export async function startQuoteFlow(args) {
  // 1-2: Incoming payment grant + creation
  const incoming = await createIncomingPayment(...)
  
  // 3-4: Quote grant + creation
  const quote = await createQuote(...)
  
  // 5-7: Interactive outgoing grant
  const interactive = await requestInteractiveOutgoingGrant(client, {
    buyerWalletAddressUrl,
    debitAmount: quote.debitAmount,
    finish: { uri: finishUrl, nonce: pendingId },
    clientId: sellerWallet.id
  })
  
  // Return redirect URL for step 8
  return {
    redirectUrl: interactive.redirect,
    pendingId,
    ...
  }
}
```

#### 3. Finish Handler (`jobs/views.py::payments_finish`)

Handles wallet redirect after approval:

```python
def payments_finish(request):
    """Handle wallet redirect after approval"""
    pending_id = request.GET.get('pendingId')
    interact_ref = request.GET.get('interact_ref')
    hash = request.GET.get('hash')
    
    # Proxy to payments service to complete grant
    resp = requests.get(
        f"{settings.PAYMENTS_SERVICE_URL}/payments/finish",
        params={'pendingId': pending_id, 'interact_ref': interact_ref, 'hash': hash}
    )
    
    # Show confirmation and redirect
    messages.success(request, 'Payment completed!')
    return redirect('jobs:detail', pk=offer_id)
```

## User Experience

### For the Funder (Buyer)

1. **Select applicants** for the job
2. **Click "Pre-Approve Payment"** button
   - System validates wallet
   - Creates payment request
3. **Click "Approve Payment in Wallet"** button
   - Opens wallet in new tab
4. **Review payment details** in wallet
   - Amount, recipient, description
5. **Click "Approve"** in wallet
   - Wallet processes authorization
6. **Redirected back to marketplace**
   - See confirmation message
   - Job marked as paid

### For Workers (No action required)

Workers see the job status change to "complete" and know payment was released.

## Configuration

### Environment Variables

**Django** (`marketplace-py/.env` or settings):
```bash
DEFAULT_SELLER_ID=default-seller
PAYMENTS_SERVICE_URL=http://payments:3000
```

**Payments Service** (`services/payments/.env`):
```bash
BASE_URL=http://localhost:4001
DJANGO_BASE_URL=http://web:8000
SELLER_ID=default-seller
SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/mvr5656
SELLER_KEY_ID=fe775339-6ebc-4eb8-a4b4-0811acba3b62
SELLER_PRIVATE_KEY_PATH=./privates/mvr5656.key
```

### User Profile Requirements

Users must have:
- `wallet_address` configured in their profile
- Valid Interledger wallet (e.g., Rafiki testnet)

## API Endpoints

### 1. Start Quote (Django → Payments Service)
```
POST /offers/{offerId}/quotes/start

Body:
{
  "sellerId": "default-seller",
  "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
  "amount": "100.00"
}

Response:
{
  "success": true,
  "redirectUrl": "https://auth.interledger-test.dev/interact/...",
  "pendingId": "01HZZ...",
  "paymentUrl": "https://auth.interledger-test.dev/interact/..."
}
```

### 2. Finish Payment (Wallet → Django → Payments Service)
```
GET /payments/finish?pendingId=01HZZ...&interact_ref=abc123&hash=xyz789

Response: Redirects to job detail page
```

### 3. Payment Webhook (Payments Service → Django)
```
POST /api/webhooks/payments

Body:
{
  "type": "payment.completed",
  "pendingId": "01HZZ...",
  "offerId": "123",
  "status": "paid"
}
```

## Testing

### 1. Create Test Seller

```bash
curl -X POST http://localhost:4001/sellers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "default-seller",
    "walletAddressUrl": "https://ilp.interledger-test.dev/mvr5656",
    "keyId": "YOUR_KEY_ID",
    "privateKeyPath": "/app/src/privates/private.key"
  }'
```

### 2. Test Full Flow

1. Create a job as funder
2. Set wallet address in profile: `https://ilp.interledger-test.dev/edutest`
3. Approve applicants
4. Click "Pre-Approve Payment"
5. Click "Approve Payment in Wallet" (opens wallet)
6. Approve in wallet interface
7. Get redirected back with confirmation

### 3. Manual Testing

```bash
# Start quote
curl -X POST http://localhost:4001/offers/1/quotes/start \
  -H "Content-Type: application/json" \
  -d '{
    "sellerId": "default-seller",
    "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/edutest",
    "amount": "100"
  }'

# Returns redirectUrl - open in browser
# After approval, wallet redirects to /payments/finish
```

## Error Handling

### Common Issues

**"Configure wallet address first"**
- User needs to add wallet address in profile
- Go to profile → Add Interledger wallet URL

**"Invalid wallet address"**
- Wallet URL is malformed or unreachable
- Verify format: `https://ilp.interledger-test.dev/username`

**"Failed to initialize payment"**
- Payments service may be down
- Check: `docker compose logs payments`
- Verify seller is configured

**"Payment approval expired"**
- Interactive grants have timeout (usually 10 minutes)
- Start over by clicking "Pre-Approve Payment" again

## Security Considerations

### Current Implementation
- ✅ Wallet address validation before starting
- ✅ User must be authenticated (funder)
- ✅ Job ownership verification
- ✅ Payment limits enforced by quote

### Future Enhancements
- 🔒 Payment amount verification before approval
- 🔒 Timeout handling for expired grants
- 🔒 Retry mechanism for failed approvals
- 🔒 Multi-recipient payments (batch)

## Next Steps

1. ✅ **Interactive approval implemented**
2. 📧 **Add email notification** when approval needed
3. ⏱️ **Add timeout handling** for expired grants
4. 🔄 **Add status polling** on approval page
5. 💰 **Support partial payments** for multiple workers
6. 📊 **Add approval analytics** dashboard

## References

- [Interledger Open Payments](https://openpayments.guide/)
- [Peer-to-Peer Example](https://github.com/interledger/open-payments-node/blob/main/examples/peer-to-peer/index.js)
- [Grant Continuation Docs](https://openpayments.guide/introduction/grants/)
- [Interactive Grants](https://openpayments.guide/introduction/grants/#interactive-grants)

---

**Status**: ✅ Implemented  
**Version**: 1.0  
**Date**: January 9, 2025
