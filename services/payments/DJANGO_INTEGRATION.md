# Django Integration Guide

This guide explains how to integrate the Payments Service with your Django marketplace application.

## Overview

The Payments Service handles Interledger Open Payments flows while Django manages the marketplace logic. Communication happens via REST API and webhooks.

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌────────────────┐
│   Django    │◄───────►│ Payments Service │◄───────►│ Interledger    │
│ Marketplace │  REST   │   (Node.js)      │  GNAP   │    Wallet      │
└─────────────┘         └──────────────────┘         └────────────────┘
      │                          │
      │                          │
      └──────── Webhook ─────────┘
           (payment.completed)
```

## Setup

### 1. Configure Django Settings

Add to `marketplace/settings.py`:

```python
# Payments service configuration
PAYMENTS_SERVICE_URL = os.environ.get('PAYMENTS_SERVICE_URL', 'http://payments:3000')
```

### 2. Environment Variables

In your Django `.env` or docker-compose:

```bash
PAYMENTS_SERVICE_URL=http://payments:3000  # Docker internal
# Or for local development:
# PAYMENTS_SERVICE_URL=http://localhost:4001
```

### 3. Verify Connection

The `payments_utils.py` module is already set up. Test the connection:

```python
import requests
from django.conf import settings

response = requests.get(f'{settings.PAYMENTS_SERVICE_URL}/health')
print(response.json())  # Should show {"status": "ok", "service": "payments", ...}
```

## Payment Flow Integration

### Step 1: Initiate Payment (Django View)

When a user wants to fund a job:

```python
from django.shortcuts import redirect
from django.contrib import messages
from jobs.payments_utils import start_quote

@login_required
def fund_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    
    # Ensure user has wallet address
    if not request.user.wallet_address:
        messages.error(request, 'Please add your Interledger wallet address to your profile.')
        return redirect('users:profile')
    
    # Start payment quote
    result = start_quote(
        offer_id=job.id,
        seller_id='default-seller',  # Or configure dynamically
        buyer_wallet_address_url=request.user.wallet_address,
        amount=str(job.budget)
    )
    
    if result['success']:
        # Store pendingId for tracking
        pending_id = result['data'].get('pendingId')
        # Optional: Save to session or database
        request.session['pending_payment_id'] = pending_id
        request.session['pending_job_id'] = job.id
        
        # Redirect to wallet for approval
        return redirect(result['redirect_url'])
    else:
        messages.error(request, f"Payment failed: {result['error']}")
        return redirect('jobs:detail', pk=job.id)
```

### Step 2: Add URL Pattern

Add to `jobs/urls.py`:

```python
urlpatterns = [
    # ... existing patterns ...
    path('<int:job_id>/fund/', views.fund_job, name='fund_job'),
]
```

### Step 3: Add Fund Button to Template

In `jobs/job_detail.html`:

```html
{% if job.status == 'recruiting' and user.is_authenticated and user != job.funder %}
  <form method="post" action="{% url 'jobs:fund_job' job.id %}">
    {% csrf_token %}
    <button type="submit" class="btn btn-primary">
      Fund Job (${{ job.budget }})
    </button>
  </form>
{% endif %}
```

## Webhook Integration

### Step 1: Create Webhook Handler

Create `jobs/views_webhooks.py`:

```python
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from jobs.models import Job
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def payment_webhook(request):
    """
    Receive payment completion notifications from Payments Service.
    
    Event types:
    - payment.completed: Payment successfully processed
    - payment.failed: Payment failed
    """
    try:
        data = json.loads(request.body)
        event_type = data.get('type')
        
        logger.info(f"Received webhook: {event_type} - {data}")
        
        if event_type == 'payment.completed':
            handle_payment_completed(data)
        elif event_type == 'payment.failed':
            handle_payment_failed(data)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
        
        return JsonResponse({'ok': True})
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def handle_payment_completed(data):
    """Process successful payment."""
    offer_id = data.get('offerId')
    pending_id = data.get('pendingId')
    outgoing_payment_id = data.get('outgoingPaymentId')
    
    try:
        job = Job.objects.get(pk=offer_id)
        
        # Update job status
        job.is_funded = True
        job.payment_id = outgoing_payment_id
        
        # If job was recruiting, move to selecting
        if job.status == 'recruiting':
            job.status = 'selecting'
        
        job.save()
        
        logger.info(f"Job {offer_id} funded successfully. Payment ID: {outgoing_payment_id}")
        
        # Optional: Send notification to job owner
        # from django.core.mail import send_mail
        # send_mail(
        #     'Job Funded',
        #     f'Your job "{job.title}" has been funded.',
        #     'noreply@example.com',
        #     [job.funder.email],
        # )
        
    except Job.DoesNotExist:
        logger.error(f"Job {offer_id} not found for payment {pending_id}")
    except Exception as e:
        logger.error(f"Error handling payment completion: {str(e)}")


def handle_payment_failed(data):
    """Process failed payment."""
    offer_id = data.get('offerId')
    pending_id = data.get('pendingId')
    
    logger.warning(f"Payment failed for job {offer_id}, pending ID: {pending_id}")
    
    # Optional: Update job status, notify user, etc.
```

### Step 2: Add Webhook URL

Add to `marketplace/urls.py`:

```python
from jobs import views_webhooks

urlpatterns = [
    # ... existing patterns ...
    path('api/webhooks/payments', views_webhooks.payment_webhook, name='payment_webhook'),
]
```

### Step 3: Test Webhook Locally

For local development, use ngrok or similar to expose your Django server:

```bash
ngrok http 8000
```

Then update the Payments Service `.env`:

```bash
DJANGO_BASE_URL=https://your-ngrok-url.ngrok.io
```

## Payment Status Queries

### Check Payment Status

```python
import requests
from django.conf import settings

def get_payment_status(pending_id):
    """Query payment status from Payments Service."""
    try:
        url = f'{settings.PAYMENTS_SERVICE_URL}/payments/{pending_id}/status'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return None

# Usage
status = get_payment_status(pending_id)
if status:
    print(f"Payment status: {status['status']}")
    print(f"Outgoing payment: {status.get('outgoingPaymentId')}")
```

### Get All Payments for a Job

```python
def get_job_payments(job_id):
    """Get all payment attempts for a job."""
    try:
        url = f'{settings.PAYMENTS_SERVICE_URL}/offers/{job_id}/payments'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()['payments']
        else:
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching job payments: {str(e)}")
        return []
```

## User Model Extension

Add wallet address field to your User model:

```python
# users/models.py
class User(AbstractUser):
    # ... existing fields ...
    wallet_address = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Interledger wallet address URL (e.g., https://ilp.interledger-test.dev/username)'
    )
```

Create and run migration:

```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Add to user profile form:

```python
# users/forms.py
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['wallet_address', 'email', ...]
```

## Pre-Approved Payments (Escrow)

For the escrow flow where the job owner pre-funds:

```python
from jobs.payments_utils import create_incoming_payment

@login_required
@require_POST
def pre_fund_job(request, job_id):
    """Job owner creates pre-approved payment for selected workers."""
    job = get_object_or_404(Job, pk=job_id, funder=request.user)
    
    if job.status != 'selecting':
        messages.error(request, 'Job must be in selecting phase.')
        return redirect('jobs:view_applications', pk=job_id)
    
    selected_count = job.applications.filter(status='selected').count()
    
    if selected_count == 0:
        messages.error(request, 'Please select workers first.')
        return redirect('jobs:view_applications', pk=job_id)
    
    # Calculate total amount
    total_amount = job.budget * selected_count
    
    result = create_incoming_payment(
        amount=str(total_amount),
        description=f'Escrow for job: {job.title}'
    )
    
    if result['success']:
        job.escrow_payment_id = result['payment_id']
        job.status = 'submitting'
        job.save()
        
        messages.success(request, 'Escrow payment created. Workers can now submit work.')
        return redirect('jobs:view_applications', pk=job_id)
    else:
        messages.error(request, f"Escrow creation failed: {result['error']}")
        return redirect('jobs:view_applications', pk=job_id)
```

## Testing

### Manual Testing with curl

```bash
# Test start quote
curl -X POST http://localhost:4001/offers/123/quotes/start \
  -H "Content-Type: application/json" \
  -d '{
    "sellerId": "default-seller",
    "buyerWalletAddressUrl": "https://ilp.interledger-test.dev/buyer",
    "amount": "100"
  }'

# Test payment status
curl http://localhost:4001/payments/{pendingId}/status
```

### Django Shell Testing

```python
# Start Django shell
uv run python manage.py shell

# Test connection
from jobs.payments_utils import start_quote
result = start_quote(
    offer_id='test-123',
    seller_id='default-seller',
    buyer_wallet_address_url='https://ilp.interledger-test.dev/buyer',
    amount='100'
)
print(result)
```

## Troubleshooting

### Payment Service Unreachable

```python
# Check in Django shell
import requests
from django.conf import settings

try:
    r = requests.get(f'{settings.PAYMENTS_SERVICE_URL}/health', timeout=5)
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
```

**Solutions:**
- Verify `PAYMENTS_SERVICE_URL` is correct
- Check both services are running: `docker compose ps`
- Check network connectivity in docker: `docker network inspect hackathon-interledger-market-accesible_default`

### Webhook Not Received

- Check Django logs: `docker compose logs web`
- Verify webhook endpoint exists: `curl -X POST http://localhost:8000/api/webhooks/payments -d '{"test": true}'`
- Check `DJANGO_BASE_URL` in Payments Service
- Ensure CSRF exemption on webhook endpoint

### "seller not found" Error

- Register a seller in Payments Service first
- Or configure `SELLER_ID` and related env vars for auto-registration

## Production Considerations

1. **Authentication**: Add API key authentication to webhook endpoint
2. **Retry Logic**: Implement retry mechanism for failed API calls
3. **Idempotency**: Handle duplicate webhook deliveries
4. **Monitoring**: Log all payment events for audit trail
5. **Error Handling**: Show user-friendly error messages
6. **Security**: Always use HTTPS in production

## Example: Complete Payment Flow

1. User clicks "Fund Job" button
2. Django calls `start_quote()` → Payments Service
3. Payments Service creates incoming payment, quote, and grant
4. Django redirects user to wallet
5. User approves payment in their wallet
6. Wallet redirects to Payments Service `/payments/finish`
7. Payments Service completes payment
8. Payments Service sends webhook to Django
9. Django updates job status and notifies users

## Additional Resources

- [Payments Service API Documentation](./API.md)
- [Interledger Documentation](https://interledger.org/developers/get-started/)
- [Open Payments Specification](https://openpayments.guide/)
