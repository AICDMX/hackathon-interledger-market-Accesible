from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Prefetch
from django.urls import reverse
from django.http import Http404
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from audio.forms import AudioContributionForm
from .forms import JobApplicationForm
from .models import Job, JobSubmission, JobApplication
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
    # Show only jobs that are recruiting (available for applications)
    # Include both 'recruiting' and legacy 'open' status for backward compatibility
    jobs = Job.objects.filter(status__in=['recruiting', 'open']).order_by('-created_at')
    
    # Filter by language if provided
    language_filter = request.GET.get('language')
    if language_filter:
        jobs = jobs.filter(target_language=language_filter)
    
    # Filter out jobs user has already applied to (default behavior)
    hide_applied = request.GET.get('hide_applied', 'on') == 'on'
    if request.user.is_authenticated and hide_applied:
        applied_job_ids = JobApplication.objects.filter(
            applicant=request.user
        ).values_list('job_id', flat=True)
        jobs = jobs.exclude(pk__in=applied_job_ids)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Get jobs waiting for user's submission (if authenticated)
    waiting_for_submission = []
    if request.user.is_authenticated:
        # Jobs in 'submitting' state where user has selected application but no submission
        selected_applications = JobApplication.objects.filter(
            applicant=request.user,
            status='selected'
        ).select_related('job')
        
        for application in selected_applications:
            job = application.job
            if job.status == 'submitting':
                # Check if user hasn't submitted yet
                if not job.submissions.filter(creator=request.user).exists():
                    waiting_for_submission.append(job)
    
    context = {
        'jobs': jobs,
        'language_filter': language_filter,
        'search_query': search_query,
        'hide_applied': hide_applied,
        'waiting_for_submission': waiting_for_submission,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    """View job details."""
    job = get_object_or_404(Job, pk=pk)
    
    # If job is a draft, only allow the owner to view it
    if job.status == 'draft' and (not request.user.is_authenticated or request.user != job.funder):
        raise Http404("Job not found")
    
    # Check if job should auto-transition (e.g., deadline passed)
    if job.should_transition_to_selecting():
        job.status = 'selecting'
        job.save(update_fields=['status'])
    
    # Check if job should expire
    if job.should_expire():
        job.status = 'expired'
        job.save(update_fields=['status'])
    
    user_submissions = None
    user_application = None
    
    if request.user.is_authenticated:
        user_submissions = job.submissions.filter(creator=request.user)
        user_application = job.applications.filter(applicant=request.user).first()
    
    context = {
        'job': job,
        'user_submissions': user_submissions,
        'user_application': user_application,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def my_jobs(request):
    """View jobs posted by the current user."""
    if not request.user.is_funder():
        messages.error(request, _('You do not have permission to view this page.'))
        return redirect('jobs:list')
    
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
    if not request.user.is_funder():
        messages.error(request, _('You do not have permission to create jobs.'))
        return redirect('jobs:list')
    
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        target_language = request.POST.get('target_language', '')
        target_dialect = request.POST.get('target_dialect', '')
        deliverable_types_list = request.POST.getlist('deliverable_types')
        deliverable_types = ','.join(deliverable_types_list) if deliverable_types_list else ''
        amount_per_person = request.POST.get('amount_per_person', '')
        max_responses = request.POST.get('max_responses', '1')
        recruit_limit = request.POST.get('recruit_limit', '10')
        recruit_deadline_days = request.POST.get('recruit_deadline_days', '7')
        submit_limit = request.POST.get('submit_limit', '10')
        submit_deadline_days = request.POST.get('submit_deadline_days', '7')
        expired_date_days = request.POST.get('expired_date_days', '14')
        reference_audio = request.FILES.get('reference_audio')
        reference_video = request.FILES.get('reference_video')
        reference_image = request.FILES.get('reference_image')
        
        # Check if this is a draft save
        is_draft = 'save_draft' in request.POST
        
        # For drafts, allow saving with minimal data (just title)
        # For publishing, require all fields
        if is_draft:
            # Draft: only require title, allow partial data
            if not title:
                messages.error(request, _('Please provide at least a title for the draft.'))
                return render(request, 'jobs/create_job.html', {
                    'title': title,
                    'description': description,
                    'target_language': target_language,
                    'target_dialect': target_dialect,
                    'deliverable_types_list': deliverable_types_list,
                    'amount_per_person': amount_per_person,
                    'max_responses': max_responses,
                    'recruit_limit': recruit_limit,
                    'recruit_deadline_days': recruit_deadline_days,
                    'submit_limit': submit_limit,
                    'submit_deadline_days': submit_deadline_days,
                    'expired_date_days': expired_date_days,
                })
            
            try:
                # Parse numeric fields with defaults for drafts
                amount_per_person_decimal = Decimal(amount_per_person) if amount_per_person else Decimal('0.00')
                max_responses_int = int(max_responses) if max_responses else 1
                if max_responses_int < 1:
                    max_responses_int = 1
                
                # Calculate budget
                budget_decimal = amount_per_person_decimal * max_responses_int
                
                # Parse recruit_limit
                recruit_limit_int = int(recruit_limit) if recruit_limit else 10
                if recruit_limit_int < 1:
                    recruit_limit_int = 1
                
                # Parse submit_limit
                submit_limit_int = int(submit_limit) if submit_limit else 10
                if submit_limit_int < 1:
                    submit_limit_int = 1
                
                # Calculate deadlines
                recruit_deadline_days_int = int(recruit_deadline_days) if recruit_deadline_days else 7
                if recruit_deadline_days_int < 1:
                    recruit_deadline_days_int = 7
                
                submit_deadline_days_int = int(submit_deadline_days) if submit_deadline_days else 7
                if submit_deadline_days_int < 1:
                    submit_deadline_days_int = 7
                
                expired_date_days_int = int(expired_date_days) if expired_date_days else 14
                if expired_date_days_int < 1:
                    expired_date_days_int = 14
                
                now = timezone.now()
                recruit_deadline = now + timedelta(days=recruit_deadline_days_int) if recruit_deadline_days_int else None
                expired_date = now + timedelta(days=expired_date_days_int) if expired_date_days_int else None
                
                job = Job.objects.create(
                    title=title,
                    description=description or '',
                    target_language=target_language or 'en',
                    target_dialect=target_dialect,
                    deliverable_types=deliverable_types or 'text',
                    amount_per_person=amount_per_person_decimal,
                    budget=budget_decimal,
                    max_responses=max_responses_int,
                    recruit_limit=recruit_limit_int,
                    recruit_deadline=recruit_deadline,
                    submit_limit=submit_limit_int,
                    submit_deadline_days=submit_deadline_days_int,
                    expired_date=expired_date,
                    funder=request.user,
                    status='draft',
                    reference_audio=reference_audio,
                    reference_video=reference_video,
                    reference_image=reference_image
                )
                
                messages.success(request, _('Draft saved successfully! You can edit and publish it later.'))
                return redirect('jobs:edit', pk=job.pk)
            except ValueError as e:
                messages.error(request, _('Invalid numeric value: {error}').format(error=str(e)))
            except Exception as e:
                messages.error(request, _('Error saving draft: {error}').format(error=str(e)))
        else:
            # Publishing: require all fields
            if not deliverable_types_list:
                messages.error(request, _('Please select at least one deliverable type.'))
                return render(request, 'jobs/create_job.html', {
                    'title': title,
                    'description': description,
                    'target_language': target_language,
                    'target_dialect': target_dialect,
                    'deliverable_types_list': deliverable_types_list,
                    'amount_per_person': amount_per_person,
                    'max_responses': max_responses,
                    'recruit_limit': recruit_limit,
                    'recruit_deadline_days': recruit_deadline_days,
                    'submit_limit': submit_limit,
                    'submit_deadline_days': submit_deadline_days,
                    'expired_date_days': expired_date_days,
                })
            
            if title and description and target_language and deliverable_types and amount_per_person:
                try:
                    amount_per_person_decimal = Decimal(amount_per_person)
                    max_responses_int = int(max_responses)
                    if max_responses_int < 1:
                        max_responses_int = 1
                    
                    # Calculate budget
                    budget_decimal = amount_per_person_decimal * max_responses_int
                    
                    # Parse recruit_limit
                    recruit_limit_int = int(recruit_limit)
                    if recruit_limit_int < 1:
                        recruit_limit_int = 1
                    
                    # Parse submit_limit
                    submit_limit_int = int(submit_limit)
                    if submit_limit_int < 1:
                        submit_limit_int = 1
                    
                    # Calculate deadlines
                    recruit_deadline_days_int = int(recruit_deadline_days)
                    if recruit_deadline_days_int < 1:
                        recruit_deadline_days_int = 7
                    
                    submit_deadline_days_int = int(submit_deadline_days)
                    if submit_deadline_days_int < 1:
                        submit_deadline_days_int = 7
                    
                    expired_date_days_int = int(expired_date_days)
                    if expired_date_days_int < 1:
                        expired_date_days_int = 14
                    
                    now = timezone.now()
                    recruit_deadline = now + timedelta(days=recruit_deadline_days_int)
                    expired_date = now + timedelta(days=expired_date_days_int)
                    
                    job = Job.objects.create(
                        title=title,
                        description=description,
                        target_language=target_language,
                        target_dialect=target_dialect,
                        deliverable_types=deliverable_types,
                        amount_per_person=amount_per_person_decimal,
                        budget=budget_decimal,
                        max_responses=max_responses_int,
                        recruit_limit=recruit_limit_int,
                        recruit_deadline=recruit_deadline,
                        submit_limit=submit_limit_int,
                        submit_deadline_days=submit_deadline_days_int,
                        expired_date=expired_date,
                        funder=request.user,
                        status='recruiting',
                        reference_audio=reference_audio,
                        reference_video=reference_video,
                        reference_image=reference_image
                    )
                    
                    messages.success(request, _('Job created successfully! It will be published for recruiting.'))
                    return redirect('jobs:detail', pk=job.pk)
                except ValueError:
                    messages.error(request, _('Invalid amount per person.'))
                except Exception as e:
                    messages.error(request, _('Error creating job: {error}').format(error=str(e)))
            else:
                messages.error(request, _('Please fill in all required fields.'))
    
    return render(request, 'jobs/create_job.html')


@login_required
def edit_job(request, pk):
    """Edit a draft job or update an existing job."""
    job = get_object_or_404(Job, pk=pk, funder=request.user)
    
    # Only allow editing drafts or jobs that haven't started recruiting yet
    if job.status not in ['draft', 'recruiting']:
        messages.warning(request, _('This job cannot be edited in its current state.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        target_language = request.POST.get('target_language', '')
        target_dialect = request.POST.get('target_dialect', '')
        deliverable_types_list = request.POST.getlist('deliverable_types')
        deliverable_types = ','.join(deliverable_types_list) if deliverable_types_list else ''
        amount_per_person = request.POST.get('amount_per_person', '')
        max_responses = request.POST.get('max_responses', '1')
        recruit_limit = request.POST.get('recruit_limit', '10')
        recruit_deadline_days = request.POST.get('recruit_deadline_days', '7')
        submit_limit = request.POST.get('submit_limit', '10')
        submit_deadline_days = request.POST.get('submit_deadline_days', '7')
        expired_date_days = request.POST.get('expired_date_days', '14')
        reference_audio = request.FILES.get('reference_audio')
        reference_video = request.FILES.get('reference_video')
        reference_image = request.FILES.get('reference_image')
        
        # Check if this is a draft save or publish
        is_draft = 'save_draft' in request.POST
        is_publish = 'publish' in request.POST
        
        # For drafts, allow saving with minimal data (just title)
        # For publishing, require all fields
        if is_draft:
            # Draft: only require title, allow partial data
            if not title:
                messages.error(request, _('Please provide at least a title for the draft.'))
                return render(request, 'jobs/edit_job.html', {
                    'job': job,
                    'title': title,
                    'description': description,
                    'target_language': target_language,
                    'target_dialect': target_dialect,
                    'deliverable_types_list': deliverable_types_list,
                    'amount_per_person': amount_per_person,
                    'max_responses': max_responses,
                    'recruit_limit': recruit_limit,
                    'recruit_deadline_days': recruit_deadline_days,
                    'submit_limit': submit_limit,
                    'submit_deadline_days': submit_deadline_days,
                    'expired_date_days': expired_date_days,
                })
            
            try:
                # Parse numeric fields with defaults for drafts
                amount_per_person_decimal = Decimal(amount_per_person) if amount_per_person else Decimal('0.00')
                max_responses_int = int(max_responses) if max_responses else 1
                if max_responses_int < 1:
                    max_responses_int = 1
                
                # Calculate budget
                budget_decimal = amount_per_person_decimal * max_responses_int
                
                # Parse recruit_limit
                recruit_limit_int = int(recruit_limit) if recruit_limit else 10
                if recruit_limit_int < 1:
                    recruit_limit_int = 1
                
                # Parse submit_limit
                submit_limit_int = int(submit_limit) if submit_limit else 10
                if submit_limit_int < 1:
                    submit_limit_int = 1
                
                # Calculate deadlines
                recruit_deadline_days_int = int(recruit_deadline_days) if recruit_deadline_days else 7
                if recruit_deadline_days_int < 1:
                    recruit_deadline_days_int = 7
                
                submit_deadline_days_int = int(submit_deadline_days) if submit_deadline_days else 7
                if submit_deadline_days_int < 1:
                    submit_deadline_days_int = 7
                
                expired_date_days_int = int(expired_date_days) if expired_date_days else 14
                if expired_date_days_int < 1:
                    expired_date_days_int = 14
                
                now = timezone.now()
                recruit_deadline = now + timedelta(days=recruit_deadline_days_int) if recruit_deadline_days_int else None
                expired_date = now + timedelta(days=expired_date_days_int) if expired_date_days_int else None
                
                # Update job fields
                job.title = title
                job.description = description or ''
                job.target_language = target_language or 'en'
                job.target_dialect = target_dialect
                job.deliverable_types = deliverable_types or 'text'
                job.amount_per_person = amount_per_person_decimal
                job.budget = budget_decimal
                job.max_responses = max_responses_int
                job.recruit_limit = recruit_limit_int
                job.recruit_deadline = recruit_deadline
                job.submit_limit = submit_limit_int
                job.submit_deadline_days = submit_deadline_days_int
                job.expired_date = expired_date
                
                # Update file fields only if new files are provided
                if reference_audio:
                    job.reference_audio = reference_audio
                if reference_video:
                    job.reference_video = reference_video
                if reference_image:
                    job.reference_image = reference_image
                
                job.status = 'draft'
                job.save()
                
                messages.success(request, _('Draft saved successfully!'))
                return redirect('jobs:edit', pk=job.pk)
            except ValueError as e:
                messages.error(request, _('Invalid numeric value: {error}').format(error=str(e)))
            except Exception as e:
                messages.error(request, _('Error saving draft: {error}').format(error=str(e)))
        elif is_publish:
            # Publishing: require all fields
            if not deliverable_types_list:
                messages.error(request, _('Please select at least one deliverable type.'))
                return render(request, 'jobs/edit_job.html', {
                    'job': job,
                    'title': title,
                    'description': description,
                    'target_language': target_language,
                    'target_dialect': target_dialect,
                    'deliverable_types_list': deliverable_types_list,
                    'amount_per_person': amount_per_person,
                    'max_responses': max_responses,
                    'recruit_limit': recruit_limit,
                    'recruit_deadline_days': recruit_deadline_days,
                    'submit_limit': submit_limit,
                    'submit_deadline_days': submit_deadline_days,
                    'expired_date_days': expired_date_days,
                })
            
            if title and description and target_language and deliverable_types and amount_per_person:
                try:
                    amount_per_person_decimal = Decimal(amount_per_person)
                    max_responses_int = int(max_responses)
                    if max_responses_int < 1:
                        max_responses_int = 1
                    
                    # Calculate budget
                    budget_decimal = amount_per_person_decimal * max_responses_int
                    
                    # Parse recruit_limit
                    recruit_limit_int = int(recruit_limit)
                    if recruit_limit_int < 1:
                        recruit_limit_int = 1
                    
                    # Parse submit_limit
                    submit_limit_int = int(submit_limit)
                    if submit_limit_int < 1:
                        submit_limit_int = 1
                    
                    # Calculate deadlines
                    recruit_deadline_days_int = int(recruit_deadline_days)
                    if recruit_deadline_days_int < 1:
                        recruit_deadline_days_int = 7
                    
                    submit_deadline_days_int = int(submit_deadline_days)
                    if submit_deadline_days_int < 1:
                        submit_deadline_days_int = 7
                    
                    expired_date_days_int = int(expired_date_days)
                    if expired_date_days_int < 1:
                        expired_date_days_int = 14
                    
                    now = timezone.now()
                    recruit_deadline = now + timedelta(days=recruit_deadline_days_int)
                    expired_date = now + timedelta(days=expired_date_days_int)
                    
                    # Update job fields
                    job.title = title
                    job.description = description
                    job.target_language = target_language
                    job.target_dialect = target_dialect
                    job.deliverable_types = deliverable_types
                    job.amount_per_person = amount_per_person_decimal
                    job.budget = budget_decimal
                    job.max_responses = max_responses_int
                    job.recruit_limit = recruit_limit_int
                    job.recruit_deadline = recruit_deadline
                    job.submit_limit = submit_limit_int
                    job.submit_deadline_days = submit_deadline_days_int
                    job.expired_date = expired_date
                    
                    # Update file fields only if new files are provided
                    if reference_audio:
                        job.reference_audio = reference_audio
                    if reference_video:
                        job.reference_video = reference_video
                    if reference_image:
                        job.reference_image = reference_image
                    
                    job.status = 'recruiting'
                    job.save()
                    
                    messages.success(request, _('Job published successfully! It is now available for recruiting.'))
                    return redirect('jobs:detail', pk=job.pk)
                except ValueError:
                    messages.error(request, _('Invalid amount per person.'))
                except Exception as e:
                    messages.error(request, _('Error publishing job: {error}').format(error=str(e)))
            else:
                messages.error(request, _('Please fill in all required fields to publish.'))
        else:
            messages.error(request, _('Invalid action.'))
    
    # GET request - show edit form
    # Calculate days from now for deadlines, or use defaults
    now = timezone.now()
    recruit_deadline_days_value = 7
    if job.recruit_deadline:
        days_diff = (job.recruit_deadline - now).days
        if days_diff > 0:
            recruit_deadline_days_value = days_diff
    
    expired_date_days_value = 14
    if job.expired_date:
        days_diff = (job.expired_date - now).days
        if days_diff > 0:
            expired_date_days_value = days_diff
    
    context = {
        'job': job,
        'title': job.title,
        'description': job.description,
        'target_language': job.target_language,
        'target_dialect': job.target_dialect,
        'deliverable_types_list': job.get_deliverable_types_list(),
        'amount_per_person': str(job.amount_per_person) if job.amount_per_person else '',
        'max_responses': job.max_responses,
        'recruit_limit': job.recruit_limit,
        'recruit_deadline_days': recruit_deadline_days_value,
        'submit_limit': job.submit_limit,
        'submit_deadline_days': job.submit_deadline_days,
        'expired_date_days': expired_date_days_value,
    }
    return render(request, 'jobs/edit_job.html', context)


@login_required
def submit_job(request, pk):
    """Submit work for a job."""
    job = get_object_or_404(Job, pk=pk)
    
    # Check if job is already completed
    if job.status == 'complete':
        messages.error(request, _('This job has been completed and is no longer accepting submissions.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Only allow submissions when job is in submitting state
    if job.status != 'submitting':
        messages.error(request, _('This job is not currently accepting submissions.'))
        return redirect('jobs:detail', pk=job.pk)
    
    # Check if submit limit or deadline has been reached
    if job.should_transition_to_reviewing():
        messages.error(request, _('This job has reached its submission limit or deadline. Submissions are no longer being accepted.'))
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
        
        # Refresh job to check if it should transition to reviewing
        # Need to refresh to get updated submission count
        job.refresh_from_db()
        if job.should_transition_to_reviewing():
            job.status = 'reviewing'
            job.save(update_fields=['status'])
        
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
    # If we've reached max responses, move to reviewing (or complete if all are already reviewed)
    new_status = None
    if job.has_reached_max_responses():
        # Check if we have submissions that need review
        if job.submissions.filter(status='pending').exists():
            new_status = 'reviewing'
        else:
            # All submissions are accepted/rejected, job is complete
            new_status = 'complete'
    elif job.status == 'submitting':
        # First submission received, move to reviewing
        new_status = 'reviewing'
    
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
        if job.status in ['submitting', 'reviewing', 'complete', 'completed']
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
    if not request.user.is_creator():
        messages.error(request, _('You do not have permission to view this page.'))
        return redirect('jobs:list')
    
    # Get jobs where user has accepted submissions that aren't completed
    accepted_submissions = JobSubmission.objects.filter(
        creator=request.user,
        status='accepted'
    ).select_related('job').order_by('-created_at')
    
    # Filter to only show jobs that aren't completed
    pending = [sub for sub in accepted_submissions if sub.job.status != 'complete']
    
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
    
    if job.status == 'complete':
        messages.info(request, _('This job is already marked as completed.'))
        return redirect('jobs:owner_dashboard')
    
    if job.submissions.filter(status='accepted').count() == 0:
        messages.warning(request, _('You need at least one accepted submission before completing a job.'))
        return redirect('jobs:owner_dashboard')
    
    job.status = 'complete'
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
    
    # Only allow applications when job is in recruiting state
    if job.status != 'recruiting':
        messages.warning(request, _('This job is not currently accepting applications.'))
        return redirect('jobs:detail', pk=job.pk)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            
            # If no files provided in form, copy from user profile
            if 'profile_audio' not in request.FILES and request.user.profile_audio:
                application.profile_audio = request.user.profile_audio
            if 'profile_video' not in request.FILES and request.user.profile_video:
                application.profile_video = request.user.profile_video
            if 'profile_image' not in request.FILES and request.user.profile_image:
                application.profile_image = request.user.profile_image
            
            application.save()
            
            # Check if job should auto-transition to selecting
            job.refresh_from_db()
            if job.should_transition_to_selecting():
                job.status = 'selecting'
                job.save(update_fields=['status'])
                messages.success(request, _('Your application has been submitted! The job has reached its recruit limit and moved to selection phase.'))
            else:
                messages.success(request, _('Your application has been submitted! The job owner will review it.'))
            return redirect('jobs:detail', pk=job.pk)
    else:
        form = JobApplicationForm(user=request.user)
    
    context = {
        'job': job,
        'form': form,
        'user': request.user,
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
