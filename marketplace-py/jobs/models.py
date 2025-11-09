from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from users.models import User


class Job(models.Model):
    """Job/Brief model for funders to post work."""
    
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('in_review', _('In Review')),
        ('funded', _('Funded')),
        ('rejected', _('Rejected')),
        ('waiting_completion', _('Waiting Completion')),
        ('completed', _('Completed')),
    ]
    
    DELIVERABLE_CHOICES = [
        ('text', _('Text')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('image', _('Image')),
    ]
    
    title = models.CharField(max_length=200, verbose_name=_('Title'))
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
        help_text=_('Amount in ILP to pay each person who completes this job')
    )
    
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Budget'),
        help_text=_('Total amount in ILP (calculated as amount_per_person ? max_responses)')
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
        default='open',
        verbose_name=_('Status')
    )
    
    # Funding information
    funded_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Funded Amount'),
        help_text=_('Amount that has been funded in ILP')
    )
    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Payment ID'),
        help_text=_('Interledger payment ID for escrow')
    )
    is_funded = models.BooleanField(
        default=False,
        verbose_name=_('Is Funded'),
        help_text=_('Whether the job has been fully funded')
    )
    
    # Response limit
    max_responses = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Maximum Responses'),
        help_text=_('Number of responses/submissions needed for this job (e.g., if you want 20 people to do the same voice or picture set)')
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
    
    def get_funded_amount(self):
        """Return total amount pledged toward this job."""
        total = self.fundings.aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')
    
    def is_fully_funded(self):
        """Convenience flag to indicate the budget has been met."""
        try:
            return self.get_funded_amount() >= self.budget
        except TypeError:
            return False
    
    def remaining_budget(self):
        """Return how much budget is still unfunded."""
        cached_value = getattr(self, '_remaining_budget_cache', None)
        if cached_value is not None:
            return cached_value
        total = self.get_funded_amount()
        remaining = self.budget - total
        if remaining <= Decimal('0.00'):
            remaining = Decimal('0.00')
        self._remaining_budget_cache = remaining
        return remaining
    
    def has_remaining_budget(self):
        """Check if the job can still accept additional funding."""
        return self.remaining_budget() > Decimal('0.00')
    
    def has_reference_media(self):
        """Return True if funder added any supporting media."""
        return any([
            self.reference_audio,
            self.reference_video,
            self.reference_image,
        ])
    
    def refresh_funding_snapshot(self):
        """Sync stored funded amount + flag with recorded pledges."""
        total = self.get_funded_amount()
        fields_to_update = []
        if self.funded_amount != total:
            self.funded_amount = total
            fields_to_update.append('funded_amount')
        is_fully_funded = total >= self.budget
        if self.is_funded != is_fully_funded:
            self.is_funded = is_fully_funded
            fields_to_update.append('is_funded')
        if fields_to_update:
            self.save(update_fields=fields_to_update)


class JobFunding(models.Model):
    """Tracks pledges made toward a job budget."""
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='fundings',
        verbose_name=_('Job')
    )
    
    funder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_fundings',
        verbose_name=_('Funder')
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Amount'),
        help_text=_('Amount pledged in ILP tokens')
    )
    
    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Note'),
        help_text=_('Optional note for context (shown on job page)')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Job Funding')
        verbose_name_plural = _('Job Fundings')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.funder.username} -> {self.job.title} ({self.amount})"


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
        return f"{self.applicant.username} - {self.job.title}"
