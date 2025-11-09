"""
REST API serializers for audio app.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.templatetags.static import static
from .models import AudioSnippet, AudioRequest


class AudioSnippetSerializer(serializers.ModelSerializer):
    """Serializer for AudioSnippet model."""
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    audio_url = serializers.SerializerMethodField()
    fallback_audio_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioSnippet
        fields = [
            'id', 'content_type', 'object_id', 'content_type_name',
            'target_field', 'language_code', 'transcript', 'status',
            'audio_url', 'fallback_audio_url', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_audio_url(self, obj):
        """Return the audio file URL."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_fallback_audio_url(self, obj):
        """Return the fallback audio URL."""
        fallback_path = getattr(settings, 'AUDIO_FALLBACK_FILE', 'audio/fallback.mp3')
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(static(fallback_path))
        return static(fallback_path)


class AudioRequestSerializer(serializers.ModelSerializer):
    """Serializer for AudioRequest model."""
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    has_audio = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioRequest
        fields = [
            'id', 'content_type', 'object_id', 'content_type_name',
            'target_field', 'language_code', 'status', 'notes',
            'requested_by', 'has_audio', 'created_at', 'updated_at', 'fulfilled_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'fulfilled_at', 'requested_by']
    
    def get_has_audio(self, obj):
        """Check if audio snippet exists for this request."""
        if obj.pk:
            return AudioSnippet.objects.filter(
                content_type=obj.content_type,
                object_id=obj.object_id,
                target_field=obj.target_field,
                language_code=obj.language_code,
                status='ready'
            ).exists()
        return False


class AudioSnippetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AudioSnippet."""
    
    class Meta:
        model = AudioSnippet
        fields = [
            'content_type', 'object_id', 'target_field',
            'language_code', 'file', 'transcript', 'status'
        ]
    
    def validate(self, data):
        """Validate that content object exists."""
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        
        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                if model_class:
                    obj = model_class.objects.get(pk=object_id)
                    data['content_object'] = obj
            except model_class.DoesNotExist:
                raise serializers.ValidationError(
                    f"Object with id {object_id} does not exist for {content_type.model}"
                )
        return data
