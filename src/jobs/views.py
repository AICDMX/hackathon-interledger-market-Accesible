from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import Job, JobSubmission


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
