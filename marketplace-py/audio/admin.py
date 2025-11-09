from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings
from .models import AudioSnippet, AudioRequest, AudioContribution, StaticUIElement


class AudioSnippetInline(admin.TabularInline):
    """Inline for managing audio snippets on related models."""
    model = AudioSnippet
    extra = 0
    fields = ('target_field', 'language_code', 'file', 'status', 'transcript')
    readonly_fields = ('created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('created_at',)
        return self.readonly_fields


@admin.register(AudioSnippet)
class AudioSnippetAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'target_field', 'language_code', 'status', 'audio_preview', 'created_at', 'created_by']
    list_filter = ['status', 'language_code', 'target_field', 'created_at']
    search_fields = ['transcript', 'target_field', 'language_code']
    readonly_fields = ['created_at', 'updated_at', 'audio_preview']
    fieldsets = (
        (_('Content'), {
            'fields': ('content_type', 'object_id', 'target_field')
        }),
        (_('Audio'), {
            'fields': ('language_code', 'file', 'audio_preview', 'transcript', 'status')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('content_type', 'created_by')
    
    def audio_preview(self, obj):
        """Display audio player preview in admin."""
        if obj.file:
            return format_html(
                '<audio controls style="width: 100%; max-width: 400px;">'
                '<source src="{}" type="audio/mpeg">'
                '<source src="{}" type="audio/ogg">'
                'Your browser does not support the audio element.'
                '</audio>',
                obj.file.url,
                obj.file.url
            )
        return format_html('<em>{}</em>', _('No audio file uploaded'))
    audio_preview.short_description = _('Audio Preview')
    
    def save_model(self, request, obj, form, change):
        """Set created_by if not set."""
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AudioRequest)
class AudioRequestAdmin(admin.ModelAdmin):
    list_display = ['content_object', 'target_field', 'language_code', 'status', 'requested_by', 'created_at', 'has_audio']
    list_filter = ['status', 'language_code', 'target_field', 'created_at']
    search_fields = ['notes', 'target_field', 'language_code']
    readonly_fields = ['created_at', 'updated_at', 'fulfilled_at', 'has_audio']
    fieldsets = (
        (_('Content'), {
            'fields': ('content_type', 'object_id', 'target_field')
        }),
        (_('Request'), {
            'fields': ('language_code', 'status', 'notes', 'requested_by')
        }),
        (_('Status'), {
            'fields': ('has_audio', 'created_at', 'updated_at', 'fulfilled_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('content_type', 'requested_by')
    
    def has_audio(self, obj):
        """Check if audio snippet exists for this request."""
        if obj.pk:
            content_type = obj.content_type
            snippet = AudioSnippet.objects.filter(
                content_type=content_type,
                object_id=obj.object_id,
                target_field=obj.target_field,
                language_code=obj.language_code,
                status='ready'
            ).exists()
            if snippet:
                return format_html('<span style="color: green;">? {}</span>', _('Audio available'))
        return format_html('<span style="color: red;">? {}</span>', _('No audio'))
    has_audio.short_description = _('Audio Status')
    
    actions = ['mark_as_fulfilled', 'create_audio_snippet']
    
    def mark_as_fulfilled(self, request, queryset):
        """Mark selected requests as fulfilled."""
        count = 0
        for audio_request in queryset.filter(status__in=['open', 'in_progress']):
            audio_request.mark_fulfilled()
            count += 1
        self.message_user(request, f'{count} audio request(s) marked as fulfilled.')
    mark_as_fulfilled.short_description = _('Mark selected requests as fulfilled')
    
    def create_audio_snippet(self, request, queryset):
        """Create draft audio snippets for selected requests."""
        count = 0
        for audio_request in queryset.filter(status__in=['open', 'in_progress']):
            # Check if snippet already exists
            content_type = audio_request.content_type
            snippet_exists = AudioSnippet.objects.filter(
                content_type=content_type,
                object_id=audio_request.object_id,
                target_field=audio_request.target_field,
                language_code=audio_request.language_code
            ).exists()
            
            if not snippet_exists:
                AudioSnippet.objects.create(
                    content_type=content_type,
                    object_id=audio_request.object_id,
                    target_field=audio_request.target_field,
                    language_code=audio_request.language_code,
                    status='draft',
                    created_by=request.user
                )
                count += 1
        self.message_user(request, f'{count} draft audio snippet(s) created.')
    create_audio_snippet.short_description = _('Create draft audio snippets for selected requests')
    
    def save_model(self, request, obj, form, change):
        """Set requested_by if not set."""
        if not change:  # Creating new object
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AudioContribution)
class AudioContributionAdmin(admin.ModelAdmin):
    list_display = ['target_label', 'language_code', 'status', 'contributed_by', 'created_at']
    list_filter = ['status', 'language_code', 'created_at']
    search_fields = ['target_slug', 'target_label', 'language_code', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Meta'), {
            'fields': ('target_slug', 'target_label', 'language_code', 'notes')
        }),
        (_('Archivo'), {
            'fields': ('file', 'status')
        }),
        (_('Relaciones'), {
            'fields': ('contributed_by', 'audio_request', 'content_type', 'object_id')
        }),
        (_('Seguimiento'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    raw_id_fields = ['contributed_by', 'audio_request']


@admin.register(StaticUIElement)
class StaticUIElementAdmin(admin.ModelAdmin):
    list_display = ['slug', 'label_es', 'label_en', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['slug', 'label_es', 'label_en', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Identification'), {
            'fields': ('slug', 'category')
        }),
        (_('Labels'), {
            'fields': ('label_es', 'label_en', 'description')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('audiosnippet_set')
