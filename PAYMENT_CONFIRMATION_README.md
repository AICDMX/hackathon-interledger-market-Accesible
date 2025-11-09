# Payment Confirmation Feature

## What is this?

Your Django marketplace now automatically receives payment confirmations after buyers complete Interledger payments.

## How does it work?

### Two ways to confirm payments:

1. **🔔 Webhooks** (Background, automatic)
   - Payments service sends notification to Django
   - Django updates job status automatically
   - Most reliable method

2. **🔄 Redirects** (User-facing, immediate)
   - Wallet redirects user back to Django
   - User sees confirmation message
   - Best user experience

## Quick Start

### 1. Configure environment

Edit `services/payments/.env`:
```bash
DJANGO_BASE_URL=http://web:8000
BASE_URL=http://localhost:4001
```

### 2. Test the setup

```bash
./test_payment_confirmation.sh
```

### 3. Try a real payment

1. Create a job as a funder
2. Pre-approve payment
3. Have a buyer pay via wallet
4. Watch the magic happen! ✨

## What gets updated?

When payment completes:
- ✅ `job.payment_id` = payment transaction ID
- ✅ `job.contract_completed` = `True`
- ✅ `job.status` = `'complete'`

## Endpoints

### Webhook endpoint
```
POST /api/webhooks/payments
```
Receives payment notifications from payments service.

### Redirect endpoint
```
GET /payments/finish
```
Handles user redirect after wallet authorization.

## Documentation

- 📖 **[Quick Start](PAYMENT_CONFIRMATION_QUICKSTART.md)** - Get started in 5 minutes
- 📚 **[Full Setup](PAYMENT_CONFIRMATION_SETUP.md)** - Complete configuration guide
- 🔧 **[Implementation](PAYMENT_CONFIRMATION_IMPLEMENTATION.md)** - Technical details

## Testing

### Manual webhook test
```bash
curl -X POST http://localhost:8000/api/webhooks/payments \
  -H "Content-Type: application/json" \
  -d '{
    "type": "payment.completed",
    "pendingId": "test-123",
    "offerId": "1",
    "status": "paid",
    "timestamp": "2025-01-09T12:00:00Z"
  }'
```

### Check logs
```bash
# Django logs
docker compose logs web | grep webhook

# Payments service logs
docker compose logs payments | grep webhook
```

## Troubleshooting

### Payments not updating?

1. **Check environment variables**
   ```bash
   grep DJANGO_BASE_URL services/payments/.env
   ```

2. **Test webhook endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/webhooks/payments
   ```

3. **Check logs for errors**
   ```bash
   docker compose logs web | tail -n 50
   ```

### Still having issues?

See the [Full Setup Guide](PAYMENT_CONFIRMATION_SETUP.md) for detailed troubleshooting.

## Architecture

```
Buyer → Wallet → Payments Service → Django
                       ↓
                   Webhook (background)
                       ↓
                 Update job status
```

## Files

### Created
- `marketplace-py/jobs/webhooks.py`
- `marketplace-py/templates/jobs/payment_finish.html`
- `test_payment_confirmation.sh`

### Modified
- `marketplace-py/jobs/views.py`
- `marketplace-py/jobs/urls.py`
- `marketplace-py/marketplace/urls.py`

## Security

- ✅ Input validation
- ✅ CSRF protection (exempt for webhooks)
- ✅ Error handling
- ⚠️ TODO: Add webhook signature verification

## Next Steps

1. ✅ Basic confirmation working
2. 🔒 Add webhook authentication
3. 🔄 Add retry logic
4. 📧 Email notifications
5. 📊 Payment analytics

---

**Need help?** Check the documentation or run `./test_payment_confirmation.sh` to diagnose issues.
