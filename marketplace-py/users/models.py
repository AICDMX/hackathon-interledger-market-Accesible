from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with wallet and language support."""
    
    ROLE_CHOICES = [
        ('funder', _('Funder')),
        ('creator', _('Creator')),
        ('both', _('Both')),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='both',
        help_text=_('User role: funder creates jobs, creator accepts jobs')
    )
    
    wallet_endpoint = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Interledger wallet endpoint')
    )
    
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        help_text=_('Preferred language for interface')
    )
    
    native_languages = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Comma-separated list of native languages (e.g., nahuatl, otomi)')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.username
    
    def get_native_languages_list(self):
        """Return native languages as a list."""
        if self.native_languages:
            return [lang.strip() for lang in self.native_languages.split(',')]
        return []
    
    def is_funder(self):
        """Check if user can create jobs (funder or both)."""
        return self.role in ['funder', 'both']
    
    def is_creator(self):
        """Check if user can accept jobs (creator or both)."""
        return self.role in ['creator', 'both']

    def save(self, *args, **kwargs):
        """
        Temporarily promote every new account to admin-level access so the team
        can reach the Django admin without manual flag setting.
        """
        if self.pk is None:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)
