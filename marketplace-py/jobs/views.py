from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.urls import reverse
from django.http import Http404
from audio.forms import AudioContributionForm
from .models import Job, JobSubmission
from .audio_support import AUDIO_SUPPORT_OPPORTUNITIES, get_audio_support_opportunity


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
    jobs = Job.objects.filter(status='open').order_by('-created_at')
    
    # Filter by language if provided
    language_filter = request.GET.get('language')
    if language_filter:
        jobs = jobs.filter(target_language=language_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'jobs': jobs,
        'language_filter': language_filter,
        'search_query': search_query,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    """View job details."""
    job = get_object_or_404(Job, pk=pk)
    user_submissions = None
    
    if request.user.is_authenticated:
        user_submissions = job.submissions.filter(creator=request.user)
    
    context = {
        'job': job,
        'user_submissions': user_submissions,
    }
    return render(request, 'jobs/job_detail.html', context)


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
        deliverable_types = request.POST.get('deliverable_types')
        budget = request.POST.get('budget')
        
        if title and description and target_language and deliverable_types and budget:
            job = Job.objects.create(
                title=title,
                description=description,
                target_language=target_language,
                target_dialect=target_dialect,
                deliverable_types=deliverable_types,
                budget=budget,
                funder=request.user
            )
            messages.success(request, _('Job created successfully!'))
            return redirect('jobs:detail', pk=job.pk)
        else:
            messages.error(request, _('Please fill in all required fields.'))
    
    return render(request, 'jobs/create_job.html')


@login_required
def submit_job(request, pk):
    """Submit work for a job."""
    job = get_object_or_404(Job, pk=pk)
    
    if job.status != 'open':
        messages.error(request, _('This job is no longer accepting submissions.'))
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
def accept_submission(request, job_pk, submission_pk):
    """Accept a submission for a job."""
    job = get_object_or_404(Job, pk=job_pk, funder=request.user)
    submission = get_object_or_404(JobSubmission, pk=submission_pk, job=job)
    
    if submission.status == 'accepted':
        messages.warning(request, _('This submission is already accepted.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Reject all other submissions
    job.submissions.exclude(pk=submission_pk).update(status='rejected')
    
    # Accept this submission
    submission.status = 'accepted'
    submission.save()
    
    # Update job status
    job.status = 'funded'
    job.save()
    
    messages.success(request, _('Submission accepted! Funds will be released.'))
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
    total_spent = sum(job.budget for job in posted_jobs if job.status in ['funded', 'completed'])
    
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
    context = {
        'audio_targets': _build_audio_targets(),
        'community_fund_amount': COMMUNITY_FUND_AMOUNT,
    }
    return render(request, 'jobs/dashboard.html', context)


def audio_support(request, slug):
    """Public page where the community can fund or upload missing audio."""
    opportunity = get_audio_support_opportunity(slug)
    if not opportunity:
        raise Http404

    contribution_form = AudioContributionForm(
        initial={'language_code': opportunity.language_code}
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_audio':
            contribution_form = AudioContributionForm(request.POST, request.FILES)
            if contribution_form.is_valid():
                contribution = contribution_form.save(commit=False)
                contribution.target_slug = opportunity.slug
                contribution.target_label = opportunity.title
                if request.user.is_authenticated:
                    contribution.contributed_by = request.user
                contribution.save()
                messages.success(
                    request,
                    _('¡Gracias! Tu audio se subió correctamente. El equipo lo revisará antes de publicarlo.')
                )
                return redirect('jobs:audio_support', slug=slug)
        elif action == 'pledge_funds':
            messages.info(
                request,
                _('Gracias por tu interés en fondear este audio. Conectaremos los pagos de 10 pesos muy pronto.')
            )
            return redirect('jobs:audio_support', slug=slug)

    context = {
        'opportunity': opportunity,
        'contribution_form': contribution_form,
        'community_fund_amount': COMMUNITY_FUND_AMOUNT,
    }
    return render(request, 'jobs/audio_support.html', context)
