from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Prefetch
from django.urls import reverse
from django.http import Http404
from django.views.decorators.http import require_POST
from decimal import Decimal
from audio.forms import AudioContributionForm
from .forms import JobFundingForm, JobApplicationForm
from .models import Job, JobSubmission, JobFunding, JobApplication
from .audio_support import AUDIO_SUPPORT_OPPORTUNITIES, get_audio_support_opportunity
from .payments_utils import create_incoming_payment


COMMUNITY_FUND_AMOUNT = 10


def _build_audio_targets():
    targets = {}
    for slug, opportunity in AUDIO_SUPPORT_OPPORTUNITIES.items():
        targets[slug] = {
            'slug': slug,
            'title': opportunity.title,
            'description_es': opportunity.description_es,
            'language_code': opportunity.language_code,
            'needs_funding': opportunity.needs_funding,
            'support_url': reverse('jobs:audio_support', args=[slug]),
        }
    return targets


def job_list(request):
    """List all available jobs."""
    jobs = Job.objects.all().order_by('-created_at')
    
    # Filter by funding status - default to showing funded jobs
    show_funded = request.GET.get('show_funded', 'on') == 'on'
    show_unfunded = request.GET.get('show_unfunded', '') == 'on'
    
    funding_filters = Q()
    if show_funded:
        funding_filters |= Q(is_funded=True)
    if show_unfunded:
        funding_filters |= Q(is_funded=False)
    
    if funding_filters:
        jobs = jobs.filter(funding_filters)
    else:
        # If neither is checked, show nothing (edge case)
        jobs = jobs.none()
    
    # Filter by status - exclude completed by default
    show_completed = request.GET.get('show_completed', '') == 'on'
    if not show_completed:
        jobs = jobs.exclude(status='completed')
    
    # Filter by language if provided
    language_filter = request.GET.get('language')
    if language_filter:
        jobs = jobs.filter(target_language=language_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'jobs': jobs,
        'language_filter': language_filter,
        'search_query': search_query,
        'show_funded': show_funded,
        'show_unfunded': show_unfunded,
        'show_completed': show_completed,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    """View job details."""
    job = get_object_or_404(Job, pk=pk)
    job.refresh_funding_snapshot()
    user_submissions = None
    user_application = None
    
    if request.user.is_authenticated:
        user_submissions = job.submissions.filter(creator=request.user)
        user_application = job.applications.filter(applicant=request.user).first()
    
    context = {
        'job': job,
        'user_submissions': user_submissions,
        'user_application': user_application,
        'fundings': job.fundings.select_related('funder').order_by('-created_at')[:5],
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def pledge_job(request, pk):
    """Allow authenticated users to pledge funds toward a job budget."""
    job = get_object_or_404(Job, pk=pk)
    
    if request.user == job.funder:
        messages.info(request, _('You already created this job; use the fund button on your dashboard.'))
        return redirect('jobs:detail', pk=job.pk)
    
    remaining_amount = job.remaining_budget()
    existing_total = job.budget - remaining_amount
    
    if remaining_amount <= Decimal('0.00'):
        job.refresh_funding_snapshot()
        messages.info(request, _('This job is already fully funded.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if job.is_funded:
        messages.info(request, _('This job is already fully funded.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if job.status != 'open':
        messages.warning(request, _('This job is no longer accepting funding.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        form = JobFundingForm(request.POST, job=job)
        if form.is_valid():
            funding = form.save(commit=False)
            funding.job = job
            funding.funder = request.user
            funding.save()
            job.refresh_funding_snapshot()
            messages.success(request, _('Thank you! Your pledge was recorded.'))
            return redirect('jobs:detail', pk=job.pk)
    else:
        suggested_amount = remaining_amount if remaining_amount > Decimal('0.00') else job.budget
        form = JobFundingForm(initial={'amount': suggested_amount}, job=job)
    
    context = {
        'job': job,
        'form': form,
        'remaining_amount': remaining_amount,
        'existing_total': existing_total,
    }
    return render(request, 'jobs/pledge_job.html', context)


@login_required
def my_jobs(request):
    """View jobs posted by the current user."""
    jobs = Job.objects.filter(funder=request.user).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    context = {
        'jobs': jobs,
        'status_filter': status_filter,
    }
    return render(request, 'jobs/my_jobs.html', context)


@login_required
def job_owner_dashboard(request):
    """Dashboard for funders to monitor their jobs and submissions."""
    jobs_qs = Job.objects.filter(funder=request.user).annotate(
        total_submissions=Count('submissions', distinct=True),
        accepted_submissions=Count('submissions', filter=Q(submissions__status='accepted'), distinct=True),
        pending_submissions=Count('submissions', filter=Q(submissions__status='pending'), distinct=True),
    ).prefetch_related(
        Prefetch(
            'submissions',
            queryset=JobSubmission.objects.select_related('creator').order_by('-created_at')
        )
    ).order_by('-created_at')
    
    has_jobs = jobs_qs.exists()
    jobs = list(jobs_qs)
    
    context = {
        'jobs': jobs,
        'has_jobs': has_jobs,
    }
    return render(request, 'jobs/job_owner_dashboard.html', context)


@login_required
def accepted_jobs(request):
    """View jobs where user's submissions were accepted."""
    accepted_submissions = JobSubmission.objects.filter(
        creator=request.user,
        status='accepted'
    ).select_related('job').order_by('-created_at')
    
    context = {
        'accepted_submissions': accepted_submissions,
    }
    return render(request, 'jobs/accepted_jobs.html', context)


@login_required
def create_job(request):
    """Create a new job."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        target_language = request.POST.get('target_language')
        target_dialect = request.POST.get('target_dialect', '')
        deliverable_types_list = request.POST.getlist('deliverable_types')
        deliverable_types = ','.join(deliverable_types_list) if deliverable_types_list else ''
        amount_per_person = request.POST.get('amount_per_person')
        max_responses = request.POST.get('max_responses', '1')
        reference_audio = request.FILES.get('reference_audio')
        reference_video = request.FILES.get('reference_video')
        reference_image = request.FILES.get('reference_image')
        
        # Validate that at least one deliverable type is selected
        if not deliverable_types_list:
            messages.error(request, _('Please select at least one deliverable type.'))
            return render(request, 'jobs/create_job.html')
        
        if title and description and target_language and deliverable_types and budget:
            try:
                budget_decimal = Decimal(budget)
                max_responses_int = int(max_responses)
                if max_responses_int < 1:
                    max_responses_int = 1
                
                job = Job.objects.create(
                    title=title,
                    description=description,
                    target_language=target_language,
                    target_dialect=target_dialect,
                    deliverable_types=deliverable_types,
                    budget=budget_decimal,
                    max_responses=max_responses_int,
                    funder=request.user,
                    reference_audio=reference_audio,
                    reference_video=reference_video,
                    reference_image=reference_image
                )
                
                messages.success(request, _('Job created successfully! You can fund it later from the job detail page.'))
                
                return redirect('jobs:detail', pk=job.pk)
            except ValueError:
                messages.error(request, _('Invalid amount per person.'))
            except Exception as e:
                messages.error(request, _('Error creating job: {error}').format(error=str(e)))
        else:
            messages.error(request, _('Please fill in all required fields.'))
    
    return render(request, 'jobs/create_job.html')


@login_required
def submit_job(request, pk):
    """Submit work for a job."""
    job = get_object_or_404(Job, pk=pk)
    
    # Check if job is already completed
    if job.status == 'completed':
        messages.error(request, _('This job has been completed and is no longer accepting submissions.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if job.status != 'open':
        messages.error(request, _('This job is no longer accepting submissions.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if not job.is_funded:
        messages.error(request, _('This job is not yet funded. Please wait for the funder to fund it.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Check if user has already submitted to this job
    existing_submission = job.submissions.filter(creator=request.user).first()
    if existing_submission:
        messages.error(request, _('You have already submitted work for this job. You can only submit once per job.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Check if job has reached max responses
    if job.has_reached_max_responses():
        messages.error(request, _('This job has reached its maximum number of responses ({max}). No more submissions are being accepted.').format(max=job.max_responses))
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        note = request.POST.get('note', '')
        
        submission = JobSubmission.objects.create(
            job=job,
            creator=request.user,
            note=note
        )
        
        # Handle file uploads
        deliverable_types = job.get_deliverable_types_list()
        
        if 'text' in deliverable_types and 'text_file' in request.FILES:
            submission.text_file = request.FILES['text_file']
        if 'video' in deliverable_types and 'video_file' in request.FILES:
            submission.video_file = request.FILES['video_file']
        if 'audio' in deliverable_types and 'audio_file' in request.FILES:
            submission.audio_file = request.FILES['audio_file']
        if 'image' in deliverable_types and 'image_file' in request.FILES:
            submission.image_file = request.FILES['image_file']
        
        submission.save()
        messages.success(request, _('Submission created successfully!'))
        return redirect('jobs:detail', pk=job.pk)
    
    return render(request, 'jobs/submit_job.html', {'job': job})


@login_required
def fund_job(request, pk):
    """Fund a job by creating an escrow payment."""
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    remaining_amount = job.remaining_budget()
    if remaining_amount <= Decimal('0.00'):
        job.refresh_funding_snapshot()
        messages.warning(request, _('This job is already funded.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        # Create incoming payment for the remaining budget
        payment_result = create_incoming_payment(
            amount=remaining_amount,
            description=f"Funding for job: {job.title}"
        )
        
        if payment_result['success']:
            job.payment_id = payment_result.get('payment_id', '')
            job.save(update_fields=['payment_id'])
            JobFunding.objects.create(
                job=job,
                funder=request.user,
                amount=remaining_amount,
                note=_('Owner funding')
            )
            job.refresh_funding_snapshot()
            messages.success(request, _('Job funded successfully!'))
        else:
            messages.error(
                request,
                _('Failed to fund job: {error}').format(
                    error=payment_result.get('error', 'Unknown error')
                )
            )
        
        return redirect('jobs:detail', pk=job.pk)
    
    # GET request - show confirmation page or redirect to detail
    return redirect('jobs:detail', pk=job.pk)


@login_required
def accept_submission(request, job_pk, submission_pk):
    """Accept a submission for a job."""
    job = get_object_or_404(Job, pk=job_pk, funder=request.user)
    submission = get_object_or_404(JobSubmission, pk=submission_pk, job=job)
    
    if submission.status == 'accepted':
        messages.warning(request, _('This submission is already accepted.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Check if job has reached max responses
    if job.has_reached_max_responses():
        messages.error(request, _('This job has reached its maximum number of responses ({max}). Cannot accept more submissions.').format(max=job.max_responses))
        return redirect('jobs:detail', pk=job.pk)
    
    # If max_responses is 1, reject all other submissions (old behavior)
    # Otherwise, allow multiple accepted submissions
    if job.max_responses == 1:
        job.submissions.exclude(pk=submission_pk).update(status='rejected')
    
    # Accept this submission
    submission.status = 'accepted'
    submission.save()
    
    # Update job status based on progress
    new_status = None
    if job.has_reached_max_responses():
        new_status = 'waiting_completion'
    elif not job.is_funded:
        new_status = 'funded'
    
    if new_status and job.status != new_status:
        job.status = new_status
        job.save(update_fields=['status'])
    
    messages.success(request, _('Submission accepted! ({accepted}/{max} responses)').format(
        accepted=job.get_accepted_submissions_count(),
        max=job.max_responses
    ))
    return redirect('jobs:detail', pk=job.pk)


@login_required
def my_products(request):
    """View user's products/services (placeholder)."""
    # This is a placeholder for future products functionality
    context = {}
    return render(request, 'jobs/my_products.html', context)


@login_required
def my_money(request):
    """View user's wallet and financial information."""
    # Get user's accepted jobs and their budgets
    accepted_submissions = JobSubmission.objects.filter(
        creator=request.user,
        status='accepted'
    ).select_related('job')
    
    total_earned = sum(submission.job.budget for submission in accepted_submissions)
    
    # Get jobs posted by user (money spent)
    posted_jobs = Job.objects.filter(funder=request.user)
    total_spent = sum(
        job.budget for job in posted_jobs
        if job.is_funded or job.status in ['funded', 'completed']
    )
    
    balance = total_earned - total_spent
    
    context = {
        'accepted_submissions': accepted_submissions,
        'total_earned': total_earned,
        'total_spent': total_spent,
        'balance': balance,
        'wallet_endpoint': request.user.wallet_endpoint,
    }
    return render(request, 'jobs/my_money.html', context)


@login_required
def pending_jobs(request):
    """View jobs that need to be finished (accepted submissions)."""
    # Get jobs where user has accepted submissions that aren't completed
    accepted_submissions = JobSubmission.objects.filter(
        creator=request.user,
        status='accepted'
    ).select_related('job').order_by('-created_at')
    
    # Filter to only show jobs that aren't completed
    pending = [sub for sub in accepted_submissions if sub.job.status != 'completed']
    
    context = {
        'pending_jobs': pending,
    }
    return render(request, 'jobs/pending_jobs.html', context)


@login_required
def filler_page_1(request):
    """Filler page 1 (placeholder)."""
    context = {}
    return render(request, 'jobs/filler_page_1.html', context)


@login_required
def filler_page_2(request):
    """Filler page 2 (placeholder)."""
    context = {}
    return render(request, 'jobs/filler_page_2.html', context)


@login_required
def dashboard(request):
    """Dashboard with main navigation icons - mobile first design."""
    has_posted_jobs = False
    if request.user.is_authenticated:
        has_posted_jobs = request.user.posted_jobs.exists()
    context = {
        'audio_targets': _build_audio_targets(),
        'community_fund_amount': COMMUNITY_FUND_AMOUNT,
        'has_posted_jobs': has_posted_jobs,
    }
    return render(request, 'jobs/dashboard.html', context)


@login_required
@require_POST
def mark_job_completed(request, pk):
    """Allow funders to mark a job as completed after reviewing submissions."""
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    if job.status == 'completed':
        messages.info(request, _('This job is already marked as completed.'))
        return redirect('jobs:owner_dashboard')
    
    if job.submissions.filter(status='accepted').count() == 0:
        messages.warning(request, _('You need at least one accepted submission before completing a job.'))
        return redirect('jobs:owner_dashboard')
    
    job.status = 'completed'
    job.save(update_fields=['status'])
    messages.success(request, _('Job marked as completed.'))
    return redirect('jobs:owner_dashboard')


@login_required
def apply_to_job(request, pk):
    """Allow workers to submit their profile/application for a job."""
    job = get_object_or_404(Job, pk=pk)
    
    # Check if user already applied
    existing_application = JobApplication.objects.filter(job=job, applicant=request.user).first()
    if existing_application:
        messages.info(request, _('You have already applied to this job.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Don't allow job owner to apply to their own job
    if request.user == job.funder:
        messages.warning(request, _('You cannot apply to your own job.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, _('Your application has been submitted! The job owner will review it.'))
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobApplicationForm()
    
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'jobs/apply_to_job.html', context)


@login_required
def view_applications(request, pk):
    """Job owner view to see all applications for their job."""
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    applications = job.applications.select_related('applicant').order_by('-created_at')
    
    context = {
        'job': job,
        'applications': applications,
        'selected_count': applications.filter(status='selected').count(),
    }
    return render(request, 'jobs/view_applications.html', context)


@login_required
@require_POST
def select_application(request, job_pk, application_pk):
    """Job owner selects an application."""
    job = get_object_or_404(Job, pk=job_pk, funder=request.user)
    application = get_object_or_404(JobApplication, pk=application_pk, job=job)
    
    action = request.POST.get('action')
    if action == 'select':
        application.status = 'selected'
        application.save()
        messages.success(request, _('Application selected.'))
    elif action == 'reject':
        application.status = 'rejected'
        application.save()
        messages.success(request, _('Application rejected.'))
    elif action == 'pending':
        application.status = 'pending'
        application.save()
        messages.success(request, _('Application status reset to pending.'))
    
    return redirect('jobs:view_applications', pk=job.pk)


@login_required
def pre_approve_payments(request, pk):
    """Stub for pre-approved payments - button that doesn't work yet."""
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    selected_applications = job.applications.filter(status='selected')
    
    if not selected_applications.exists():
        messages.warning(request, _('You need to select at least one applicant before creating pre-approved payments.'))
        return redirect('jobs:view_applications', pk=job.pk)
    
    # TODO: Implement actual pre-approved payment logic
    messages.info(request, _('Pre-approved payment functionality is coming soon. This will allow you to create payment authorizations for selected workers.'))
    return redirect('jobs:view_applications', pk=job.pk)


@login_required
@require_POST
def mark_submission_complete(request, job_pk, submission_pk):
    """Allow workers to mark their submission as complete."""
    job = get_object_or_404(Job, pk=job_pk)
    submission = get_object_or_404(JobSubmission, pk=submission_pk, job=job, creator=request.user)
    
    if submission.status != 'accepted':
        messages.warning(request, _('You can only mark accepted submissions as complete.'))
        return redirect('jobs:detail', pk=job.pk)
    
    from django.utils import timezone
    submission.is_complete = True
    submission.completed_at = timezone.now()
    submission.save()
    
    messages.success(request, _('Your work has been marked as complete!'))
    return redirect('jobs:detail', pk=job.pk)


def audio_support(request, slug):
    """Public page where the community can fund or upload missing audio."""
    opportunity = get_audio_support_opportunity(slug)
    if not opportunity:
        raise Http404

    # Hide language field since the opportunity already has a specific language
    contribution_form = AudioContributionForm(
        hide_language=True,
        initial={'language_code': opportunity.language_code}
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_audio':
            # Create form without language field, but set language_code in POST data
            post_data = request.POST.copy()
            post_data['language_code'] = opportunity.language_code
            contribution_form = AudioContributionForm(post_data, request.FILES, hide_language=True)
            if contribution_form.is_valid():
                contribution = contribution_form.save(commit=False)
                contribution.language_code = opportunity.language_code  # Ensure it's set
                contribution.target_slug = opportunity.slug
                contribution.target_label = opportunity.title
                if request.user.is_authenticated:
                    contribution.contributed_by = request.user
                contribution.save()
                messages.success(
                    request,
                    _('?Gracias! Tu audio se subi? correctamente. El equipo lo revisar? antes de publicarlo.')
                )
                return redirect('jobs:audio_support', slug=slug)
        elif action == 'pledge_funds':
            messages.info(
                request,
                _('Gracias por tu inter?s en fondear este audio. Conectaremos los pagos de 10 pesos muy pronto.')
            )
            return redirect('jobs:audio_support', slug=slug)

    context = {
        'opportunity': opportunity,
        'contribution_form': contribution_form,
        'community_fund_amount': COMMUNITY_FUND_AMOUNT,
    }
    return render(request, 'jobs/audio_support.html', context)
