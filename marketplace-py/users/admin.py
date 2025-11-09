from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'preferred_language', 'created_at', 'has_seller_credentials']
    list_filter = ['role', 'preferred_language', 'created_at']
    search_fields = ['username', 'email']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'pretty_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Role & Language'), {'fields': ('role', 'preferred_language', 'native_languages')}),
        (_('Wallet'), {'fields': ('wallet_address',)}),
        (_('Seller Credentials (Marketplace Account)'), {
            'fields': ('seller_wallet_address', 'seller_key_id', 'seller_private_key'),
            'description': 'Configure seller credentials for Open Payments. Only one user should have these configured (the marketplace account).'
        }),
        (_('Profile'), {'fields': ('profile_note', 'profile_audio', 'profile_video', 'profile_image')}),
        (_('Job Defaults'), {'fields': (
            'default_target_language', 'default_target_dialect', 'default_deliverable_types',
            'default_recruit_limit', 'default_submit_limit',
            'default_recruit_deadline_days', 'default_submit_deadline_days', 'default_expired_date_days'
        )}),
    )
    
    def has_seller_credentials(self, obj):
        """Check if user has seller credentials configured."""
        return bool(obj.seller_wallet_address and obj.seller_key_id and obj.seller_private_key)
    has_seller_credentials.boolean = True
    has_seller_credentials.short_description = _('Has Seller Credentials')
