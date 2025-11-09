# Interledger Payment Integration - Quick Start Guide

## What Was Implemented

This integration connects the job marketplace with Interledger Open Payments, enabling funders to initiate payments directly from job pages. When a job is available, the system:

1. **Generates a payment quote** using the Interledger protocol
2. **Creates a payment link** that redirects to the buyer's wallet
3. **Displays the payment link** on the job detail page for easy access
4. **Tracks payment status** using pending payment IDs

## Key Features

✅ **Automatic Payment Quote Generation** - Click "Approve Quote & Pay" to instantly create a payment quote  
✅ **Payment Link Display** - Payment URL is saved and displayed on the job page  
✅ **Wallet Integration** - Uses Interledger Open Payments for secure, cross-currency payments  
✅ **Payment Tracking** - Each payment has a unique ID for tracking and reconciliation  
✅ **User-Friendly UI** - Clear buttons and payment link display with copy-paste support  

## Files Changed

### Backend (Payments Service)
- `services/payments/src/workflow/paymentsService.ts` - Enhanced to return payment URLs
- `services/payments/src/web/routes_handlers.ts` - Updated API response format

### Backend (Django)
- `marketplace-py/jobs/models.py` - Added `payment_url` field to Job model
- `marketplace-py/jobs/views.py` - Updated `approve_quote` view to save payment URL
- `marketplace-py/jobs/payments_utils.py` - Enhanced to return payment URL
- `marketplace-py/jobs/migrations/0020_add_payment_url.py` - Database migration (auto-generated)

### Frontend
- `marketplace-py/templates/jobs/job_detail.html` - Enhanced UI to show payment link

### Documentation
- `docs/INTERLEDGER_PAYMENT_FLOW.md` - Complete technical documentation
- `services/payments/test-payment-flow.js` - Test script for verification

## Quick Start

### 1. Database Migration

The payment_url field has already been added to the database:

```bash
cd marketplace-py
uv run python manage.py migrate
```

✅ **Status**: Migration applied successfully

### 2. Start Services

#### Terminal 1: Payments Service
```bash
cd services/payments
npm run dev
```

The service should start on `http://localhost:4001`

#### Terminal 2: Django Application
```bash
cd marketplace-py
uv run python manage.py runserver
```

The app should start on `http://localhost:8000`

### 3. Test the Integration

#### Option A: Automated Test (Recommended)
```bash
cd services/payments
node test-payment-flow.js
```

This will verify:
- Payments service is running
- Quote creation endpoint works
- Payment URLs are generated correctly

#### Option B: Manual Test
1. Open browser to `http://localhost:8000`
2. Log in as a funder (job poster)
3. Navigate to any job detail page
4. Look for the "Approve Quote & Pay" section
5. Click "Approve quote & pay" button
6. System will:
   - Validate your wallet address
   - Create payment quote
   - Save payment URL to job
   - Redirect you to payment page
7. Return to job page to see the payment link displayed

## How It Works

```
┌─────────────────┐
│   Job Created   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User clicks "Approve Quote & Pay" │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Django validates wallet address  │
└────────┬─────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ POST /offers/:id/quotes/start       │
│ → Payments Service (Node.js)        │
│   1. Creates incoming payment       │
│   2. Creates quote                  │
│   3. Creates interactive grant      │
│   4. Returns payment URL            │
└────────┬────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Django saves payment_url to job │
└────────┬─────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User redirected to payment URL   │
│ (Interledger wallet)             │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ User authorizes payment          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Wallet redirects back            │
│ GET /payments/finish             │
│ → Payment completed              │
└──────────────────────────────────┘
```

## UI Changes

### Before Payment Initiated
```
┌──────────────────────────────────┐
│ 📋 Approve Quote & Pay           │
├──────────────────────────────────┤
│ Start the payment flow. You will │
│ be redirected to your wallet.    │
│                                   │
│ [Approve quote & pay] 🔊         │
└──────────────────────────────────┘
```

### After Payment Initiated
```
┌──────────────────────────────────┐
│ 📋 Approve Quote & Pay           │
├──────────────────────────────────┤
│ Payment link has been generated. │
│ Click below to complete payment. │
│                                   │
│ [Complete Payment] 🔊            │
│                                   │
│ ┌──────────────────────────────┐ │
│ │ Payment Link:                │ │
│ │ https://wallet.example.com/  │ │
│ │ interact/...                 │ │
│ └──────────────────────────────┘ │
│                                   │
│ Payment ID: 01HXXX...            │
└──────────────────────────────────┘
```

## Configuration

### Required Environment Variables

#### Payments Service (`.env`)
```bash
PORT=4001
BASE_URL=http://localhost:4001

SELLER_ID=seller-mvr5656
SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/mvr5656
SELLER_KEY_ID=fe775339-6ebc-4eb8-a4b4-0811acba3b62
SELLER_PRIVATE_KEY_PATH=./privates/mvr5656.key
```

#### Django (`marketplace-py/marketplace/settings.py`)
```python
PAYMENTS_SERVICE_URL = 'http://localhost:4001'
PAYMENTS_SELLER_ID = 'seller-mvr5656'
```

## Testing Checklist

- [ ] Payments service starts without errors
- [ ] Django server starts without errors
- [ ] Database migration applied
- [ ] Test script passes (run `node test-payment-flow.js`)
- [ ] Can view job detail page
- [ ] "Approve Quote & Pay" button is visible for job owner
- [ ] Clicking button generates payment link
- [ ] Payment link is displayed on job page
- [ ] Can click "Complete Payment" button
- [ ] Payment URL redirects to Interledger wallet

## Troubleshooting

### Payment link not generated

**Symptoms**: Button click doesn't create payment link

**Check**:
1. Is payments service running? (`http://localhost:4001/sellers` should return data)
2. Is wallet address configured in user profile?
3. Check Django console for error messages
4. Check payments service console for API call logs

### TypeScript compilation errors

**Solution**:
```bash
cd services/payments
npm run build
```

Any compilation errors will be shown. All files should compile successfully.

### Database migration fails

**Solution**:
```bash
cd marketplace-py
# Check current migration status
uv run python manage.py showmigrations jobs

# If migration needs to be applied
uv run python manage.py migrate jobs
```

## API Reference

### Create Payment Quote
```
POST /offers/:offerId/quotes/start
```

**Request Body:**
```json
{
  "sellerId": "seller-mvr5656",
  "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/buyer-wallet",
  "amount": "100.00"
}
```

**Response:**
```json
{
  "success": true,
  "redirectUrl": "https://wallet.example.com/interact/...",
  "paymentUrl": "https://wallet.example.com/interact/...",
  "pendingId": "01HXXX...",
  "incomingPaymentId": "https://ilp.interledger-test.dev/...",
  "quoteId": "https://ilp.interledger-test.dev/...",
  "amount": "100.00",
  "assetCode": "USD"
}
```

## Next Steps

1. **Test with Real Wallets**: Configure actual Interledger wallet addresses
2. **Add Payment Status Polling**: Auto-update UI when payment completes
3. **Implement Webhooks**: Receive notifications when payments complete
4. **Add Payment History**: Track all payment attempts for a job
5. **Multi-Seller Support**: Allow different sellers per job category

## Need Help?

- 📚 **Full Documentation**: See `docs/INTERLEDGER_PAYMENT_FLOW.md`
- 🧪 **Run Tests**: `cd services/payments && node test-payment-flow.js`
- 🔍 **Check Logs**: Both Django and Node.js services log all actions
- 🌐 **Interledger Docs**: https://openpayments.guide/

## Summary

This integration enables seamless payment flows using Interledger Open Payments. Every time a job needs funding, the system automatically generates a payment link that can be used to complete the transaction through the buyer's wallet.

**Status**: ✅ Integration complete and ready for testing
