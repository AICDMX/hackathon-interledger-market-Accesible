from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'preferred_language', 'created_at']
    list_filter = ['role', 'preferred_language', 'created_at']
    search_fields = ['username', 'email']
