from django.test import RequestFactory, SimpleTestCase, override_settings

from marketplace.context_processors import language_preferences


class LanguagePreferencesContextProcessorTest(SimpleTestCase):
    @override_settings(
        LANGUAGES=(("en", "English"), ("es", "Spanish"), ("oto", "Otomi")),
        LANGUAGE_CODE="en",
        LANGUAGE_COOKIE_NAME="django_language",
        PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME="preferred_audio_language",
        SUPPORTED_UI_LANGUAGES=("en", "es"),
        FALLBACK_TEXT_LANGUAGE="es",
        MEDIA_URL="/media/",
        STATIC_URL="/static/",
        AUDIO_FALLBACK_FILE="audio/fallback.mp3",
        AUDIO_FALLBACK_BY_LANGUAGE={"oto": "audio/fallback-oto.mp3"},
    )
    def test_prefers_explicit_audio_cookie_when_valid(self):
        request = RequestFactory().get("/")
        request.COOKIES["preferred_audio_language"] = "oto"
        request.COOKIES["django_language"] = "es"
        request.LANGUAGE_CODE = "en"

        context = language_preferences(request)

        self.assertEqual(context["preferred_audio_language"], "oto")
        self.assertFalse(context["audio_text_fallback_active"])
        self.assertEqual(
            context["audio_config"]["fallback_audio"],
            '{"oto": "audio/fallback-oto.mp3"}',
        )

    @override_settings(
        LANGUAGES=(("en", "English"), ("es", "Spanish"), ("oto", "Otomi")),
        LANGUAGE_CODE="en",
        LANGUAGE_COOKIE_NAME="django_language",
        PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME="preferred_audio_language",
        SUPPORTED_UI_LANGUAGES=("en", "es"),
        FALLBACK_TEXT_LANGUAGE="es",
        MEDIA_URL="/media/",
        STATIC_URL="/static/",
    )
    def test_falls_back_to_request_language_and_marks_text_fallback(self):
        request = RequestFactory().get("/")
        request.COOKIES["preferred_audio_language"] = "oto"
        request.COOKIES["django_language"] = "es"
        request.LANGUAGE_CODE = "es"

        context = language_preferences(request)

        self.assertEqual(context["preferred_audio_language"], "oto")
        self.assertTrue(context["audio_text_fallback_active"])
