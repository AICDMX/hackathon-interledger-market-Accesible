from django.db import models
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
    
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Budget'),
        help_text=_('Amount in ILP')
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
    
    def get_accepted_submission(self):
        """Get the accepted submission if any."""
        return self.submissions.filter(status='accepted').first()


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
