from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings

from audio.forms import AudioContributionForm
from audio.mixins import get_audio_for_static_ui, get_fallback_audio_url
from audio.templatetags.audio_tags import audio_player_static_ui
from audio.models import AudioSnippet, StaticUIElement
from jobs.models import Job
from users.models import User


class AudioContributionFormTest(TestCase):
    def test_language_field_is_present_by_default(self):
        form = AudioContributionForm()

        self.assertIn("language_code", form.fields)

    def test_hide_language_removes_language_field(self):
        form = AudioContributionForm(hide_language=True)

        self.assertNotIn("language_code", form.fields)


class AudioHelperTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="u", password="p")
        self.job = Job.objects.create(
            title="Audio Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget="10.00",
            funder=self.user,
        )
        self.static_element = StaticUIElement.objects.create(
            slug="dashboard_title",
            label_es="Tablero",
            label_en="Dashboard",
            category="dashboard",
        )

    @override_settings(FALLBACK_TEXT_LANGUAGE="es", LANGUAGE_CODE="en")
    def test_get_audio_for_static_ui_uses_fallback_chain(self):
        snippet = AudioSnippet.objects.create(
            content_type=ContentType.objects.get_for_model(StaticUIElement),
            object_id=self.static_element.pk,
            target_field="label",
            language_code="es",
            status="ready",
            file=SimpleUploadedFile("dashboard.mp3", b"audio", content_type="audio/mpeg"),
        )

        resolved_snippet, language_code = get_audio_for_static_ui(
            "dashboard_title",
            preferred_language_code="oto",
        )

        self.assertEqual(resolved_snippet, snippet)
        self.assertEqual(language_code, "es")

    def test_get_audio_for_static_ui_missing_slug_with_preference(self):
        result = get_audio_for_static_ui(
            "does-not-exist",
            preferred_language_code="oto",
        )

        self.assertEqual(result, (None, None))

    @override_settings(
        STATIC_URL="/static/",
        AUDIO_FALLBACK_FILE="audio/fallback.mp3",
        AUDIO_FALLBACK_BY_LANGUAGE={"oto": "audio/fallback-oto.mp3"},
    )
    def test_get_fallback_audio_url_prefers_language_specific_file(self):
        self.assertEqual(
            get_fallback_audio_url("oto"),
            "/static/audio/fallback-oto.mp3",
        )

    @override_settings(
        STATIC_URL="/static/",
        AUDIO_FALLBACK_FILE="audio/fallback.mp3",
        AUDIO_FALLBACK_BY_LANGUAGE={"oto": "audio/fallback-oto.mp3"},
        LANGUAGE_CODE="en",
    )
    def test_audio_player_static_ui_returns_empty_context_for_missing_slug(self):
        request = RequestFactory().get("/")

        context = audio_player_static_ui(
            {"request": request, "preferred_audio_language": "oto"},
            "missing-slug",
        )

        self.assertIsNone(context["audio_snippet"])
        self.assertEqual(context["language_code"], "oto")
        self.assertIsNone(context["content_object"])
