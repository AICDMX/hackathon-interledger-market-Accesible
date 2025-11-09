# Interledger Payment Flow Integration

## Overview

This document describes the integration of Interledger Open Payments into the job marketplace, allowing funders to create payment quotes and receive payment links when they approve jobs.

## Architecture

### Components

1. **Django Backend (`marketplace-py/`)**
   - Job model with payment tracking fields
   - Payment utility functions for API communication
   - View logic for payment initiation

2. **Node.js Payments Service (`services/payments/`)**
   - Interledger Open Payments client
   - Quote and payment creation
   - Interactive grant flow management

### Data Flow

```
Job Created → User Clicks "Approve Quote & Pay" → 
Django calls payments service → 
Payments service creates:
  1. Incoming payment (seller receives)
  2. Quote (buyer pays)
  3. Interactive grant (buyer authorization) →
Response with payment URL → 
Django saves payment URL to job →
User redirected to payment URL →
Buyer authorizes at their wallet →
Payment completed
```

## Key Files Modified/Created

### 1. Payments Service

#### `services/payments/src/workflow/paymentsService.ts`
- Enhanced `startQuoteFlow()` to return comprehensive payment details including:
  - `redirectUrl`: URL to redirect buyer for payment authorization
  - `paymentUrl`: Same as redirectUrl for compatibility
  - `pendingId`: Unique payment transaction ID
  - `incomingPaymentId`: Interledger incoming payment ID
  - `quoteId`: Interledger quote ID
  - Payment amount and asset information

#### `services/payments/src/web/routes_handlers.ts`
- Updated `startQuote()` handler to return enhanced payment response

### 2. Django Backend

#### `marketplace-py/jobs/models.py`
- Added `payment_url` field to `Job` model:
  ```python
  payment_url = models.URLField(
      max_length=500,
      blank=True,
      null=True,
      verbose_name=_('Payment URL'),
      help_text=_('Interledger payment redirect URL for buyer to complete payment')
  )
  ```

#### `marketplace-py/jobs/payments_utils.py`
- Enhanced `start_quote()` to return:
  - `redirect_url`: Primary redirect URL
  - `payment_url`: Payment link URL
  - `pending_id`: Transaction tracking ID

#### `marketplace-py/jobs/views.py`
- Updated `approve_quote()` view to:
  1. Create payment quote via payments service
  2. Save `payment_url` and `payment_id` to job
  3. Log payment initiation
  4. Display success message
  5. Redirect user to payment URL

### 3. Templates

#### `marketplace-py/templates/jobs/job_detail.html`
- Enhanced "Approve Quote & Pay" section with conditional logic:
  - **Before payment initiated**: Shows "Approve quote & pay" button
  - **After payment initiated**: Shows:
    - "Complete Payment" button linking to payment URL
    - Payment link display box (copyable)
    - Payment ID for tracking

## Usage Flow

### For Job Funders (Buyers)

1. **Create a Job**
   - Post a new job with budget and requirements
   - Job is created in draft status

2. **Approve Quote & Pay**
   - Navigate to job detail page
   - Click "Approve quote & pay" button
   - System validates wallet address
   - Payment service creates quote and generates payment URL
   - User is redirected to their Interledger wallet

3. **Complete Payment**
   - Authorize payment at wallet provider
   - Wallet redirects back to marketplace
   - Payment is finalized via continuation grant

4. **View Payment Status**
   - Job detail page shows payment link and ID
   - "Complete Payment" button allows re-access to payment URL
   - Payment link can be shared or saved for later

### API Endpoints

#### POST `/offers/:offerId/quotes/start`

Creates a payment quote for a job.

**Request:**
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
  "redirectUrl": "https://wallet.interledger-test.dev/interact/...",
  "paymentUrl": "https://wallet.interledger-test.dev/interact/...",
  "pendingId": "01HXXX...",
  "incomingPaymentId": "https://ilp.interledger-test.dev/...",
  "quoteId": "https://ilp.interledger-test.dev/...",
  "amount": "100.00",
  "assetCode": "USD"
}
```

#### GET `/payments/finish`

Completes payment after user authorization.

**Query Parameters:**
- `pendingId`: Payment transaction ID
- `interact_ref`: Interaction reference from wallet
- `hash`: Security hash from wallet

## Testing

### Prerequisites

1. **Wallet Setup**
   - Test wallet addresses configured (see `services/payments/index.js`)
   - Private keys available in `services/payments/privates/`
   - Seller configuration in environment variables

2. **Services Running**
   ```bash
   # Terminal 1: Django
   cd marketplace-py
   uv run python manage.py runserver
   
   # Terminal 2: Payments Service
   cd services/payments
   npm run dev
   ```

3. **Database Migrated**
   ```bash
   cd marketplace-py
   uv run python manage.py migrate
   ```

### Test Scenario

1. **Create Test Job**
   - Log in as funder
   - Navigate to "Post a Job"
   - Fill in job details with budget (e.g., 100 pesos)
   - Save job

2. **Initiate Payment**
   - View job detail page
   - Verify "Approve Quote & Pay" section is visible
   - Click "Approve quote & pay" button
   - Verify redirection to Interledger wallet

3. **Verify Payment Link**
   - Return to job detail page (after authorization or by navigating back)
   - Verify "Complete Payment" button is displayed
   - Verify payment link is shown in read-only box
   - Verify payment ID is displayed
   - Click "Complete Payment" to re-access payment URL

4. **Check Database**
   ```python
   from jobs.models import Job
   job = Job.objects.get(pk=YOUR_JOB_ID)
   print(job.payment_url)  # Should show Interledger URL
   print(job.payment_id)   # Should show pending ID
   ```

### Testing with Mock Wallets

For testing without real wallet interaction:

1. **Check Payment Service Logs**
   ```bash
   cd services/payments
   npm run dev
   # Watch console for quote creation logs
   ```

2. **Verify Payment Creation**
   ```bash
   curl http://localhost:4001/payments/pending
   # Should show list of pending payments
   ```

3. **Test Payment Status**
   ```bash
   curl http://localhost:4001/payments/{pendingId}/status
   ```

## Configuration

### Environment Variables

#### Payments Service (`.env`)
```bash
PORT=4001
BASE_URL=http://localhost:4001

# Seller Configuration
SELLER_ID=seller-mvr5656
SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/mvr5656
SELLER_KEY_ID=fe775339-6ebc-4eb8-a4b4-0811acba3b62
SELLER_PRIVATE_KEY_PATH=./privates/mvr5656.key
```

#### Django (`settings.py`)
```python
PAYMENTS_SERVICE_URL = 'http://localhost:4001'
PAYMENTS_SELLER_ID = 'seller-mvr5656'
```

## Security Considerations

1. **Private Keys**: Never commit private keys to version control
2. **HTTPS**: Use HTTPS in production for all payment URLs
3. **Wallet Validation**: Wallet addresses are validated before payment creation
4. **Hash Verification**: Payment completion includes hash verification (implement in production)
5. **CSRF Protection**: Django CSRF tokens protect payment initiation endpoints

## Future Enhancements

1. **Payment Status Polling**: Auto-update UI when payment is completed
2. **Webhook Integration**: Receive payment completion notifications
3. **Multiple Sellers**: Support multiple seller accounts
4. **Payment History**: Track all payment attempts and completions
5. **Refund Support**: Add refund functionality for canceled jobs
6. **Multi-currency**: Support various asset codes beyond USD/pesos

## Troubleshooting

### Payment Link Not Generated

**Check:**
- Payments service is running (`npm run dev` in `services/payments/`)
- Django can reach payments service (check `PAYMENTS_SERVICE_URL`)
- User has wallet address configured in profile
- Wallet address is valid Interledger address

**Logs:**
```bash
# Django logs
cd marketplace-py
uv run python manage.py runserver
# Check console for errors

# Payments service logs
cd services/payments
npm run dev
# Check console for API calls
```

### Redirect Fails

**Check:**
- `BASE_URL` is correctly set in payments service `.env`
- Finish URL is accessible from wallet provider
- Interactive grant is properly configured

### Payment Not Completing

**Check:**
- Buyer wallet has sufficient funds
- Grant continuation is working
- Check pending payment status via API

## References

- [Interledger Open Payments Spec](https://openpayments.guide/)
- [Open Payments Node SDK](https://github.com/interledger/open-payments-node)
- [Peer-to-Peer Example](https://github.com/interledger/open-payments-node/blob/main/examples/peer-to-peer/index.js)
