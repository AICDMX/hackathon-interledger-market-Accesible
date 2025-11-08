"""
Audio app for Django marketplace.
Provides reusable audio snippet functionality for any content model.
"""
from django.apps import AppConfig


class AudioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audio'
    verbose_name = 'Audio'
    
    def ready(self):
        """Import signals when app is ready."""
        import audio.signals  # noqa
