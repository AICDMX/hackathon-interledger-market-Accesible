"""
REST API views for audio app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings
from .models import AudioSnippet, AudioRequest
from .serializers import AudioSnippetSerializer, AudioRequestSerializer, AudioSnippetCreateSerializer
from .mixins import get_audio_for_content


class AudioSnippetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AudioSnippet.
    Provides endpoints to get, create, update, and delete audio snippets.
    """
    queryset = AudioSnippet.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AudioSnippetCreateSerializer
        return AudioSnippetSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context for building absolute URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set created_by when creating."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_content(self, request):
        """
        Get audio snippets for a specific content object.
        Query params: content_type_id, object_id, language_code (optional), status (optional)
        """
        content_type_id = request.query_params.get('content_type_id')
        object_id = request.query_params.get('object_id')
        language_code = request.query_params.get('language_code')
        status_filter = request.query_params.get('status', 'ready')
        
        if not content_type_id or not object_id:
            return Response(
                {'error': 'content_type_id and object_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content_type = ContentType.objects.get(pk=content_type_id)
        except ContentType.DoesNotExist:
            return Response(
                {'error': 'Invalid content_type_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = AudioSnippet.objects.filter(
            content_type=content_type,
            object_id=object_id,
            status=status_filter
        )
        
        if language_code:
            queryset = queryset.filter(language_code=language_code)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='get/(?P<content_type_id>[^/.]+)/(?P<object_id>[^/.]+)/(?P<target_field>[^/.]+)/(?P<language_code>[^/.]+)')
    def get_audio(self, request, content_type_id, object_id, target_field, language_code):
        """
        Get a specific audio snippet.
        URL: /api/audio/snippets/get/<content_type_id>/<object_id>/<target_field>/<language_code>/
        """
        try:
            content_type = ContentType.objects.get(pk=content_type_id)
        except ContentType.DoesNotExist:
            return Response(
                {'error': 'Invalid content_type_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        snippet = AudioSnippet.objects.filter(
            content_type=content_type,
            object_id=object_id,
            target_field=target_field,
            language_code=language_code,
            status='ready'
        ).first()
        
        if snippet:
            serializer = self.get_serializer(snippet)
            return Response(serializer.data)
        else:
            # Return fallback audio URL when snippet is not available
            from django.templatetags.static import static
            fallback_path = getattr(settings, 'AUDIO_FALLBACK_FILE', 'audio/fallback.mp3')
            fallback_url = self.request.build_absolute_uri(static(fallback_path))
            
            return Response(
                {
                    'available': False,
                    'message': 'Audio not available for this content',
                    'fallback_audio_url': fallback_url,
                    'content_type_id': content_type_id,
                    'object_id': object_id,
                    'target_field': target_field,
                    'language_code': language_code
                },
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """
        Stream audio file directly.
        URL: /api/audio/snippets/<id>/stream/
        """
        snippet = self.get_object()
        if not snippet.file:
            raise Http404("Audio file not found")
        
        # In production, you might want to use signed URLs or proxy through Django
        # For now, return the file directly
        return FileResponse(
            snippet.file.open('rb'),
            content_type='audio/mpeg',
            as_attachment=False
        )


class AudioRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AudioRequest.
    Provides endpoints to get, create, and manage audio requests.
    """
    queryset = AudioRequest.objects.all()
    serializer_class = AudioRequestSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """Set requested_by when creating."""
        serializer.save(requested_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def request_audio(self, request):
        """
        Create an audio request for a content object.
        Body: content_type_id, object_id, target_field, language_code, notes (optional)
        """
        content_type_id = request.data.get('content_type_id')
        object_id = request.data.get('object_id')
        target_field = request.data.get('target_field')
        language_code = request.data.get('language_code')
        notes = request.data.get('notes', '')
        
        if not all([content_type_id, object_id, target_field, language_code]):
            return Response(
                {'error': 'content_type_id, object_id, target_field, and language_code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content_type = ContentType.objects.get(pk=content_type_id)
        except ContentType.DoesNotExist:
            return Response(
                {'error': 'Invalid content_type_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if audio already exists
        existing_audio = AudioSnippet.objects.filter(
            content_type=content_type,
            object_id=object_id,
            target_field=target_field,
            language_code=language_code,
            status='ready'
        ).exists()
        
        if existing_audio:
            return Response(
                {'error': 'Audio already exists for this content'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if request already exists
        existing_request = AudioRequest.objects.filter(
            content_type=content_type,
            object_id=object_id,
            target_field=target_field,
            language_code=language_code,
            status__in=['open', 'in_progress']
        ).first()
        
        if existing_request:
            serializer = self.get_serializer(existing_request)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Create new request
        audio_request = AudioRequest.objects.create(
            content_type=content_type,
            object_id=object_id,
            target_field=target_field,
            language_code=language_code,
            notes=notes,
            requested_by=request.user
        )
        
        serializer = self.get_serializer(audio_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
