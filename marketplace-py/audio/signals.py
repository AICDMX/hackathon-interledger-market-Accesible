"""
Signals for the audio app.
Auto-close AudioRequests when AudioSnippets are created.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AudioSnippet, AudioRequest


@receiver(post_save, sender=AudioSnippet)
def auto_close_audio_requests(sender, instance, created, **kwargs):
    """
    When an AudioSnippet is created or updated to 'ready' status,
    automatically close any open AudioRequests for the same content.
    """
    if instance.status == 'ready':
        # Find and close any open requests for this content
        content_type = instance.content_type
        object_id = instance.object_id
        target_field = instance.target_field
        language_code = instance.language_code
        
        AudioRequest.objects.filter(
            content_type=content_type,
            object_id=object_id,
            target_field=target_field,
            language_code=language_code,
            status__in=['open', 'in_progress']
        ).update(status='fulfilled')
