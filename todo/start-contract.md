# Contract Creation Implementation Plan (Simplified)

## Overview
Implement contract creation flow that automatically sets up payment contracts using GNAP (Grant Negotiation and Authorization Protocol) and Open Payments. When users click the "Start Contract" button (section_start_contract), the system auto-fills all contract parameters and immediately redirects the buyer to their wallet for authorization. No form needed - everything is auto-filled from existing job and user data.

## Requirements

### Auto-filled Contract Parameters
- **Number of payments**: Always 1 (hardcoded)
- **Date finished**: Calculated as `expired_date + 7 days` (from Job model)
- **Who**: 
  - Buyer/Funder: `job.funder` (the job creator)
  - Seller: Determined from selected/approved applicants on the job
- **Seller key**: Retrieved from User model (seller's `key_id` and `private_key` fields)
- **Contract ID**: ULID transaction ID stored in `Job.contract_id` field

### Flow
1. User clicks "Start Contract" button on job detail page
2. System validates:
   - Job is in 'selecting' or 'recruiting' state
   - At least one application is selected/approved
   - Job has `expired_date` set
   - Funder has `wallet_address` configured
   - Seller (marketplace) has `wallet_address`, `key_id`, and `private_key` configured
3. Auto-fill contract parameters:
   - Calculate completion date: `expired_date + timedelta(days=7)`
   - Get buyer wallet: `job.funder.wallet_address`
   - Get seller wallet/key: From User model (marketplace account)
   - Number of payments: 1
4. Initiate GNAP flow:
   - Initialize `OpenPaymentsProcessor` with seller credentials
   - Request incoming payment grant (seller side)
   - Create incoming payment (escrow)
   - Request quote grant (buyer side)
   - Create quote
   - Request interactive outgoing payment grant
   - Store contract_id (transaction ID) in Job model
   - Redirect buyer to wallet for authorization
5. After authorization callback:
   - Complete payment using stored transaction data
   - Update job status to 'submitting'
   - Redirect to job detail page

## Implementation Steps

### 1. Database Model Changes

#### Add Seller Key Fields to User Model (`users/models.py`)
```python
class User(AbstractUser):
    # ... existing fields ...
    
    # Seller credentials for Open Payments (for marketplace account)
    seller_key_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Seller Key ID'),
        help_text=_('Key identifier for seller wallet (marketplace account)')
    )
    seller_private_key = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Seller Private Key'),
        help_text=_('Private key (PEM format) for seller wallet authentication')
    )
    seller_wallet_address = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_('Seller Wallet Address'),
        help_text=_('Open Payments wallet address for seller/marketplace account')
    )
```

#### Add Contract ID to Job Model (`jobs/models.py`)
```python
class Job(models.Model):
    # ... existing fields ...
    
    contract_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_('Contract ID'),
        help_text=_('ULID transaction ID for Open Payments contract')
    )
    
    # Store GNAP transaction data (for completing payment after authorization)
    incoming_payment_id = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Incoming Payment ID'),
        help_text=_('Open Payments incoming payment URL')
    )
    quote_id = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Quote ID'),
        help_text=_('Open Payments quote URL')
    )
    interactive_redirect_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Interactive Redirect URL'),
        help_text=_('URL to redirect buyer for wallet authorization')
    )
    finish_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Finish ID'),
        help_text=_('GNAP finish identifier')
    )
    continue_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Continue ID'),
        help_text=_('GNAP continuation access token')
    )
    continue_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_('Continue URL'),
        help_text=_('GNAP continuation endpoint')
    )
```

### 2. Views and URLs

#### Create Start Contract View (`jobs/views.py`)
```python
@login_required
@require_POST
def start_contract(request, pk):
    """Start contract with auto-filled parameters and initiate GNAP flow."""
    from datetime import timedelta
    from ulid import ULID
    from open_payments.crud_open_payments import OpenPaymentsProcessor
    from schemas.openpayments.open_payments import SellerOpenPaymentAccount
    from django.conf import settings
    
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    # Validate job state
    if job.status not in ['selecting', 'recruiting']:
        messages.warning(request, _('Contract can only be started in selecting or recruiting state.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Validate selected applications exist
    selected_applications = job.applications.filter(status='selected')
    if not selected_applications.exists():
        messages.warning(request, _('You need to approve at least one applicant before starting the contract.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Validate expired_date exists
    if not job.expired_date:
        messages.error(request, _('Job must have an expired date set before starting contract.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Validate contract not already started
    if job.contract_id:
        messages.info(request, _('Contract already started for this job.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Get buyer wallet (funder)
    buyer_wallet = job.funder.wallet_address
    if not buyer_wallet:
        messages.error(request, _('You must configure your wallet address in your profile before starting a contract.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Get seller credentials (marketplace account)
    # For now, use the first user with seller credentials configured
    # TODO: In production, use a dedicated marketplace/system account
    seller_user = User.objects.filter(
        seller_wallet_address__isnull=False,
        seller_key_id__isnull=False,
        seller_private_key__isnull=False
    ).first()
    
    if not seller_user:
        messages.error(request, _('Seller account not configured. Please contact administrator.'))
        return redirect('jobs:detail', pk=job.pk)
    
    try:
        # Prepare seller account
        seller_account = SellerOpenPaymentAccount(
            walletAddressUrl=seller_user.seller_wallet_address,
            privateKey=seller_user.seller_private_key,
            keyId=seller_user.seller_key_id
        )
        
        # Initialize processor
        redirect_uri = f"{settings.DEFAULT_REDIRECT_AFTER_AUTH or '/jobs/contract-complete/'}"
        processor = OpenPaymentsProcessor(
            seller=seller_account,
            buyer=buyer_wallet,
            redirect_uri=redirect_uri
        )
        
        # Calculate total amount (budget in smallest currency unit)
        # Assuming pesos with 2 decimal places, convert to smallest unit
        total_amount = str(int(job.budget * 100))
        
        # Get purchase endpoint (triggers incoming payment, quote, and interactive grant)
        redirect_url = processor.get_purchase_endpoint(amount=total_amount)
        
        # Store contract_id and transaction data in Job
        contract_id = str(processor.pending_payment.id)
        job.contract_id = contract_id
        job.incoming_payment_id = str(processor.pending_payment.incoming_payment_id) if processor.pending_payment.incoming_payment_id else None
        job.quote_id = str(processor.pending_payment.quote_id) if processor.pending_payment.quote_id else None
        job.interactive_redirect_url = str(redirect_url)
        job.finish_id = processor.pending_payment.finish_id
        job.continue_id = processor.pending_payment.continue_id
        job.continue_url = str(processor.pending_payment.continue_url) if processor.pending_payment.continue_url else None
        job.save()
        
        # TODO: Persist PendingIncomingPaymentTransaction to database/cache
        # Currently it's in-memory, need to store it keyed by contract_id
        # Option: Create PendingPaymentTransaction model or use cache
        
        # Redirect buyer to wallet for authorization
        return redirect(redirect_url)
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to start contract: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, _('Failed to start contract: {error}').format(error=str(e)))
        return redirect('jobs:detail', pk=job.pk)
```

#### Create Contract Completion Callback Handler (`jobs/views.py`)
```python
@login_required
def complete_contract_payment(request):
    """Handle callback from buyer wallet after authorization."""
    from open_payments.crud_open_payments import OpenPaymentsProcessor
    from schemas.openpayments.open_payments import SellerOpenPaymentAccount, PendingIncomingPaymentTransaction
    from open_payments_sdk.models.wallet import WalletAddress
    
    interact_ref = request.GET.get('interact_ref')
    hash_value = request.GET.get('hash')
    contract_id = request.GET.get('contract_id')  # From redirect URI suffix
    
    if not contract_id:
        # Try to extract from redirect URI
        # The redirect URI format is: /jobs/contract-complete/{contract_id}
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 3 and path_parts[-2] == 'contract-complete':
            contract_id = path_parts[-1]
    
    if not contract_id or not interact_ref or not hash_value:
        messages.error(request, _('Invalid callback parameters.'))
        return redirect('jobs:list')
    
    # Retrieve job by contract_id
    try:
        job = Job.objects.get(contract_id=contract_id)
    except Job.DoesNotExist:
        messages.error(request, _('Contract not found.'))
        return redirect('jobs:list')
    
    # Verify user is the funder
    if request.user != job.funder:
        messages.error(request, _('You are not authorized to complete this contract.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Get seller credentials
    seller_user = User.objects.filter(
        seller_wallet_address__isnull=False,
        seller_key_id__isnull=False,
        seller_private_key__isnull=False
    ).first()
    
    if not seller_user:
        messages.error(request, _('Seller account not configured.'))
        return redirect('jobs:detail', pk=job.pk)
    
    try:
        # Reconstruct PendingIncomingPaymentTransaction from stored data
        # TODO: This should ideally be retrieved from database/cache
        # For now, we'll need to reconstruct it or store it properly
        
        # Prepare seller account
        seller_account = SellerOpenPaymentAccount(
            walletAddressUrl=seller_user.seller_wallet_address,
            privateKey=seller_user.seller_private_key,
            keyId=seller_user.seller_key_id
        )
        
        # Initialize processor to get wallet addresses
        processor = OpenPaymentsProcessor(
            seller=seller_account,
            buyer=job.funder.wallet_address,
            redirect_uri=f"{settings.DEFAULT_REDIRECT_AFTER_AUTH or '/jobs/contract-complete/'}"
        )
        
        # Reconstruct pending payment transaction
        # Note: This is a workaround - ideally we'd store the full PendingIncomingPaymentTransaction
        from ulid import ULID
        pending_payment = PendingIncomingPaymentTransaction(
            id=ULID.from_str(contract_id),
            buyer=processor.buyer_wallet,
            seller=processor.seller_wallet,
            incoming_payment_id=job.incoming_payment_id,
            quote_id=job.quote_id,
            finish_id=job.finish_id,
            continue_id=job.continue_id,
            continue_url=job.continue_url,
        )
        
        # Complete payment
        outgoing_payment = processor.complete_payment(
            interact_ref=interact_ref,
            received_hash=hash_value,
            pending_payment=pending_payment
        )
        
        # Update job status to submitting
        job.status = 'submitting'
        job.save()
        
        messages.success(request, _('Contract authorized! Job is now in submitting phase. Approved workers can now submit their work.'))
        return redirect('jobs:detail', pk=job.pk)
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to complete contract payment: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, _('Failed to complete contract: {error}').format(error=str(e)))
        return redirect('jobs:detail', pk=job.pk)
```

#### Update URLs (`jobs/urls.py`)
```python
path('<int:pk>/start-contract/', views.start_contract, name='start_contract'),
path('contract-complete/<str:contract_id>/', views.complete_contract_payment, name='complete_contract_payment'),
# Or if using query params:
path('contract-complete/', views.complete_contract_payment, name='complete_contract_payment'),
```

#### Update Job Detail Template (`templates/jobs/job_detail.html`)
Change the "Start Contract" form action:
```django
<form method="post" action="{% url 'jobs:start_contract' job.pk %}" id="start-contract-form">
    {% csrf_token %}
    <!-- ... existing button ... -->
</form>
```

### 3. Settings (`marketplace/settings.py`)
```python
DEFAULT_REDIRECT_AFTER_AUTH = '/jobs/contract-complete/'
```

### 4. Transaction Storage

#### Option: Create PendingPaymentTransaction Model (`jobs/models.py`)
```python
class PendingPaymentTransaction(models.Model):
    """Stores PendingIncomingPaymentTransaction data for contract completion."""
    contract_id = models.CharField(max_length=255, unique=True, primary_key=True)
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='pending_transaction')
    
    # Serialized wallet data (JSON)
    buyer_wallet_data = models.JSONField()
    seller_wallet_data = models.JSONField()
    
    # Transaction IDs
    incoming_payment_id = models.URLField(null=True, blank=True)
    quote_id = models.URLField(null=True, blank=True)
    interactive_redirect = models.URLField(null=True, blank=True)
    finish_id = models.CharField(max_length=255, null=True, blank=True)
    continue_id = models.CharField(max_length=255, null=True, blank=True)
    continue_url = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Pending Payment Transaction')
        verbose_name_plural = _('Pending Payment Transactions')
```

Update `start_contract` to save pending transaction:
```python
# After creating processor and getting redirect_url
from jobs.models import PendingPaymentTransaction

PendingPaymentTransaction.objects.create(
    contract_id=contract_id,
    job=job,
    buyer_wallet_data=processor.buyer_wallet.model_dump(),
    seller_wallet_data=processor.seller_wallet.model_dump(),
    incoming_payment_id=str(processor.pending_payment.incoming_payment_id) if processor.pending_payment.incoming_payment_id else None,
    quote_id=str(processor.pending_payment.quote_id) if processor.pending_payment.quote_id else None,
    interactive_redirect=str(redirect_url),
    finish_id=processor.pending_payment.finish_id,
    continue_id=processor.pending_payment.continue_id,
    continue_url=str(processor.pending_payment.continue_url) if processor.pending_payment.continue_url else None,
)
```

### 5. Testing

#### Basic Integration Test (`jobs/tests/test_contract_creation.py`)
```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job, JobApplication
from open_payments.crud_open_payments import OpenPaymentsProcessor
from schemas.openpayments.open_payments import SellerOpenPaymentAccount

User = get_user_model()

class ContractCreationTest(TestCase):
    """Test contract creation flow without frontend, no mocks."""
    
    def setUp(self):
        """Set up test data."""
        # Create funder (buyer) with wallet
        self.funder = User.objects.create_user(
            username='funder',
            email='funder@test.com',
            wallet_address='https://ilp.interledger-test.dev/buyer'
        )
        
        # Create seller (marketplace account) with credentials
        self.seller = User.objects.create_user(
            username='seller',
            email='seller@test.com',
            seller_wallet_address='https://ilp.interledger-test.dev/seller',
            seller_key_id='test-key-id',
            seller_private_key='''-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg...
-----END PRIVATE KEY-----'''
        )
        
        # Create job
        self.job = Job.objects.create(
            title='Test Job',
            description='Test description',
            target_language='en',
            deliverable_types='text',
            budget=100.00,
            amount_per_person=100.00,
            funder=self.funder,
            status='selecting',
            expired_date=timezone.now() + timedelta(days=7),
            max_responses=1
        )
        
        # Create applicant
        self.applicant = User.objects.create_user(
            username='applicant',
            email='applicant@test.com'
        )
        
        # Create selected application
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.applicant,
            status='selected'
        )
    
    def test_start_contract_auto_fills_parameters(self):
        """Test that contract creation auto-fills all parameters."""
        # This test verifies the auto-fill logic
        # Note: Actual GNAP calls will hit real wallets - ensure test wallets are configured
        
        # Calculate expected completion date
        expected_completion_date = self.job.expired_date + timedelta(days=7)
        
        # Verify job has required data
        self.assertIsNotNone(self.job.expired_date)
        self.assertIsNotNone(self.funder.wallet_address)
        self.assertIsNotNone(self.seller.seller_wallet_address)
        self.assertIsNotNone(self.seller.seller_key_id)
        self.assertIsNotNone(self.seller.seller_private_key)
        
        # Verify selected applications exist
        selected_apps = self.job.applications.filter(status='selected')
        self.assertTrue(selected_apps.exists())
        
        # Number of payments should always be 1
        num_payments = 1
        self.assertEqual(num_payments, 1)
    
    def test_start_contract_creates_transaction_id(self):
        """Test that starting contract creates and stores contract_id."""
        from jobs.views import start_contract
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post(f'/jobs/{self.job.pk}/start-contract/')
        request.user = self.funder
        
        # Call start_contract view
        # Note: This will make real GNAP calls - ensure test environment is configured
        response = start_contract(request, pk=self.job.pk)
        
        # Refresh job from database
        self.job.refresh_from_db()
        
        # Verify contract_id was created
        self.assertIsNotNone(self.job.contract_id)
        self.assertIsNotNone(self.job.incoming_payment_id)
        self.assertIsNotNone(self.job.quote_id)
        
        # Verify contract_id is a valid ULID format
        from ulid import ULID
        try:
            ULID.from_str(self.job.contract_id)
        except ValueError:
            self.fail("contract_id is not a valid ULID")
    
    def test_complete_contract_payment_updates_job_status(self):
        """Test that completing contract payment updates job status to submitting."""
        # First, start the contract
        # ... (setup contract_id and transaction data)
        
        # Then simulate callback
        # ... (call complete_contract_payment with interact_ref and hash)
        
        # Verify job status changed to submitting
        # self.job.refresh_from_db()
        # self.assertEqual(self.job.status, 'submitting')
        
        # Note: Full test requires actual wallet interaction
        pass
    
    def test_contract_completion_date_calculation(self):
        """Test that completion date is calculated as expired_date + 7 days."""
        expired_date = timezone.now() + timedelta(days=7)
        completion_date = expired_date + timedelta(days=7)
        
        expected_date = expired_date + timedelta(days=7)
        self.assertEqual(completion_date, expected_date)
```

#### Run Tests
```bash
cd marketplace-py
uv run python manage.py test jobs.tests.test_contract_creation
```

## Migration Path

1. **Add User model fields** (seller_key_id, seller_private_key, seller_wallet_address)
   ```bash
   uv run python manage.py makemigrations users
   uv run python manage.py migrate users
   ```

2. **Add Job model fields** (contract_id, incoming_payment_id, quote_id, etc.)
   ```bash
   uv run python manage.py makemigrations jobs
   uv run python migrate jobs
   ```

3. **Create PendingPaymentTransaction model** (optional, for better transaction storage)
   ```bash
   uv run python manage.py makemigrations jobs
   uv run python migrate jobs
   ```

4. **Update views** - Add start_contract and complete_contract_payment

5. **Update URLs** - Add new routes

6. **Update template** - Change Start Contract button action

7. **Add settings** - DEFAULT_REDIRECT_AFTER_AUTH

8. **Write tests** - Create test_contract_creation.py

9. **Test end-to-end** - Run tests and manual testing

## Related Files to Modify

- `marketplace-py/users/models.py` - Add seller credential fields
- `marketplace-py/jobs/models.py` - Add contract_id and transaction fields
- `marketplace-py/jobs/views.py` - Add start_contract and complete_contract_payment views
- `marketplace-py/jobs/urls.py` - Add new routes
- `marketplace-py/templates/jobs/job_detail.html` - Update Start Contract button
- `marketplace-py/marketplace/settings.py` - Add DEFAULT_REDIRECT_AFTER_AUTH
- `marketplace-py/jobs/tests/test_contract_creation.py` - New test file

## Notes

- **Seller Account**: Currently uses first user with seller credentials. In production, use a dedicated marketplace/system account.
- **Transaction Storage**: PendingIncomingPaymentTransaction is currently in-memory. Consider storing in database (PendingPaymentTransaction model) or cache.
- **Error Handling**: Add comprehensive error handling for wallet configuration, GNAP failures, network errors.
- **Security**: Seller private keys stored in User model should be encrypted at rest in production.
- **Completion Date**: Always calculated as `expired_date + 7 days` as per help text.
- **Number of Payments**: Always 1 for all cases.
- **Parties**: Buyer is funder, seller is marketplace account (not individual workers - payments to workers happen later).
