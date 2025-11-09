# Payment Confirmation Setup

This guide explains how payment confirmations are received in the Django marketplace after a buyer completes an Interledger payment.

## Overview

The system uses **two methods** to receive payment confirmations:

1. **Webhook notifications** (backend-to-backend) - Most reliable
2. **Redirect callbacks** (wallet → Django) - Immediate UX feedback

## 1. Webhook Notifications (Background)

### How it works
When a payment completes in the payments service, it automatically sends a webhook to Django:

```
Payments Service → Django Webhook Endpoint
```

### Setup

#### Step 1: Configure environment variable
In your payments service `.env` file:
```bash
DJANGO_BASE_URL=http://web:8000
```

For local development:
```bash
DJANGO_BASE_URL=http://localhost:8000
```

#### Step 2: Webhook endpoint (already created)
Django endpoint: `POST /api/webhooks/payments`

Location: `marketplace-py/jobs/webhooks.py`

### Webhook payload
```json
{
  "type": "payment.completed",
  "pendingId": "01HZZ...",
  "offerId": "123",
  "status": "paid",
  "outgoingPaymentId": "https://...",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### What it does
- Looks up the job by `offerId`
- Updates `job.payment_id` and `job.contract_completed = True`
- If job status is `reviewing`, changes it to `complete`
- Logs the confirmation

## 2. Redirect Callback (Immediate UX)

### How it works
After the buyer authorizes payment in their wallet, the wallet redirects back:

```
Wallet → Django → Payments Service → Job Detail Page
```

### Setup

#### Step 1: Configure BASE_URL
In payments service `.env`:
```bash
BASE_URL=http://localhost:4001
```

For production (use ngrok or your domain):
```bash
BASE_URL=https://your-domain.com
```

#### Step 2: Redirect endpoint (already created)
Django endpoint: `GET /payments/finish`

Location: `marketplace-py/jobs/views.py` → `payments_finish()`

### Query parameters
```
?pendingId=01HZZ...&interact_ref=abc123&hash=xyz789
```

### What it does
1. Receives redirect from wallet
2. Proxies to payments service `/payments/finish` to complete grant
3. Fetches payment status
4. Redirects to job detail page with success/error message
5. Shows confirmation page if job not found

## Testing

### Test webhook locally

```bash
# Simulate webhook from payments service
curl -X POST http://localhost:8000/api/webhooks/payments \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment.completed",
    "pendingId": "test-123",
    "offerId": "1",
    "status": "paid",
    "outgoingPaymentId": "https://ilp.interledger-test.dev/outgoing/xyz",
    "timestamp": "2025-01-09T12:00:00Z"
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Payment confirmed",
  "job_id": 1,
  "job_status": "complete"
}
```

### Test redirect callback

```bash
# Simulate wallet redirect (note: won't actually complete payment without real interact_ref)
curl "http://localhost:8000/payments/finish?pendingId=test-123&interact_ref=abc&hash=xyz"
```

## Architecture Flow

### Complete payment flow

```
1. Buyer approves payment in wallet
   ↓
2. Wallet redirects to Django /payments/finish
   ↓
3. Django proxies to payments service /payments/finish
   ↓
4. Payments service:
   - Continues grant with wallet
   - Creates outgoing payment
   - Updates pending status to "paid"
   - Sends webhook to Django
   ↓
5. Django webhook handler:
   - Updates job.contract_completed = True
   - Changes job status to "complete"
   ↓
6. Django redirect handler:
   - Shows success message
   - Redirects to job detail page
```

## File Reference

### Django Files Created/Modified
- `marketplace-py/jobs/webhooks.py` - Webhook handler
- `marketplace-py/jobs/views.py` - Added `payments_finish()` view
- `marketplace-py/jobs/urls.py` - Added `/payments/finish` route
- `marketplace-py/marketplace/urls.py` - Added `/api/webhooks/payments` route
- `marketplace-py/templates/jobs/payment_finish.html` - Confirmation page template

### Payments Service Files (Reference)
- `services/payments/src/workflow/webhookNotifier.ts` - Sends webhook to Django
- `services/payments/src/workflow/paymentsService.ts` - Calls `notifyDjango()` on completion
- `services/payments/src/web/routes_handlers.ts` - `/payments/finish` endpoint

## Configuration Summary

### Required Environment Variables

**Payments Service** (`services/payments/.env`):
```bash
BASE_URL=http://localhost:4001          # For redirect finish URL
DJANGO_BASE_URL=http://web:8000         # For webhook notifications
```

**Django** (`marketplace-py/.env` or `settings.py`):
```python
PAYMENTS_SERVICE_URL = "http://payments:4001"  # Or http://localhost:4001
```

## Troubleshooting

### Webhooks not received
1. Check `DJANGO_BASE_URL` is set in payments service
2. Verify Django is accessible from payments service container
3. Check Django logs: `docker compose logs web`
4. Verify endpoint responds: `curl http://localhost:8000/api/webhooks/payments`

### Redirect callback fails
1. Check `BASE_URL` is set in payments service
2. Verify wallet can reach the finish URL
3. Check for CORS issues in browser console
4. Verify `PAYMENTS_SERVICE_URL` in Django settings

### Payment status not updating
1. Check if webhook fired: look for `[webhook]` in payments service logs
2. Verify job exists: `offerId` must match job primary key
3. Check Django logs for errors in webhook handler
4. Manually query status: `curl http://localhost:4001/payments/{pendingId}/status`

## Next Steps

1. **Add authentication**: Secure webhook endpoint with shared secret
2. **Retry logic**: Implement webhook retry on failure
3. **Status polling**: Add frontend polling as fallback
4. **Notifications**: Email/SMS notifications on payment completion
5. **Audit trail**: Log all payment state changes

## Security Considerations

- **CSRF exempt**: Webhook endpoint is CSRF-exempt (external service)
- **Validation**: Always validate `offerId` maps to real job
- **Idempotency**: Webhook handler is safe to call multiple times
- **Authentication**: TODO - Add webhook signature verification

## References

- [Interledger Open Payments Docs](https://openpayments.guide/)
- [Services README](./services/payments/README.md)
- [Django Integration Guide](./services/payments/DJANGO_INTEGRATION.md)
