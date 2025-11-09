# Quick Start Guide

Get the Payments Service running with Django in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Interledger test wallet account
- Private key file for your wallet

## Step 1: Configure Payments Service (2 min)

```bash
cd services/payments

# Copy environment template
cp .env.example .env

# Edit .env with your wallet details
nano .env
```

Update these values in `.env`:
```bash
SELLER_WALLET_ADDRESS_URL=https://ilp.interledger-test.dev/YOUR_WALLET
SELLER_KEY_ID=your-key-id-here
SELLER_PRIVATE_KEY_PATH=./privates/your-wallet.key
DJANGO_BASE_URL=http://web:8000
```

## Step 2: Add Private Key (1 min)

```bash
# Create privates directory
mkdir -p privates

# Copy your wallet private key
cp /path/to/your-wallet.key privates/

# Secure it
chmod 600 privates/*.key
```

## Step 3: Start Services (1 min)

From the repository root:

```bash
# Start both Django and Payments services
docker compose up web payments

# Or in detached mode
docker compose up -d web payments
```

## Step 4: Verify Setup (1 min)

### Test Payments Service

```bash
# Health check
curl http://localhost:4001/health

# Expected: {"status": "ok", "service": "payments", ...}

# Check seller registered
curl http://localhost:4001/sellers | jq

# Expected: {"sellers": [{"id": "default-seller", ...}]}
```

### Test Django Connection

```bash
# From Django shell
docker compose exec web uv run python manage.py shell
```

```python
import requests
response = requests.get('http://payments:3000/health')
print(response.json())
# Should show: {'status': 'ok', 'service': 'payments', ...}
```

## Step 5: Test Payment Flow (Optional)

### Start a Quote

```bash
curl -X POST http://localhost:4001/offers/test-job-123/quotes/start \
  -H "Content-Type: application/json" \
  -d '{
    "sellerId": "default-seller",
    "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/BUYER_WALLET",
    "amount": "100"
  }'
```

Expected response:
```json
{
  "pendingId": "01JCEXAMPLE...",
  "redirectUrl": "https://ilp.interledger-test.dev/interact/..."
}
```

Visit the `redirectUrl` in a browser to approve the payment!

---

## 🎉 You're Done!

The Payments Service is now running and integrated with Django.

## Next Steps

### 1. Add Webhook Handler to Django

Create `marketplace-py/jobs/views_webhooks.py`:

```python
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from jobs.models import Job

@csrf_exempt
def payment_webhook(request):
    data = json.loads(request.body)
    if data['type'] == 'payment.completed':
        job = Job.objects.get(pk=data['offerId'])
        job.is_funded = True
        job.save()
    return JsonResponse({'ok': True})
```

Add to `marketplace-py/marketplace/urls.py`:
```python
from jobs import views_webhooks

urlpatterns = [
    # ... existing patterns ...
    path('api/webhooks/payments', views_webhooks.payment_webhook),
]
```

### 2. Add Payment Button to Job Detail

In your job detail template:
```html
<form method="post" action="{% url 'jobs:fund_job' job.id %}">
  {% csrf_token %}
  <button class="btn btn-primary">Fund This Job (${{ job.budget }})</button>
</form>
```

### 3. Create Fund View

```python
from jobs.payments_utils import start_quote

@login_required
def fund_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    result = start_quote(
        offer_id=job.id,
        seller_id='default-seller',
        buyer_wallet_address_url=request.user.wallet_address,
        amount=str(job.budget)
    )
    if result['success']:
        return redirect(result['redirect_url'])
    else:
        messages.error(request, result['error'])
        return redirect('jobs:detail', pk=job_id)
```

---

## 🔍 Troubleshooting

### Service won't start

**Check logs:**
```bash
docker compose logs payments
```

**Common issues:**
- Private key file not found → Check path in `.env`
- Port already in use → Stop other services on port 3000/4001
- Invalid wallet credentials → Verify SELLER_* env vars

### Health check fails

```bash
# Check service is running
docker compose ps

# Check network
docker compose exec web ping payments

# Restart service
docker compose restart payments
```

### Seller not registered

```bash
# Manually register seller
curl -X POST http://localhost:4001/sellers \
  -H "Content-Type: application/json" \
  -d '{
    "id": "default-seller",
    "walletAddressUrl": "https://ilp.interledger-test.dev/YOUR_WALLET",
    "keyId": "your-key-id",
    "privateKeyPath": "./privates/your-wallet.key"
  }'
```

---

## 📚 Documentation

- **API Reference**: [API.md](./API.md)
- **Django Integration**: [DJANGO_INTEGRATION.md](./DJANGO_INTEGRATION.md)
- **Full Details**: [README.md](./README.md)
- **Changes Made**: [IMPROVEMENTS.md](./IMPROVEMENTS.md)

---

## 💬 Need Help?

1. Check the logs: `docker compose logs payments`
2. Verify environment: `cat .env`
3. Test endpoints: `curl http://localhost:4001/health`
4. Review documentation in this directory

---

## ✅ Checklist

- [ ] `.env` file configured
- [ ] Private key added to `privates/`
- [ ] Services started with docker compose
- [ ] Health check returns OK
- [ ] Seller registered and visible
- [ ] Django webhook endpoint created
- [ ] Payment flow tested

All checked? You're ready to process payments! 🚀
