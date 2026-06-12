from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings

from audio.models import AudioRequest, AudioSnippet
from audio.serializers import (
    AudioRequestSerializer,
    AudioSnippetCreateSerializer,
    AudioSnippetSerializer,
)
from jobs.models import Job
from users.models import User


@override_settings(STATIC_URL="/static/", AUDIO_FALLBACK_FILE="audio/fallback.mp3")
class AudioSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.job = Job.objects.create(
            title="Serializer Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget="10.00",
            funder=self.user,
        )
        self.content_type = ContentType.objects.get_for_model(Job)

    def test_audio_snippet_serializer_builds_absolute_urls(self):
        snippet = AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
            created_by=self.user,
        )
        request = RequestFactory().get("/")

        data = AudioSnippetSerializer(snippet, context={"request": request}).data

        self.assertEqual(
            data["audio_url"],
            f"http://testserver{snippet.file.url}",
        )
        self.assertEqual(
            data["fallback_audio_url"],
            "http://testserver/static/audio/fallback.mp3",
        )
        self.assertEqual(data["content_type_name"], "job")

    def test_audio_request_serializer_reports_existing_audio(self):
        request_obj = AudioRequest.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            requested_by=self.user,
        )
        AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        data = AudioRequestSerializer(request_obj).data

        self.assertTrue(data["has_audio"])
        self.assertEqual(data["content_type_name"], "job")

    def test_audio_snippet_create_serializer_rejects_missing_object(self):
        serializer = AudioSnippetCreateSerializer(
            data={
                "content_type": self.content_type.pk,
                "object_id": 999999,
                "target_field": "title",
                "language_code": "oto",
                "status": "ready",
                "file": SimpleUploadedFile(
                    "title.mp3",
                    b"audio",
                    content_type="audio/mpeg",
                ),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("does not exist", str(serializer.errors))
