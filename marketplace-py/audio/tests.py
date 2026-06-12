from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from audio.models import AudioSnippet, AudioRequest, AudioContribution, StaticUIElement
from users.models import User
from jobs.models import Job
from decimal import Decimal


class AudioSnippetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.job = Job.objects.create(
            title="Test Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.user,
        )
        self.ct = ContentType.objects.get_for_model(Job)

    def test_create_snippet(self):
        snippet = AudioSnippet.objects.create(
            content_type=self.ct,
            object_id=self.job.pk,
            target_field="title",
            language_code="nah",
            status="ready",
        )
        self.assertEqual(snippet.target_field, "title")
        self.assertEqual(snippet.language_code, "nah")

    def test_get_audio_url_no_file(self):
        snippet = AudioSnippet.objects.create(
            content_type=self.ct,
            object_id=self.job.pk,
            target_field="title",
            language_code="nah",
        )
        self.assertIsNone(snippet.get_audio_url())

    def test_unique_together(self):
        AudioSnippet.objects.create(
            content_type=self.ct,
            object_id=self.job.pk,
            target_field="title",
            language_code="nah",
        )
        with self.assertRaises(Exception):
            AudioSnippet.objects.create(
                content_type=self.ct,
                object_id=self.job.pk,
                target_field="title",
                language_code="nah",
            )


class AudioRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.job = Job.objects.create(
            title="Test Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.user,
        )
        self.ct = ContentType.objects.get_for_model(Job)

    def test_create_request(self):
        req = AudioRequest.objects.create(
            content_type=self.ct,
            object_id=self.job.pk,
            target_field="description",
            language_code="oto",
            requested_by=self.user,
        )
        self.assertEqual(req.status, "open")

    def test_mark_fulfilled(self):
        req = AudioRequest.objects.create(
            content_type=self.ct,
            object_id=self.job.pk,
            target_field="description",
            language_code="oto",
        )
        req.mark_fulfilled()
        self.assertEqual(req.status, "fulfilled")
        self.assertIsNotNone(req.fulfilled_at)


class AudioContributionModelTest(TestCase):
    def test_create_contribution(self):
        user = User.objects.create_user(username="u", password="p")
        contrib = AudioContribution.objects.create(
            target_slug="dashboard_my_money",
            target_label="Mi dinero",
            language_code="oto",
            contributed_by=user,
        )
        self.assertEqual(contrib.status, "pending")
        self.assertEqual(contrib.target_slug, "dashboard_my_money")


class StaticUIElementModelTest(TestCase):
    def test_create_element(self):
        elem = StaticUIElement.objects.create(
            slug="dashboard_title",
            label_es="Tablero",
            label_en="Dashboard",
            category="dashboard",
        )
        self.assertEqual(str(elem.slug), "dashboard_title")

    def test_slug_unique(self):
        StaticUIElement.objects.create(slug="unique_slug", label_es="Test")
        with self.assertRaises(Exception):
            StaticUIElement.objects.create(slug="unique_slug", label_es="Test2")
