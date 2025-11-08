from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Job, JobSubmission


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'funder', 'target_language', 'status', 'budget', 'created_at']
    list_filter = ['status', 'target_language', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    # Note: Audio snippets and requests use GenericForeignKey, so they can't be used as standard inlines
    # Use the audio admin directly or create custom admin views if needed


@admin.register(JobSubmission)
class JobSubmissionAdmin(admin.ModelAdmin):
    list_display = ['job', 'creator', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
