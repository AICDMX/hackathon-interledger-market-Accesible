"""
URL configuration for marketplace project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Ensure our custom language switcher overrides Django's default set_language view
    path('i18n/setlang/', views.set_language_custom, name='set_language_custom'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('rosetta/', include('rosetta.urls')),
]

# Add language prefix to URLs
urlpatterns += i18n_patterns(
    path('', include('jobs.urls')),
    path('users/', include('users.urls')),
    prefix_default_language=False,
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
