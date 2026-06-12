from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from audio.models import AudioRequest, AudioSnippet, StaticUIElement
from jobs.models import Job
from users.models import User


@override_settings(
    ROOT_URLCONF="marketplace.urls",
    STATIC_URL="/static/",
    LANGUAGE_CODE="en",
    FALLBACK_TEXT_LANGUAGE="es",
    AUDIO_FALLBACK_FILE="audio/fallback.mp3",
    AUDIO_FALLBACK_BY_LANGUAGE={"oto": "audio/fallback-oto.mp3"},
)
class AudioApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="user", password="pass")
        self.client.force_authenticate(user=self.user)
        self.job = Job.objects.create(
            title="API Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget="10.00",
            funder=self.user,
        )
        self.static_element = StaticUIElement.objects.create(
            slug="dashboard_my_money",
            label_es="Mi dinero",
            label_en="My Money",
            category="dashboard",
        )

    def test_by_content_requires_ids(self):
        response = self.client.get("/api/audio/snippets/by_content/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "content_type_id and object_id are required",
        )

    def test_by_content_rejects_invalid_content_type_id(self):
        response = self.client.get(
            "/api/audio/snippets/by_content/",
            {"content_type_id": 999999, "object_id": self.job.pk},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid content_type_id")

    def test_get_audio_rejects_invalid_content_type_id(self):
        response = self.client.get(
            f"/api/audio/snippets/get/999999/{self.job.pk}/title/oto/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Invalid content_type_id: 999999",
        )

    def test_get_audio_rejects_invalid_object_id(self):
        content_type = ContentType.objects.get_for_model(Job)

        response = self.client.get(
            f"/api/audio/snippets/get/{content_type.pk}/not-an-int/title/oto/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Invalid object_id: not-an-int",
        )

    def test_get_audio_returns_404_for_missing_object(self):
        content_type = ContentType.objects.get_for_model(Job)

        response = self.client.get(
            f"/api/audio/snippets/get/{content_type.pk}/999999/title/oto/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("Content object not found", response.json()["error"])

    def test_get_audio_for_missing_static_ui_returns_fallback(self):
        response = self.client.get(
            "/api/audio/snippets/get/static_ui/missing/label/oto/"
        )

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertFalse(payload["available"])
        self.assertEqual(
            payload["fallback_audio_url"],
            "http://testserver/static/audio/fallback-oto.mp3",
        )

    def test_get_audio_for_existing_static_ui_without_snippet_returns_200_fallback(self):
        response = self.client.get(
            f"/api/audio/snippets/get/static_ui/{self.static_element.slug}/label/oto/"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["available"])
        self.assertEqual(
            payload["fallback_audio_url"],
            "http://testserver/static/audio/fallback-oto.mp3",
        )
        self.assertEqual(payload["tried_languages"], ["oto", "es", "en"])

    def test_request_audio_returns_existing_open_request(self):
        content_type = ContentType.objects.get_for_model(Job)
        existing = AudioRequest.objects.create(
            content_type=content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="open",
            requested_by=self.user,
        )

        response = self.client.post(
            "/api/audio/requests/request_audio/",
            {
                "content_type_id": content_type.pk,
                "object_id": self.job.pk,
                "target_field": "title",
                "language_code": "oto",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], existing.pk)
        self.assertEqual(AudioRequest.objects.count(), 1)

    def test_request_audio_rejects_when_ready_audio_exists(self):
        content_type = ContentType.objects.get_for_model(Job)
        AudioSnippet.objects.create(
            content_type=content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        response = self.client.post(
            "/api/audio/requests/request_audio/",
            {
                "content_type_id": content_type.pk,
                "object_id": self.job.pk,
                "target_field": "title",
                "language_code": "oto",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Audio already exists for this content",
        )

    def test_upload_audio_contribution_rejects_invalid_extension(self):
        response = self.client.post(
            "/api/audio/contributions/upload/",
            {
                "file": SimpleUploadedFile(
                    "bad.txt",
                    b"not-audio",
                    content_type="text/plain",
                ),
                "language_code": "oto",
                "target_slug": "dashboard_my_money",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file type", response.json()["error"])

    def test_upload_audio_contribution_requires_file(self):
        response = self.client.post(
            "/api/audio/contributions/upload/",
            {
                "language_code": "oto",
                "target_slug": "dashboard_my_money",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "No audio file provided")

    def test_upload_audio_contribution_requires_language_code(self):
        response = self.client.post(
            "/api/audio/contributions/upload/",
            {
                "file": SimpleUploadedFile(
                    "clip.mp3",
                    b"audio-bytes",
                    content_type="audio/mpeg",
                ),
                "target_slug": "dashboard_my_money",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Language code is required")

    def test_upload_audio_contribution_rejects_oversized_file(self):
        oversized = SimpleUploadedFile(
            "clip.mp3",
            b"a" * (10 * 1024 * 1024 + 1),
            content_type="audio/mpeg",
        )

        response = self.client.post(
            "/api/audio/contributions/upload/",
            {
                "file": oversized,
                "language_code": "oto",
                "target_slug": "dashboard_my_money",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("File too large", response.json()["error"])

    def test_upload_audio_contribution_accepts_extension_fallback(self):
        response = self.client.post(
            "/api/audio/contributions/upload/",
            {
                "file": SimpleUploadedFile(
                    "clip.mp3",
                    b"audio-bytes",
                    content_type="application/octet-stream",
                ),
                "language_code": "oto",
                "target_slug": "dashboard_my_money",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["success"])

    @patch("audio.views.AudioContribution.objects.create", side_effect=RuntimeError("boom"))
    def test_upload_audio_contribution_returns_500_on_storage_error(self, _mock_create):
        response = self.client.post(
            "/api/audio/contributions/upload/",
            {
                "file": SimpleUploadedFile(
                    "clip.mp3",
                    b"audio-bytes",
                    content_type="audio/mpeg",
                ),
                "language_code": "oto",
                "target_slug": "dashboard_my_money",
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"], "Error uploading audio: boom")
