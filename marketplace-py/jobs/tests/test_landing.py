from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from jobs.models import Job
from users.models import User


class LandingPageTest(TestCase):
    def test_anonymous_sees_landing(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Native Language")

    def test_logged_in_redirects_to_dashboard(self):
        User.objects.create_user(username="u", password="pass")
        self.client.login(username="u", password="pass")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("dashboard", response.url)

    def test_landing_shows_stats(self):
        funder = User.objects.create_user(
            username="f", password="p", role="funder"
        )
        for i in range(3):
            User.objects.create_user(
                username=f"c{i}", password="p", role="creator"
            )
        Job.objects.create(
            title="J1", description="d", target_language="nah",
            deliverable_types="text", budget=Decimal("10"),
            funder=funder, status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        Job.objects.create(
            title="J2", description="d", target_language="oto",
            deliverable_types="text", budget=Decimal("10"),
            funder=funder, status="submitting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        Job.objects.create(
            title="J3", description="d", target_language="nah",
            deliverable_types="text", budget=Decimal("10"),
            funder=funder, status="complete",
        )

        response = self.client.get("/")
        # 2 active jobs (recruiting + submitting), not the complete one
        self.assertContains(response, ">2<")  # active jobs stat
        # 2 distinct languages in active+complete
        self.assertContains(response, "Languages")
        # 3 creators
        self.assertContains(response, ">3<")

    def test_landing_has_cta_buttons(self):
        response = self.client.get("/")
        self.assertContains(response, "Browse Jobs")
        self.assertContains(response, "Join as Creator")
        self.assertContains(response, "Post a Job")

    def test_landing_has_features(self):
        response = self.client.get("/")
        self.assertContains(response, "Voice-First Design")
        self.assertContains(response, "Interledger")
        self.assertContains(response, "How It Works")
