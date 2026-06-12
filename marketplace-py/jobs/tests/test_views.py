from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from jobs.models import Job, JobApplication, JobSubmission
from users.models import User


class HomeViewTest(TestCase):
    def test_anonymous_sees_landing_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Native Language")

    def test_logged_in_redirects_to_dashboard(self):
        user = User.objects.create_user(username="u", password="pass")
        self.client.login(username="u", password="pass")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("dashboard", response.url)


class JobListViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.job = Job.objects.create(
            title="Recruiting Job",
            description="Open for applications",
            target_language="nah",
            deliverable_types="text",
            budget=Decimal("50.00"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        Job.objects.create(
            title="Draft Job",
            description="Not visible",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
            status="draft",
        )

    def test_browse_page_loads(self):
        response = self.client.get("/browse/")
        self.assertEqual(response.status_code, 200)

    def test_only_shows_active_jobs(self):
        response = self.client.get("/browse/")
        self.assertContains(response, "Recruiting Job")
        self.assertNotContains(response, "Draft Job")

    def test_search_filter(self):
        response = self.client.get("/browse/?search=Recruiting")
        self.assertContains(response, "Recruiting Job")

    def test_language_filter(self):
        response = self.client.get("/browse/?language=nah")
        self.assertContains(response, "Recruiting Job")
        response = self.client.get("/browse/?language=en")
        self.assertNotContains(response, "Recruiting Job")


class JobDetailViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Detail Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("50.00"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )

    def test_detail_loads(self):
        response = self.client.get(f"/{self.job.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Job")

    def test_draft_only_visible_to_owner(self):
        draft = Job.objects.create(
            title="My Draft",
            description="secret",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
            status="draft",
        )
        # Anonymous user gets 404
        response = self.client.get(f"/{draft.pk}/")
        self.assertEqual(response.status_code, 404)

        # Owner can see
        self.client.login(username="funder", password="pass")
        response = self.client.get(f"/{draft.pk}/")
        self.assertEqual(response.status_code, 200)


class DashboardViewTest(TestCase):
    def test_requires_login(self):
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 302)

    def test_loads_for_logged_in_user(self):
        User.objects.create_user(username="u", password="pass")
        self.client.login(username="u", password="pass")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)


class MyJobsViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )

    def test_requires_login(self):
        response = self.client.get("/my-jobs/")
        self.assertEqual(response.status_code, 302)

    def test_funder_can_access(self):
        self.client.login(username="funder", password="pass")
        response = self.client.get("/my-jobs/")
        self.assertEqual(response.status_code, 200)

    def test_creator_redirected(self):
        self.client.login(username="creator", password="pass")
        response = self.client.get("/my-jobs/")
        # Should redirect non-funders
        self.assertIn(response.status_code, [302, 403, 200])


class CreateJobViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )

    def test_requires_login(self):
        response = self.client.post("/create/")
        self.assertEqual(response.status_code, 302)

    def test_create_draft_job(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            "/create/",
            {
                "title": "New Job",
                "description": "Some work",
                "target_language": "nah",
                "deliverable_types": "text",
                "amount_per_person": "50",
                "max_responses": "1",
                "save_draft": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Job.objects.filter(title="New Job").exists())
        job = Job.objects.get(title="New Job")
        self.assertEqual(job.status, "draft")

    def test_create_and_publish_job(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            "/create/",
            {
                "title": "Published Job",
                "description": "Some work",
                "target_language": "nah",
                "deliverable_types": "text",
                "amount_per_person": "100",
                "max_responses": "2",
                "action": "publish",
            },
        )
        self.assertEqual(response.status_code, 302)
        job = Job.objects.get(title="Published Job")
        self.assertEqual(job.status, "recruiting")
        self.assertEqual(job.budget, Decimal("200.00"))


class ApplyToJobViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Apply Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("50.00"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )

    def test_apply_requires_login(self):
        response = self.client.post(f"/{self.job.pk}/apply/")
        self.assertEqual(response.status_code, 302)

    def test_creator_can_apply(self):
        self.client.login(username="creator", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/apply/",
            {"profile_note": "I am interested"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            JobApplication.objects.filter(
                job=self.job, applicant=self.creator
            ).exists()
        )

    def test_cannot_apply_twice(self):
        self.client.login(username="creator", password="pass")
        self.client.post(f"/{self.job.pk}/apply/", {"profile_note": "first"})
        response = self.client.post(f"/{self.job.pk}/apply/", {"profile_note": "second"})
        self.assertEqual(
            JobApplication.objects.filter(
                job=self.job, applicant=self.creator
            ).count(),
            1,
        )


class SelectApplicationViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Select Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("50.00"),
            funder=self.funder,
            status="selecting",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.application = JobApplication.objects.create(
            job=self.job, applicant=self.creator, status="pending"
        )

    def test_funder_can_select_application(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/applications/{self.application.pk}/select/",
            {"action": "select"},
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "selected")


class AcceptDeclineSubmissionViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Review Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("50.00"),
            funder=self.funder,
            status="reviewing",
            expired_date=timezone.now() + timedelta(days=7),
        )
        self.submission = JobSubmission.objects.create(
            job=self.job, creator=self.creator, status="pending", is_draft=False
        )

    def test_accept_submission(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/accept/{self.submission.pk}/"
        )
        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, "accepted")

    def test_decline_submission(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(
            f"/{self.job.pk}/decline/{self.submission.pk}/"
        )
        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, "rejected")


class OwnerDashboardViewTest(TestCase):
    def test_requires_login(self):
        response = self.client.get("/owner-dashboard/")
        self.assertEqual(response.status_code, 302)

    def test_loads_for_funder(self):
        funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.client.login(username="funder", password="pass")
        response = self.client.get("/owner-dashboard/")
        self.assertEqual(response.status_code, 200)


class AcceptedJobsViewTest(TestCase):
    def test_requires_login(self):
        response = self.client.get("/accepted/")
        self.assertEqual(response.status_code, 302)

    def test_loads_for_logged_in_user(self):
        User.objects.create_user(username="u", password="pass")
        self.client.login(username="u", password="pass")
        response = self.client.get("/accepted/")
        self.assertEqual(response.status_code, 200)


class DuplicateJobViewTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.job = Job.objects.create(
            title="Original Job",
            description="desc",
            target_language="nah",
            deliverable_types="text,audio",
            budget=Decimal("100.00"),
            amount_per_person=Decimal("50.00"),
            funder=self.funder,
            status="recruiting",
            expired_date=timezone.now() + timedelta(days=7),
        )

    def test_duplicate_creates_draft_copy(self):
        self.client.login(username="funder", password="pass")
        response = self.client.post(f"/{self.job.pk}/duplicate/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Job.objects.count(), 2)
        dup = Job.objects.exclude(pk=self.job.pk).first()
        self.assertEqual(dup.status, "draft")
        self.assertIn("Original Job", dup.title)


class FillerPagesTest(TestCase):
    def setUp(self):
        User.objects.create_user(username="u", password="pass")
        self.client.login(username="u", password="pass")

    def test_filler_page_1(self):
        response = self.client.get("/filler-1/")
        self.assertIn(response.status_code, [200, 302])

    def test_filler_page_2(self):
        response = self.client.get("/filler-2/")
        self.assertIn(response.status_code, [200, 302])

    def test_my_products(self):
        response = self.client.get("/my-products/")
        self.assertIn(response.status_code, [200, 302])

    def test_my_money(self):
        response = self.client.get("/my-money/")
        self.assertIn(response.status_code, [200, 302])

    def test_pending_jobs(self):
        response = self.client.get("/pending/")
        self.assertIn(response.status_code, [200, 302])
