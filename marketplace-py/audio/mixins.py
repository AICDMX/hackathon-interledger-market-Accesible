"""
Audio mixin and helper functions for models that support audio snippets.
"""
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
from .models import AudioSnippet, AudioRequest, StaticUIElement


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


def get_audio_with_fallback(content_object, target_field, preferred_language_code=None, status='ready', use_cache=True):
    """
    Get audio snippet with language fallback chain.
    
    Tries in order:
    1. User's preferred language
    2. Language fallback (FALLBACK_TEXT_LANGUAGE from settings)
    3. Final fallback (LANGUAGE_CODE from settings)
    
    Args:
        content_object: Any model instance
        target_field: The field/UI element name
        preferred_language_code: User's preferred language code (optional)
        status: Filter by status (default: 'ready')
        use_cache: Whether to use cache (default: True)
    
    Returns:
        Tuple of (AudioSnippet instance or None, actual_language_code_used)
    """
    # Build fallback chain
    fallback_chain = []
    
    # 1. User's preferred language
    if preferred_language_code:
        fallback_chain.append(preferred_language_code)
    
    # 2. Language fallback from settings
    fallback_language = getattr(settings, 'FALLBACK_TEXT_LANGUAGE', None)
    if fallback_language and fallback_language not in fallback_chain:
        fallback_chain.append(fallback_language)
    
    # 3. Final fallback (default language)
    final_fallback = settings.LANGUAGE_CODE
    if final_fallback not in fallback_chain:
        fallback_chain.append(final_fallback)
    
    # Try each language in the fallback chain
    for lang_code in fallback_chain:
        audio_snippet = get_audio_for_content(
            content_object, 
            target_field, 
            lang_code, 
            status=status, 
            use_cache=use_cache
        )
        if audio_snippet:
            return audio_snippet, lang_code
    
    # No audio found in any language
    return None, fallback_chain[0] if fallback_chain else settings.LANGUAGE_CODE


def get_fallback_audio_url(language_code=None, request=None):
    """
    Get the fallback audio URL for a given language.
    
    Args:
        language_code: Language code (e.g., 'oto', 'nah'). If None, uses generic fallback.
        request: Django request object (optional, for building absolute URLs)
    
    Returns:
        URL string for the fallback audio file
    """
    from django.templatetags.static import static
    from django.contrib.staticfiles.storage import staticfiles_storage
    
    # Get language-specific fallback if available
    fallback_by_language = getattr(settings, 'AUDIO_FALLBACK_BY_LANGUAGE', {})
    fallback_path = fallback_by_language.get(language_code) if language_code else None
    
    # If no language-specific fallback, use generic one
    if not fallback_path:
        fallback_path = getattr(settings, 'AUDIO_FALLBACK_FILE', 'audio/fallback.mp3')
    
    # Build URL
    if request:
        return request.build_absolute_uri(staticfiles_storage.url(fallback_path))
    else:
        return static(fallback_path)


def get_audio_for_static_ui(slug, target_field='label', language_code=None, preferred_language_code=None, status='ready', use_cache=True):
    """
    Get audio snippet for a static UI element by slug.
    
    Args:
        slug: The slug identifier for the UI element (e.g., 'dashboard_my_money')
        target_field: The target field name (default: 'label')
        language_code: Specific language code (if provided, uses that directly)
        preferred_language_code: User's preferred language (used for fallback if language_code not provided)
        status: Filter by status (default: 'ready')
        use_cache: Whether to use cache (default: True)
    
    Returns:
        AudioSnippet instance or None (or tuple with language_code if preferred_language_code provided)
    """
    try:
        ui_element = StaticUIElement.objects.get(slug=slug)
    except StaticUIElement.DoesNotExist:
        return None if not preferred_language_code else (None, None)
    
    content_type = ContentType.objects.get_for_model(StaticUIElement)
    
    if language_code:
        # Use specific language code
        return get_audio_for_content(ui_element, target_field, language_code, status, use_cache)
    elif preferred_language_code:
        # Use fallback chain
        return get_audio_with_fallback(ui_element, target_field, preferred_language_code, status, use_cache)
    else:
        # Try with fallback chain using settings
        return get_audio_with_fallback(ui_element, target_field, None, status, use_cache)
