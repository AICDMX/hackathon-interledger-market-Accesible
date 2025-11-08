"""
Custom views for marketplace.
"""
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.shortcuts import redirect
from django.utils import translation


def set_language_custom(request):
    """
    Switch site language while respecting prefix_default_language=False.
    """
    if request.method == 'POST':
        language = request.POST.get('language')
        next_url = request.POST.get('next', '/')

        if language and language in dict(settings.LANGUAGES):
            # Parse next_url into components
            parsed = urlparse(next_url)
            path = parsed.path or '/'

            # Strip any language prefix from the current path
            path_without_lang = path
            for lang_code, _ in settings.LANGUAGES:
                prefix = f'/{lang_code}/'
                if path.startswith(prefix):
                    remaining = path[len(prefix):]
                    path_without_lang = '/' + remaining if remaining else '/'
                    break
                if path == f'/{lang_code}':
                    path_without_lang = '/'
                    break

            if not path_without_lang.startswith('/'):
                path_without_lang = '/' + path_without_lang

            # Default language shouldn't keep a prefix
            if language == settings.LANGUAGE_CODE:
                final_path = path_without_lang
            else:
                final_path = f'/{language}{path_without_lang}'

            final_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                final_path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            ))

            translation.activate(language)
            response = redirect(final_url or '/')
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language,
                max_age=settings.LANGUAGE_COOKIE_AGE,
                path=settings.LANGUAGE_COOKIE_PATH,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                secure=settings.LANGUAGE_COOKIE_SECURE,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
            )
            return response

    return redirect('/')
