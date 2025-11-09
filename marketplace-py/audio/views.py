"""
REST API views for audio app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from .models import AudioSnippet, AudioRequest, AudioContribution
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


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow anonymous contributions
def upload_audio_contribution(request):
    """
    Upload audio contribution (supports both file upload and browser recording).
    Handles background uploads with keepalive support.
    Note: CSRF protection is handled by Django middleware for form submissions,
    but API calls from JavaScript may need CSRF token in headers.
    """
    if request.method != 'POST':
        return Response(
            {'error': 'Method not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # Get form data (supports both multipart/form-data and application/json)
    audio_file = request.FILES.get('file')
    language_code = request.POST.get('language_code', '') or request.data.get('language_code', '')
    notes = request.POST.get('notes', '') or request.data.get('notes', '')
    target_slug = request.POST.get('target_slug', '') or request.data.get('target_slug', '')
    
    # Validate required fields
    if not audio_file:
        return Response(
            {'error': 'No audio file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not language_code:
        return Response(
            {'error': 'Language code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file type
    allowed_types = ['audio/webm', 'audio/ogg', 'audio/mp4', 'audio/wav', 'audio/mpeg', 'audio/mp3']
    if audio_file.content_type not in allowed_types:
        # Check file extension as fallback
        file_ext = audio_file.name.split('.')[-1].lower()
        if file_ext not in ['webm', 'ogg', 'mp4', 'wav', 'mp3', 'mpeg']:
            return Response(
                {'error': f'Invalid file type. Allowed: {", ".join(allowed_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if audio_file.size > max_size:
        return Response(
            {'error': f'File too large. Maximum size: {max_size / (1024 * 1024)}MB'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Create audio contribution
        contribution = AudioContribution.objects.create(
            file=audio_file,
            language_code=language_code,
            notes=notes,
            target_slug=target_slug,
            target_label=target_slug.replace('_', ' ').title(),  # Generate label from slug
            contributed_by=request.user if request.user.is_authenticated else None,
            status='pending'
        )

        return Response(
            {
                'success': True,
                'message': 'Audio contribution uploaded successfully',
                'contribution_id': contribution.id,
                'status': contribution.status
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'error': f'Error uploading audio: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
