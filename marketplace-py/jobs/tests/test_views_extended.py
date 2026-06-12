"""Extended view tests covering more flows and edge cases."""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from jobs.models import Job, JobApplication, JobSubmission
from users.models import User


class JobListFilterTest(TestCase):
    """Test browse page filtering and search."""

    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.job_nah = Job.objects.create(
            title="Nahuatl Job",
            description="Translate to nahuatl",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("100"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.job_oto = Job.objects.create(
            title="Otomi Job",
            description="Translate to otomi",
            target_language="oto",
            deliverable_types="audio",
            budget=Decimal("200"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )

    def test_search_by_title(self):
        response = self.client.get("/browse/?search=Nahuatl")
        self.assertContains(response, "Nahuatl Job")
        self.assertNotContains(response, "Otomi Job")

    def test_search_by_description(self):
        response = self.client.get("/browse/?search=otomi")
        self.assertContains(response, "Otomi Job")

    def test_filter_by_language(self):
        response = self.client.get("/browse/?language=nah")
        self.assertContains(response, "Nahuatl Job")
        self.assertNotContains(response, "Otomi Job")

    def test_empty_search_shows_all(self):
        response = self.client.get("/browse/?search=")
        self.assertContains(response, "Nahuatl Job")
        self.assertContains(response, "Otomi Job")

    def test_no_results(self):
        response = self.client.get("/browse/?search=nonexistent")
        self.assertContains(response, "No jobs available")

    def test_language_names_displayed(self):
        response = self.client.get("/browse/")
        self.assertContains(response, "Náhuatl")

    def test_funder_name_displayed(self):
        response = self.client.get("/browse/")
        self.assertContains(response, "Posted by")

    def test_status_badge_displayed(self):
        response = self.client.get("/browse/")
        self.assertContains(response, "Recruiting")

    def test_hide_applied_jobs(self):
        creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        JobApplication.objects.create(job=self.job_nah, applicant=creator)
        self.client.login(username="creator", password="pass")
        response = self.client.get("/browse/?hide_applied=on")
        self.assertNotContains(response, "Nahuatl Job")
        self.assertContains(response, "Otomi Job")


class EditJobViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.other = User.objects.create_user(
            username="other", password="pass", role="funder"
        )
        self.job = Job.objects.create(
            title="Editable Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("50"),
            funder=self.funder,
            status="draft",
        )

    def test_owner_can_view_edit(self):
        self.client.login(username="funder", password="pass")
        response = self.client.get(f"/{self.job.pk}/edit/")
        self.assertEqual(response.status_code, 200)

    def test_non_owner_cannot_edit(self):
        self.client.login(username="other", password="pass")
        response = self.client.get(f"/{self.job.pk}/edit/")
        self.assertIn(response.status_code, [302, 403, 404])

    def test_requires_login(self):
        response = self.client.get(f"/{self.job.pk}/edit/")
        self.assertEqual(response.status_code, 302)


class SubmitJobViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Submittable Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("50"),
            funder=self.funder,
            status="submitting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.application = JobApplication.objects.create(
            job=self.job, applicant=self.creator, status="selected"
        )

    def test_selected_creator_can_submit(self):
        self.client.login(username="creator", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/submit/",
            {"note": "Here is my work", "text_content": "Translation text"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            JobSubmission.objects.filter(job=self.job, creator=self.creator).exists()
        )

    def test_non_selected_creator_cannot_submit(self):
        other = User.objects.create_user(
            username="other_creator", password="pass", role="creator"
        )
        self.client.login(username="other_creator", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/submit/",
            {"note": "Sneaky", "text_content": "Nope"},
        )
        # Should redirect or deny
        self.assertIn(response.status_code, [302, 403])
        self.assertFalse(
            JobSubmission.objects.filter(job=self.job, creator=other).exists()
        )


class MarkSubmissionCompleteTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Complete Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("50"),
            funder=self.funder,
            status="submitting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.submission = JobSubmission.objects.create(
            job=self.job, creator=self.creator, status="pending", is_draft=False
        )

    def test_mark_complete_redirects(self):
        self.client.login(username="creator", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/mark-complete/{self.submission.pk}/"
        )
        # Should redirect regardless of outcome
        self.assertIn(response.status_code, [200, 302])


class JobDetailLanguageTest(TestCase):
    """Test that job detail shows language names not codes."""

    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.job = Job.objects.create(
            title="Language Test Job",
            description="desc",
            target_language="tzo",
            target_dialect="Altos de Chiapas",
            deliverable_types="text,audio",
            budget=Decimal("100"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )

    def test_detail_shows_language_name(self):
        response = self.client.get(f"/{self.job.pk}/")
        self.assertContains(response, "Tsotsil")

    def test_detail_shows_funder_name(self):
        response = self.client.get(f"/{self.job.pk}/")
        self.assertContains(response, "Posted by")

    def test_detail_shows_status_badge(self):
        response = self.client.get(f"/{self.job.pk}/")
        # The status_badge filter outputs styled HTML
        self.assertContains(response, "Recruiting")


class ViewApplicationsTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="App Test Job",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("50"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.creator,
            profile_note="I am a great translator",
        )

    def test_funder_can_view_applications(self):
        self.client.login(username="funder", password="pass")
        response = self.client.get(f"/{self.job.pk}/applications/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "great translator")

    def test_non_funder_cannot_view_applications(self):
        self.client.login(username="creator", password="pass")
        response = self.client.get(f"/{self.job.pk}/applications/")
        self.assertIn(response.status_code, [302, 403, 404])


class SelectApplicationRejectTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Select Test",
            description="desc",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("50"),
            funder=self.funder,
            status="selecting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.application = JobApplication.objects.create(
            job=self.job, applicant=self.creator, status="pending"
        )

    def test_reject_application(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/applications/{self.application.pk}/select/",
            {"action": "reject"},
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "rejected")

    def test_approve_application(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/applications/{self.application.pk}/select/",
            {"action": "approve"},
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "selected")

    def test_reset_to_pending(self):
        self.application.status = "selected"
        self.application.save()
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/applications/{self.application.pk}/select/",
            {"action": "pending"},
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "pending")
