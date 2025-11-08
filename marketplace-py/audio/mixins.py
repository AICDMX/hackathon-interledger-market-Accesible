"""
Audio mixin and helper functions for models that support audio snippets.
"""
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
from .models import AudioSnippet, AudioRequest


class AudioMixin:
    """
    Mixin to add audio functionality to any model.
    
    Usage:
        class MyModel(AudioMixin, models.Model):
            title = models.CharField(max_length=200)
            description = models.TextField()
            
        # Then use:
        obj = MyModel.objects.get(pk=1)
        audio = obj.get_audio_snippet('title', 'en')
        obj.request_audio('description', 'nah')
    """
    
    def get_audio_snippet(self, target_field, language_code, status='ready', use_cache=True):
        """
        Get an audio snippet for this object.
        
        Args:
            target_field: The field/UI element name (e.g., 'title', 'description')
            language_code: Language code (e.g., 'en', 'es', 'nah')
            status: Filter by status (default: 'ready')
            use_cache: Whether to use cache (default: True)
        
        Returns:
            AudioSnippet instance or None
        """
        if use_cache:
            cache_key = f'audio_snippet:{self._meta.label}:{self.pk}:{target_field}:{language_code}:{status}'
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        
        content_type = ContentType.objects.get_for_model(self)
        try:
            snippet = AudioSnippet.objects.get(
                content_type=content_type,
                object_id=self.pk,
                target_field=target_field,
                language_code=language_code,
                status=status
            )
            if use_cache:
                cache.set(cache_key, snippet, settings.AUDIO_CACHE_TIMEOUT)
            return snippet
        except AudioSnippet.DoesNotExist:
            if use_cache:
                cache.set(cache_key, None, settings.AUDIO_CACHE_TIMEOUT)
            return None
    
    def get_all_audio_snippets(self, language_code=None, status='ready'):
        """
        Get all audio snippets for this object.
        
        Args:
            language_code: Optional language code filter
            status: Filter by status (default: 'ready')
        
        Returns:
            QuerySet of AudioSnippet instances
        """
        content_type = ContentType.objects.get_for_model(self)
        queryset = AudioSnippet.objects.filter(
            content_type=content_type,
            object_id=self.pk,
            status=status
        )
        if language_code:
            queryset = queryset.filter(language_code=language_code)
        return queryset
    
    def has_audio(self, target_field, language_code, status='ready'):
        """
        Check if audio exists for a specific field and language.
        
        Args:
            target_field: The field/UI element name
            language_code: Language code
            status: Filter by status (default: 'ready')
        
        Returns:
            bool
        """
        return self.get_audio_snippet(target_field, language_code, status) is not None
    
    def request_audio(self, target_field, language_code, requested_by=None, notes=''):
        """
        Create an audio request for this object.
        
        Args:
            target_field: The field/UI element name that needs audio
            language_code: Language code for the requested audio
            requested_by: User who requested it (optional)
            notes: Optional notes about the request
        
        Returns:
            AudioRequest instance
        """
        content_type = ContentType.objects.get_for_model(self)
        
        # Check if there's already an open request
        existing_request = AudioRequest.objects.filter(
            content_type=content_type,
            object_id=self.pk,
            target_field=target_field,
            language_code=language_code,
            status__in=['open', 'in_progress']
        ).first()
        
        if existing_request:
            return existing_request
        
        # Create new request
        audio_request = AudioRequest.objects.create(
            content_type=content_type,
            object_id=self.pk,
            target_field=target_field,
            language_code=language_code,
            requested_by=requested_by,
            notes=notes
        )
        
        return audio_request
    
    def get_audio_request(self, target_field, language_code):
        """
        Get an open audio request for this object.
        
        Args:
            target_field: The field/UI element name
            language_code: Language code
        
        Returns:
            AudioRequest instance or None
        """
        content_type = ContentType.objects.get_for_model(self)
        try:
            return AudioRequest.objects.get(
                content_type=content_type,
                object_id=self.pk,
                target_field=target_field,
                language_code=language_code,
                status__in=['open', 'in_progress']
            )
        except AudioRequest.DoesNotExist:
            return None
    
    def clear_audio_cache(self):
        """Clear all cached audio snippets for this object."""
        content_type = ContentType.objects.get_for_model(self)
        # Clear cache for all possible combinations
        for snippet in AudioSnippet.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ):
            cache_key = f'audio_snippet:{self._meta.label}:{self.pk}:{snippet.target_field}:{snippet.language_code}:{snippet.status}'
            cache.delete(cache_key)


def get_audio_for_content(content_object, target_field, language_code, status='ready', use_cache=True):
    """
    Helper function to get audio snippet for any content object.
    
    Args:
        content_object: Any model instance
        target_field: The field/UI element name
        language_code: Language code
        status: Filter by status (default: 'ready')
        use_cache: Whether to use cache (default: True)
    
    Returns:
        AudioSnippet instance or None
    """
    if hasattr(content_object, 'get_audio_snippet'):
        return content_object.get_audio_snippet(target_field, language_code, status, use_cache)
    
    if use_cache:
        cache_key = f'audio_snippet:{content_object._meta.label}:{content_object.pk}:{target_field}:{language_code}:{status}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    
    content_type = ContentType.objects.get_for_model(content_object.__class__)
    try:
        snippet = AudioSnippet.objects.get(
            content_type=content_type,
            object_id=content_object.pk,
            target_field=target_field,
            language_code=language_code,
            status=status
        )
        if use_cache:
            cache.set(cache_key, snippet, settings.AUDIO_CACHE_TIMEOUT)
        return snippet
    except AudioSnippet.DoesNotExist:
        if use_cache:
            cache.set(cache_key, None, settings.AUDIO_CACHE_TIMEOUT)
        return None
