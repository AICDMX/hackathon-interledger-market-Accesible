from django.apps import AppConfig
from django.db.models.signals import post_migrate


def load_default_jobs_handler(sender, **kwargs):
    """Load default jobs after migrations."""
    from django.core.management import call_command
    try:
        call_command('load_default_jobs', verbosity=0)
    except Exception:
        # Silently fail if there's an issue
        pass


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        # Connect signal to load default jobs after migrations
        post_migrate.connect(load_default_jobs_handler, sender=self)


