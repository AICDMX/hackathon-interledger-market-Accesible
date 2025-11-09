from decimal import Decimal
from datetime import timedelta

from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from users.models import User


class Job(models.Model):
    """Job/Brief model for funders to post work."""
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('recruiting', _('Recruiting')),
        ('selecting', _('Selecting')),
        ('submitting', _('Submitting')),
        ('reviewing', _('Reviewing')),
        ('expired', _('Expired')),
        ('complete', _('Complete')),
    ]
    
    DELIVERABLE_CHOICES = [
        ('text', _('Text')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('image', _('Image')),
    ]
    
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    title_audio = models.FileField(
        upload_to='jobs/title_audio/',
        blank=True,
        null=True,
        verbose_name=_('Title Audio'),
        help_text=_('Optional audio file for the title in the target language')
    )
    description = models.TextField(verbose_name=_('Description'))
    
    # Language information
    target_language = models.CharField(
        max_length=10,
        verbose_name=_('Target Language'),
        help_text=_('Language code (e.g., nah, oto, es)')
    )
    target_dialect = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Target Dialect'),
        help_text=_('Specific dialect if applicable')
    )
    
    # Deliverable types (can be multiple)
    deliverable_types = models.CharField(
        max_length=50,
        verbose_name=_('Deliverable Types'),
        help_text=_('Comma-separated: text,video,audio,image')
    )
    reference_audio = models.FileField(
        upload_to='jobs/reference/audio/',
        blank=True,
        null=True,
        verbose_name=_('Reference Audio/Instructions'),
        help_text=_('Optional audio instructions uploaded or recorded by the funder')
    )
    reference_video = models.FileField(
        upload_to='jobs/reference/video/',
        blank=True,
        null=True,
        verbose_name=_('Reference Video'),
        help_text=_('Optional video instructions or inspiration for the job')
    )
    reference_image = models.ImageField(
        upload_to='jobs/reference/images/',
        blank=True,
        null=True,
        verbose_name=_('Reference Image'),
        help_text=_('Optional image reference or mood board for the job')
    )
    
    amount_per_person = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Amount Per Person'),
        help_text=_('Amount in pesos to pay each person who completes this job')
    )
    
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Budget'),
        help_text=_('Total amount in pesos (calculated as amount_per_person ? max_responses)')
    )
    
    funder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posted_jobs',
        verbose_name=_('Funder')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Payment ID'),
        help_text=_('Interledger payment ID for contract/escrow')
    )
    
    contract_completed = models.BooleanField(
        default=False,
        verbose_name=_('Contract Completed'),
        help_text=_('Whether the contract/payment has been completed/released')
    )
    
    # Response limit
    max_responses = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Maximum Responses'),
        help_text=_('Number of responses/submissions needed for this job (e.g., if you want 20 people to do the same voice or picture set)')
    )
    
    # Recruiting limits
    recruit_limit = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Recruit Limit'),
        help_text=_('Maximum number of applications to accept before automatically moving to selection phase')
    )
    recruit_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Recruit Deadline'),
        help_text=_('Date and time when recruiting will automatically end and move to selection phase (default: 7 days from creation)')
    )
    
    # Submitting limits
    submit_limit = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Submit Limit'),
        help_text=_('Maximum number of submissions to accept before automatically moving to review phase')
    )
    submit_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Submit Deadline'),
        help_text=_('Date and time when submitting will automatically end and move to review phase (default: 7 days from when submitting phase starts)')
    )
    submit_deadline_days = models.PositiveIntegerField(
        default=7,
        verbose_name=_('Submit Deadline Days'),
        help_text=_('Number of days from when submitting phase starts until deadline (used to calculate submit_deadline when job transitions to submitting state)')
    )
    
    expired_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expired Date'),
        help_text=_('Date and time when the job will expire if no applications (in recruiting) or no submissions (in submitting) are received. Wallet contracts expire 7 days after this date.')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Job')
        verbose_name_plural = _('Jobs')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('jobs:detail', kwargs={'pk': self.pk})
    
    def get_deliverable_types_list(self):
        """Return deliverable types as a list."""
        return [dt.strip() for dt in self.deliverable_types.split(',')]
    
    def get_deliverable_types_display(self):
        """Return deliverable types as a formatted string with display names."""
        types_list = self.get_deliverable_types_list()
        display_names = []
        choices_dict = dict(self.DELIVERABLE_CHOICES)
        for dt in types_list:
            display_names.append(str(choices_dict.get(dt, dt)))
        return ', '.join(display_names)
    
    def get_accepted_submission(self):
        """Get the accepted submission if any."""
        return self.submissions.filter(status='accepted').first()
    
    def get_accepted_submissions_count(self):
        """Get count of accepted submissions."""
        return self.submissions.filter(status='accepted').count()
    
    def get_pending_submissions_count(self):
        """Get count of pending submissions."""
        return self.submissions.filter(status='pending').count()
    
    def has_reached_max_responses(self):
        """Check if the job has reached its maximum number of accepted responses."""
        return self.get_accepted_submissions_count() >= self.max_responses
    
    def get_remaining_responses_needed(self):
        """Get the number of responses still needed."""
        accepted = self.get_accepted_submissions_count()
        remaining = self.max_responses - accepted
        return max(0, remaining)
    
    def has_reference_media(self):
        """Return True if funder added any supporting media."""
        return any([
            self.reference_audio,
            self.reference_video,
            self.reference_image,
        ])
    
    def get_applications_count(self):
        """Get count of all applications for this job."""
        return self.applications.count()
    
    def has_reached_recruit_limit(self):
        """Check if the job has reached its recruit limit."""
        return self.get_applications_count() >= self.recruit_limit
    
    def has_passed_recruit_deadline(self):
        """Check if the recruit deadline has passed."""
        if not self.recruit_deadline:
            return False
        return timezone.now() >= self.recruit_deadline
    
    def should_transition_to_selecting(self):
        """Check if job should automatically transition from recruiting to selecting."""
        if self.status != 'recruiting':
            return False
        return self.has_reached_recruit_limit() or self.has_passed_recruit_deadline()
    
    def get_submissions_count(self):
        """Get count of all submissions for this job."""
        return self.submissions.count()
    
    def has_reached_submit_limit(self):
        """Check if the job has reached its submit limit."""
        return self.get_submissions_count() >= self.submit_limit
    
    def has_passed_submit_deadline(self):
        """Check if the submit deadline has passed."""
        if not self.submit_deadline:
            return False
        return timezone.now() >= self.submit_deadline
    
    def should_transition_to_reviewing(self):
        """Check if job should automatically transition from submitting to reviewing."""
        if self.status != 'submitting':
            return False
        return self.has_reached_submit_limit() or self.has_passed_submit_deadline()
    
    def has_passed_expired_date(self):
        """Check if the expired date has passed."""
        if not self.expired_date:
            return False
        return timezone.now() >= self.expired_date
    
    def should_expire(self):
        """Check if job should expire based on expired_date and current state."""
        if not self.has_passed_expired_date():
            return False
        
        # If in recruiting state and no applications, expire
        if self.status == 'recruiting':
            return self.get_applications_count() == 0
        
        # If in submitting state and no submissions, expire
        if self.status == 'submitting':
            return self.get_submissions_count() == 0
        
        return False
    
    def save(self, *args, **kwargs):
        """Override save to set default deadlines if not provided."""
        # Set default recruit_deadline to 7 days from creation if not set and this is a new job
        is_new = not self.pk
        if is_new and not self.recruit_deadline:
            self.recruit_deadline = timezone.now() + timedelta(days=7)
        
        # Set default submit_deadline when transitioning to submitting state
        # Check if status is being changed to 'submitting'
        if self.pk:
            old_job = Job.objects.filter(pk=self.pk).first()
            if old_job and old_job.status != 'submitting' and self.status == 'submitting':
                # Transitioning to submitting state - set deadline if not already set
                if not self.submit_deadline:
                    # Use submit_deadline_days to calculate the deadline
                    days = self.submit_deadline_days if self.submit_deadline_days else 7
                    self.submit_deadline = timezone.now() + timedelta(days=days)
        elif self.status == 'submitting' and not self.submit_deadline:
            # New job created directly in submitting state
            days = self.submit_deadline_days if self.submit_deadline_days else 7
            self.submit_deadline = timezone.now() + timedelta(days=days)
        
        # Save the job first
        super().save(*args, **kwargs)
        
        # Auto-transition from recruiting to selecting if conditions are met
        # Only check after initial save to avoid recursion
        if self.should_transition_to_selecting():
            # Use update to avoid recursion
            Job.objects.filter(pk=self.pk).update(status='selecting')
            self.status = 'selecting'
        
        # Auto-transition from submitting to reviewing if conditions are met
        if self.should_transition_to_reviewing():
            # Use update to avoid recursion
            Job.objects.filter(pk=self.pk).update(status='reviewing')
            self.status = 'reviewing'
        
        # Auto-transition to expired if conditions are met
        if self.should_expire():
            # Use update to avoid recursion
            Job.objects.filter(pk=self.pk).update(status='expired')
            self.status = 'expired'


class JobSubmission(models.Model):
    """Submission model for creators to submit work for jobs."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('rejected', _('Rejected')),
    ]
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Job')
    )
    
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Creator')
    )
    
    note = models.TextField(
        blank=True,
        verbose_name=_('Note'),
        help_text=_('Additional notes about the submission')
    )
    
    # File uploads
    text_file = models.FileField(
        upload_to='submissions/text/',
        blank=True,
        null=True,
        verbose_name=_('Text File')
    )
    text_content = models.TextField(
        blank=True,
        verbose_name=_('Text Content'),
        help_text=_('Text content entered directly (alternative to file upload)')
    )
    video_file = models.FileField(
        upload_to='submissions/video/',
        blank=True,
        null=True,
        verbose_name=_('Video File')
    )
    audio_file = models.FileField(
        upload_to='submissions/audio/',
        blank=True,
        null=True,
        verbose_name=_('Audio File')
    )
    image_file = models.ImageField(
        upload_to='submissions/images/',
        blank=True,
        null=True,
        verbose_name=_('Image File')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Job Submission')
        verbose_name_plural = _('Job Submissions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.creator.username} - {self.job.title}"
    
    is_complete = models.BooleanField(
        default=False,
        verbose_name=_('Work Complete'),
        help_text=_('Whether the creator has marked their work as complete')
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed At'),
        help_text=_('When the creator marked their work as complete')
    )


class JobApplication(models.Model):
    """Application model for workers to submit their profile/interest in a job."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('selected', _('Selected')),
        ('rejected', _('Rejected')),
    ]
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('Job')
    )
    
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        verbose_name=_('Applicant')
    )
    
    profile_note = models.TextField(
        blank=True,
        verbose_name=_('Profile Note'),
        help_text=_('Tell the job owner about yourself and why you are interested')
    )
    
    # Optional profile files
    profile_audio = models.FileField(
        upload_to='applications/audio/',
        blank=True,
        null=True,
        verbose_name=_('Profile Audio'),
        help_text=_('Optional audio introduction')
    )
    profile_video = models.FileField(
        upload_to='applications/video/',
        blank=True,
        null=True,
        verbose_name=_('Profile Video'),
        help_text=_('Optional video introduction')
    )
    profile_image = models.ImageField(
        upload_to='applications/images/',
        blank=True,
        null=True,
        verbose_name=_('Profile Image'),
        help_text=_('Optional profile image')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Job Application')
        verbose_name_plural = _('Job Applications')
        ordering = ['-created_at']
        unique_together = [['job', 'applicant']]
    
    def __str__(self):
        return f"{self.applicant.get_display_name()} - {self.job.title}"
