"""
Template tags for audio functionality.
"""
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static
from audio.mixins import get_audio_for_content, get_audio_with_fallback, get_audio_for_static_ui, get_fallback_audio_url

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
        'LANGUAGE_CODE': settings.LANGUAGE_CODE,
        'preferred_audio_language': preferred_audio,
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


@register.inclusion_tag('audio/audio_player.html', takes_context=True)
def audio_player_static_ui(context, slug, target_field='label', language_code=None):
    """
    Render an audio player for a static UI element by slug.
    
    Uses language fallback chain:
    1. User's preferred language
    2. Language fallback (FALLBACK_TEXT_LANGUAGE)
    3. Final fallback (LANGUAGE_CODE)
    
    Usage:
        {% load audio_tags %}
        {% audio_player_static_ui "dashboard_my_money" %}
        {% audio_player_static_ui "form_password" "label" "oto" %}
    
    Args:
        slug: The slug identifier for the UI element (e.g., 'dashboard_my_money')
        target_field: Field name (default: 'label')
        language_code: Optional language code (if provided, uses that instead of fallback chain)
    """
    from audio.models import StaticUIElement
    
    # Get user's preferred language from context
    preferred_audio = context.get('preferred_audio_language')
    
    # Get the StaticUIElement
    try:
        ui_element = StaticUIElement.objects.get(slug=slug)
    except StaticUIElement.DoesNotExist:
        return {
            'audio_snippet': None,
            'content_object': None,
            'content_type_id': None,
            'object_id': None,
            'target_field': target_field,
            'language_code': language_code or preferred_audio or settings.LANGUAGE_CODE,
            'fallback_audio_url': None,
            'request': context.get('request'),
            'LANGUAGE_CODE': settings.LANGUAGE_CODE,
            'preferred_audio_language': preferred_audio,
        }
    
    # If language_code is explicitly provided, use it directly
    # Otherwise, use fallback chain with user's preferred language
    if language_code is None:
        # Use fallback chain starting with user's preferred language
        audio_snippet, actual_language_code = get_audio_with_fallback(
            ui_element, 
            target_field, 
            preferred_language_code=preferred_audio
        )
        language_code = actual_language_code
    else:
        # Use explicitly provided language code
        audio_snippet = get_audio_for_content(ui_element, target_field, language_code)
    
    # Get content type info for API
    content_type = ContentType.objects.get_for_model(StaticUIElement)
    
    # Get fallback audio URL (language-specific if available)
    request = context.get('request')
    fallback_audio_url = get_fallback_audio_url(language_code, request)
    
    return {
        'audio_snippet': audio_snippet,
        'content_object': ui_element,
        'content_type_id': content_type.pk,
        'object_id': ui_element.pk,
        'target_field': target_field,
        'language_code': language_code,
        'fallback_audio_url': fallback_audio_url,
        'request': request,
        'LANGUAGE_CODE': settings.LANGUAGE_CODE,
        'preferred_audio_language': preferred_audio,
    }
