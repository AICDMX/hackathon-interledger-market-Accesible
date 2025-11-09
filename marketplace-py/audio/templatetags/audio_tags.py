"""
Template tags for audio functionality.
"""
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static
from audio.mixins import get_audio_for_content, get_audio_with_fallback

register = template.Library()


@register.inclusion_tag('audio/audio_player.html', takes_context=True)
def audio_player(context, content_object, target_field, language_code=None):
    """
    Render an audio player for a content object.
    
    Uses language fallback chain:
    1. User's preferred language
    2. Language fallback (FALLBACK_TEXT_LANGUAGE)
    3. Final fallback (LANGUAGE_CODE)
    
    Usage:
        {% load audio_tags %}
        {% audio_player job "title" "en" %}
    
    Args:
        content_object: The model instance
        target_field: Field name (e.g., 'title', 'description')
        language_code: Optional language code (if provided, uses that instead of fallback chain)
    """
    # Get user's preferred language from context
    preferred_audio = context.get('preferred_audio_language')
    
    # If language_code is explicitly provided, use it directly
    # Otherwise, use fallback chain with user's preferred language
    if language_code is None:
        # Use fallback chain starting with user's preferred language
        audio_snippet, actual_language_code = get_audio_with_fallback(
            content_object, 
            target_field, 
            preferred_language_code=preferred_audio
        )
        language_code = actual_language_code
    else:
        # Use explicitly provided language code
        audio_snippet = get_audio_for_content(content_object, target_field, language_code)
    
    # Get content type info for API
    content_type = ContentType.objects.get_for_model(content_object.__class__)
    
    # Get fallback audio URL
    fallback_path = getattr(settings, 'AUDIO_FALLBACK_FILE', 'audio/fallback.mp3')
    request = context.get('request')
    if request:
        fallback_audio_url = request.build_absolute_uri(staticfiles_storage.url(fallback_path))
    else:
        fallback_audio_url = static(fallback_path)
    
    return {
        'audio_snippet': audio_snippet,
        'content_object': content_object,
        'content_type_id': content_type.pk,
        'object_id': content_object.pk,
        'target_field': target_field,
        'language_code': language_code,
        'fallback_audio_url': fallback_audio_url,
        'request': request,
    }


@register.simple_tag
def has_audio(content_object, target_field, language_code=None):
    """
    Check if audio exists for a content object.
    
    Usage:
        {% load audio_tags %}
        {% if has_audio job "title" "en" %}
            Audio available!
        {% endif %}
    """
    if language_code is None:
        from django.utils import translation
        language_code = translation.get_language()
    
    if hasattr(content_object, 'has_audio'):
        return content_object.has_audio(target_field, language_code)
    
    audio_snippet = get_audio_for_content(content_object, target_field, language_code)
    return audio_snippet is not None
