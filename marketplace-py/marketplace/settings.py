"""
Django settings for marketplace project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Since settings.py is in marketplace-py/marketplace/, parent.parent gives us marketplace-py/
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Read from environment in production; falls back to dev default
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# Toggle via environment variable DEBUG=True/False
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('1', 'true', 'yes')

# ALLOWED_HOSTS configuration
# In Docker, set ALLOWED_HOSTS environment variable (e.g., ALLOWED_HOSTS=* or ALLOWED_HOSTS=localhost,127.0.0.1)
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'modeltranslation',
    'rosetta',
    'rest_framework',
    
    # Local apps
    'users',
    'jobs',
    'audio',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # For multi-language support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'marketplace.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # For language switching
                'marketplace.context_processors.language_preferences',
            ],
        },
    },
]

WSGI_APPLICATION = 'marketplace.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('nah', 'Nahuatl'),
    ('oto', 'Otomi (?uhu)'),
    ('maz', 'Mazahua'),
    ('que', 'Quechua'),
]

# UI language rules
SUPPORTED_UI_LANGUAGES = ('en', 'es')
FALLBACK_TEXT_LANGUAGE = 'es'
PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME = 'preferred_audio_language'

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Model translation settings
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LANGUAGES = ('en', 'es', 'nah', 'oto', 'maz', 'que')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Site ID for django.contrib.sites
SITE_ID = 1

# Login URLs
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Accessibility: Ensure proper ARIA labels and semantic HTML
# This will be enforced in templates

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# Caching configuration (using in-memory cache for development)
# In production, use Redis: CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': 'redis://127.0.0.1:6379/1'}}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'audio-cache',
    }
}

# Audio cache timeout (in seconds)
AUDIO_CACHE_TIMEOUT = 300  # 5 minutes

# Fallback audio file path (relative to STATIC_URL)
# This file will be used when audio snippets are not available
# Format: MP3 is recommended for widest browser support
AUDIO_FALLBACK_FILE = 'audio/fallback.mp3'  # Path relative to static files

# Language-specific fallback audio files
# Maps language codes to fallback audio file paths (relative to STATIC_URL)
AUDIO_FALLBACK_BY_LANGUAGE = {
    'oto': 'audio/fallback-oto.mp3',  # Otomi-specific fallback
    # Add more language-specific fallbacks here as needed
    # 'nah': 'audio/fallback-nah.mp3',
    # 'maz': 'audio/fallback-maz.mp3',
    # 'que': 'audio/fallback-que.mp3',
}

# Audio icon paths (relative to MEDIA_URL)
AUDIO_ICON_INACTIVE = 'listen-inactive.png'
AUDIO_ICON_ACTIVE = 'listen-active.png'

# Payments service configuration
PAYMENTS_SERVICE_URL = os.environ.get('PAYMENTS_SERVICE_URL', 'http://payments:3000')
# In development, use http://localhost:4001 if running payments service locally
PAYMENTS_SELLER_ID = os.environ.get('PAYMENTS_SELLER_ID', 'seller-mvr5656')
DEFAULT_SELLER_ID = os.environ.get('DEFAULT_SELLER_ID', 'default-seller')
