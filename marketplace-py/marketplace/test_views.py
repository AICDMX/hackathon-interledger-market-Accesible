from django.test import SimpleTestCase, override_settings


class SetLanguageCustomViewTest(SimpleTestCase):
    @override_settings(
        ROOT_URLCONF="marketplace.urls",
        LANGUAGES=(("en", "English"), ("es", "Spanish"), ("oto", "Otomi")),
        LANGUAGE_CODE="en",
        LANGUAGE_COOKIE_NAME="django_language",
        PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME="preferred_audio_language",
        SUPPORTED_UI_LANGUAGES=("en", "es"),
        FALLBACK_TEXT_LANGUAGE="es",
    )
    def test_default_language_redirect_strips_prefix(self):
        response = self.client.post(
            "/i18n/setlang/",
            {"language": "en", "next": "/es/browse/?page=2"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/browse/?page=2")
        self.assertEqual(response.cookies["django_language"].value, "en")
        self.assertEqual(response.cookies["preferred_audio_language"].value, "en")

    @override_settings(
        ROOT_URLCONF="marketplace.urls",
        LANGUAGES=(("en", "English"), ("es", "Spanish"), ("oto", "Otomi")),
        LANGUAGE_CODE="en",
        LANGUAGE_COOKIE_NAME="django_language",
        PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME="preferred_audio_language",
        SUPPORTED_UI_LANGUAGES=("en", "es"),
        FALLBACK_TEXT_LANGUAGE="es",
    )
    def test_non_ui_language_redirects_to_fallback_text_prefix(self):
        response = self.client.post(
            "/i18n/setlang/",
            {"language": "oto", "next": "/browse/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/es/browse/")
        self.assertEqual(response.cookies["django_language"].value, "es")
        self.assertEqual(response.cookies["preferred_audio_language"].value, "oto")

    @override_settings(
        ROOT_URLCONF="marketplace.urls",
        LANGUAGES=(("en", "English"), ("es", "Spanish"), ("oto", "Otomi")),
        LANGUAGE_CODE="en",
        LANGUAGE_COOKIE_NAME="django_language",
        PREFERRED_AUDIO_LANGUAGE_COOKIE_NAME="preferred_audio_language",
        SUPPORTED_UI_LANGUAGES=("en", "es"),
        FALLBACK_TEXT_LANGUAGE="es",
    )
    def test_invalid_language_redirects_home_without_setting_cookies(self):
        response = self.client.post(
            "/i18n/setlang/",
            {"language": "invalid", "next": "/browse/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertNotIn("django_language", response.cookies)
        self.assertNotIn("preferred_audio_language", response.cookies)
