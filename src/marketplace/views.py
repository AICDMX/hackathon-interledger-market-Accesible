"""
Custom views for marketplace
"""
from django.shortcuts import redirect
from django.utils import translation
from django.utils.translation import get_language
from django.conf import settings
from urllib.parse import urlparse, urlunparse


def set_language_custom(request):
    """
    Custom language switching view that properly handles URL translation
    when prefix_default_language=False
    """
    if request.method == 'POST':
        language = request.POST.get('language')
        next_url = request.POST.get('next', '/')
        
        # Validate language
        if language and language in dict(settings.LANGUAGES):
            # Activate the new language
            translation.activate(language)
            request.session[translation.LANGUAGE_SESSION_KEY] = language
            
            # Parse the URL to separate path and query string
            parsed = urlparse(next_url)
            path = parsed.path
            query = parsed.query
            fragment = parsed.fragment
            
            # Remove language prefix from path if it exists
            path_without_lang = path
            for lang_code, _ in settings.LANGUAGES:
                prefix = f'/{lang_code}/'
                if path.startswith(prefix):
                    remaining = path[len(prefix):]
                    path_without_lang = '/' + remaining if remaining else '/'
                    break
                elif path == f'/{lang_code}':
                    path_without_lang = '/'
                    break
            
            # Ensure path starts with /
            if not path_without_lang.startswith('/'):
                path_without_lang = '/' + path_without_lang
            
            # If switching to default language, use path without prefix
            if language == settings.LANGUAGE_CODE:
                final_path = path_without_lang
            else:
                # If switching to non-default language, add language prefix
                final_path = f'/{language}{path_without_lang}'
            
            # Reconstruct URL with query string and fragment if present
            final_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                final_path,
                parsed.params,
                query,
                fragment
            ))
            
            return redirect(final_url)
    
    # Fallback to home
    return redirect('/')
