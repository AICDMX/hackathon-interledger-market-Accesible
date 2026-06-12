from django.test import SimpleTestCase

from jobs.audio_support import (
    AUDIO_SUPPORT_OPPORTUNITIES,
    AudioSupportOpportunity,
    get_audio_support_opportunity,
)


class AudioSupportOpportunityTest(SimpleTestCase):
    def test_lookup_returns_expected_opportunity(self):
        opportunity = get_audio_support_opportunity("my_products")

        self.assertEqual(
            opportunity,
            AudioSupportOpportunity(
                slug="my_products",
                title='Audio para "Mis productos"',
                description_es=(
                    'Ayúdanos a describir la sección "Mis productos" para quienes prefieren audio.'
                ),
                target_field="My Products",
                language_code="es",
                needs_funding=False,
            ),
        )

    def test_lookup_returns_none_for_unknown_slug(self):
        self.assertIsNone(get_audio_support_opportunity("missing"))

    def test_registry_contains_expected_public_slugs(self):
        self.assertEqual(
            sorted(AUDIO_SUPPORT_OPPORTUNITIES.keys()),
            ["job_post", "my_money", "my_products", "page_1", "page_2", "pending_jobs"],
        )
