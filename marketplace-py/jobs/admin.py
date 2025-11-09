from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Job, JobSubmission, JobApplication


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'funder', 'target_language', 'status', 'budget', 'created_at']
    list_filter = ['status', 'target_language', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JobSubmission)
class JobSubmissionAdmin(admin.ModelAdmin):
    list_display = ['job', 'creator', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'applicant__username', 'profile_note']
    readonly_fields = ['created_at', 'updated_at']
