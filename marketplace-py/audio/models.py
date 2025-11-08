from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class AudioSnippet(models.Model):
    """
    Model to store audio files for any content object.
    Supports multiple audio snippets per object via target_field.
    """
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('ready', _('Ready')),
        ('needs_review', _('Needs Review')),
    ]
    
    # Generic foreign key to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content Type')
    )
    object_id = models.PositiveIntegerField(verbose_name=_('Object ID'))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Target field identifies which UI element/field this audio narrates
    # e.g., 'title', 'description', 'body', etc.
    target_field = models.CharField(
        max_length=100,
        verbose_name=_('Target Field'),
        help_text=_('Short slug identifying which field/UI element this audio narrates (e.g., title, description)')
    )
    
    # Language code (e.g., 'en', 'es', 'nah', 'oto', 'maz', 'que')
    language_code = models.CharField(
        max_length=10,
        verbose_name=_('Language Code'),
        help_text=_('Language code for this audio snippet')
    )
    
    # Transcript/transcription of the audio
    transcript = models.TextField(
        blank=True,
        verbose_name=_('Transcript'),
        help_text=_('Text transcription of the audio content')
    )
    
    # Status of the audio snippet
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    # Audio file (stored via FileField - can be configured for S3/R2/local)
    file = models.FileField(
        upload_to='audio/snippets/%Y/%m/%d/',
        verbose_name=_('Audio File'),
        help_text=_('Audio file (MP3, OGG, etc.)')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_audio_snippets',
        verbose_name=_('Created By')
    )
    
    class Meta:
        verbose_name = _('Audio Snippet')
        verbose_name_plural = _('Audio Snippets')
        ordering = ['-created_at']
        # Ensure uniqueness: one audio snippet per content object + target_field + language
        unique_together = ['content_type', 'object_id', 'target_field', 'language_code']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'target_field']),
            models.Index(fields=['language_code', 'status']),
        ]
    
    def __str__(self):
        return f"{self.content_object} - {self.target_field} ({self.language_code})"
    
    def get_audio_url(self):
        """Return the URL to the audio file."""
        if self.file:
            return self.file.url
        return None


class AudioRequest(models.Model):
    """
    Model to track requests for missing audio translations.
    Logs when audio is needed but doesn't exist yet.
    """
    
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('in_progress', _('In Progress')),
        ('fulfilled', _('Fulfilled')),
        ('closed', _('Closed')),
    ]
    
    # Generic foreign key to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content Type')
    )
    object_id = models.PositiveIntegerField(verbose_name=_('Object ID'))
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Target field that needs audio
    target_field = models.CharField(
        max_length=100,
        verbose_name=_('Target Field'),
        help_text=_('Field/UI element that needs audio (e.g., title, description)')
    )
    
    # Requested language code
    language_code = models.CharField(
        max_length=10,
        verbose_name=_('Language Code'),
        help_text=_('Language code for the requested audio')
    )
    
    # Status of the request
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name=_('Status')
    )
    
    # Optional notes/description
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes about this audio request')
    )
    
    # Who requested it
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audio_requests',
        verbose_name=_('Requested By')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Fulfilled At'))
    
    class Meta:
        verbose_name = _('Audio Request')
        verbose_name_plural = _('Audio Requests')
        ordering = ['-created_at']
        # Note: We allow multiple requests per content+field+language (e.g., one fulfilled, one open)
        # Application logic in request_audio() prevents duplicate open requests
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'target_field']),
            models.Index(fields=['language_code', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Audio request: {self.content_object} - {self.target_field} ({self.language_code})"
    
    def mark_fulfilled(self):
        """Mark this request as fulfilled."""
        from django.utils import timezone
        self.status = 'fulfilled'
        self.fulfilled_at = timezone.now()
        self.save()
