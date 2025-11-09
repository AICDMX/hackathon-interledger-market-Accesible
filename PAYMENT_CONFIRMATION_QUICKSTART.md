# Payment Confirmation - Quick Start

## TL;DR

Your system now receives payment confirmations via **two channels**:

1. **Webhook** (background): Payments service → Django `/api/webhooks/payments`
2. **Redirect** (UX): Wallet → Django `/payments/finish` → Job detail page

## Quick Setup (3 steps)

### 1. Set Environment Variables

**In `services/payments/.env`:**
```bash
BASE_URL=http://localhost:4001         # Your payments service URL
DJANGO_BASE_URL=http://web:8000        # Your Django URL
```

### 2. Verify Endpoints Work

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/webhooks/payments \
  -H "Content-Type: application/json" \
  -d '{"type":"payment.completed","pendingId":"test","offerId":"1","status":"paid","timestamp":"2025-01-09T00:00:00Z"}'

# Should return: {"success": true, "message": "Payment confirmed", ...}
```

### 3. Test Full Flow

1. Create a job in Django
2. Pre-approve payment (job funder)
3. Buyer pays via Interledger wallet
4. Wallet redirects to `/payments/finish`
5. Django shows confirmation + updates job status
6. Webhook fires in background to ensure consistency

## What Happens When Payment Completes

### Automatic Actions

1. **Payments service** calls `notifyDjango()` webhook
2. **Django webhook handler** (`jobs/webhooks.py`):
   - Updates `job.payment_id`
   - Sets `job.contract_completed = True`
   - Changes `job.status` to `complete` (if in reviewing)
3. **Wallet redirects** user to Django `/payments/finish`
4. **Django redirect handler** (`jobs/views.py`):
   - Proxies to payments service to finalize grant
   - Shows success message
   - Redirects to job detail page

### Result
✅ Job marked as paid and complete  
✅ User sees confirmation  
✅ Background webhook ensures consistency  

## Files Created

```
marketplace-py/
├── jobs/
│   ├── webhooks.py              # NEW - Webhook handler
│   ├── views.py                 # MODIFIED - Added payments_finish()
│   └── urls.py                  # MODIFIED - Added /payments/finish route
├── marketplace/
│   └── urls.py                  # MODIFIED - Added /api/webhooks/payments
└── templates/jobs/
    └── payment_finish.html      # NEW - Confirmation page
```

## Testing Commands

```bash
# Simulate webhook
curl -X POST http://localhost:8000/api/webhooks/payments \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment.completed",
    "pendingId": "test-123",
    "offerId": "1",
    "status": "paid",
    "outgoingPaymentId": "https://ilp.interledger-test.dev/out/xyz",
    "timestamp": "2025-01-09T12:00:00Z"
  }'

# Check payment service logs
docker compose logs payments | grep webhook

# Check Django logs
docker compose logs web | grep webhook
```

## Troubleshooting

### Webhook not firing?
- Check `DJANGO_BASE_URL` is set in payments service
- Verify Django is accessible: `curl http://web:8000/api/webhooks/payments`

### Redirect not working?
- Check `BASE_URL` is set in payments service
- Verify wallet can reach finish URL

### Job not updating?
- Check `offerId` matches job primary key
- Look for errors in Django logs: `docker compose logs web`

## Full Documentation

See [PAYMENT_CONFIRMATION_SETUP.md](./PAYMENT_CONFIRMATION_SETUP.md) for complete details.

## Architecture Diagram

```
┌─────────────┐
│   Buyer     │
│   Wallet    │
└──────┬──────┘
       │ 1. Authorize payment
       ↓
┌─────────────────┐
│   Payments      │
│   Service       │
└──────┬──────────┘
       │ 2. Send webhook
       ↓
┌─────────────────┐      3. Redirect user      ┌──────────────┐
│    Django       │◄─────────────────────────────│    Wallet    │
│   /api/webhooks │                              └──────────────┘
│   /payments     │
└──────┬──────────┘
       │ 4. Update job status
       ↓
┌─────────────────┐
│  Job Detail     │
│  (Complete)     │
└─────────────────┘
```

## Next Steps

1. ✅ **Setup complete** - Both endpoints working
2. 🔒 **Add webhook authentication** - Secure with shared secret
3. 🔄 **Add retry logic** - Retry failed webhooks
4. 📧 **Add notifications** - Email on payment completion
5. 📊 **Add audit trail** - Log all payment events

---

**Ready to test?** Create a job and complete a payment to see the flow in action! 🚀
