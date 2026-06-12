from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from audio.mixins import (
    get_audio_for_content,
    get_audio_with_fallback,
)
from audio.models import AudioRequest, AudioSnippet
from jobs.models import Job
from users.models import User


@override_settings(AUDIO_CACHE_TIMEOUT=300, FALLBACK_TEXT_LANGUAGE="es", LANGUAGE_CODE="en")
class AudioMixinsAndSignalsTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="user", password="pass")
        self.job = Job.objects.create(
            title="Mixin Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget="10.00",
            funder=self.user,
        )
        self.content_type = ContentType.objects.get_for_model(Job)

    def test_get_audio_for_content_reads_existing_snippet(self):
        snippet = AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        result = get_audio_for_content(self.job, "title", "oto")

        self.assertEqual(result, snippet)

    def test_get_audio_with_fallback_returns_requested_fallback_language(self):
        snippet = AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="es",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        result, actual_language = get_audio_with_fallback(
            self.job,
            "title",
            preferred_language_code="oto",
        )

        self.assertEqual(result, snippet)
        self.assertEqual(actual_language, "es")

    def test_get_audio_for_content_uses_cache_for_misses(self):
        self.assertIsNone(get_audio_for_content(self.job, "title", "oto"))

        snippet = AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        self.assertIsNone(get_audio_for_content(self.job, "title", "oto"))

        cache.clear()

        self.assertEqual(get_audio_for_content(self.job, "title", "oto"), snippet)

    def test_get_audio_with_fallback_returns_requested_language_when_missing(self):
        result, actual_language = get_audio_with_fallback(
            self.job,
            "title",
            preferred_language_code="oto",
        )

        self.assertIsNone(result)
        self.assertEqual(actual_language, "oto")

    def test_ready_snippet_fulfills_matching_requests_via_signal(self):
        request = AudioRequest.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="open",
        )

        AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="ready",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        request.refresh_from_db()
        self.assertEqual(request.status, "fulfilled")

    def test_non_ready_snippet_does_not_fulfill_requests(self):
        request = AudioRequest.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="open",
        )

        AudioSnippet.objects.create(
            content_type=self.content_type,
            object_id=self.job.pk,
            target_field="title",
            language_code="oto",
            status="draft",
            file=SimpleUploadedFile("title.mp3", b"audio", content_type="audio/mpeg"),
        )

        request.refresh_from_db()
        self.assertEqual(request.status, "open")
