"""
URL configuration for audio app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AudioSnippetViewSet, AudioRequestViewSet, upload_audio_contribution

router = DefaultRouter()
router.register(r'snippets', AudioSnippetViewSet, basename='audiosnippet')
router.register(r'requests', AudioRequestViewSet, basename='audiorequest')

urlpatterns = [
    path('', include(router.urls)),
    path('contributions/upload/', upload_audio_contribution, name='upload_contribution'),
]
