"""
Custom context processors for marketplace project.
"""
import json
from django.conf import settings


def language_preferences(request):
    """
    Provide audio language preference information to all templates.
    """
    available_language_codes = {code for code, _ in settings.LANGUAGES}
    preferred_audio = request.COOKIES.get(settings.PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME)

    if preferred_audio not in available_language_codes:
        preferred_audio = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    request_language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    if preferred_audio not in available_language_codes:
        preferred_audio = request_language if request_language in available_language_codes else settings.LANGUAGE_CODE

    supported_ui = set(getattr(settings, 'SUPPORTED_UI_LANGUAGES', (settings.LANGUAGE_CODE,)))
    fallback_language = getattr(settings, 'FALLBACK_TEXT_LANGUAGE', settings.LANGUAGE_CODE)
    audio_text_fallback_active = preferred_audio not in supported_ui and request_language == fallback_language

    return {
        'preferred_audio_language': preferred_audio,
        'audio_text_fallback_active': audio_text_fallback_active,
        'fallback_text_language': fallback_language,
        'audio_config': {
            'icon_inactive': (settings.MEDIA_URL.rstrip('/') + '/' + getattr(settings, 'AUDIO_ICON_INACTIVE', 'listen-inactive.png')).replace('//', '/'),
            'icon_active': (settings.MEDIA_URL.rstrip('/') + '/' + getattr(settings, 'AUDIO_ICON_ACTIVE', 'listen-active.png')).replace('//', '/'),
            'fallback_audio': json.dumps(getattr(settings, 'AUDIO_FALLBACK_BY_LANGUAGE', {})),
            'fallback_file': getattr(settings, 'AUDIO_FALLBACK_FILE', 'audio/fallback.mp3'),
            'media_url': settings.MEDIA_URL,
            'static_url': settings.STATIC_URL,
        },
    }
