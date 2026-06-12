from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from jobs.models import Job, JobApplication, JobSubmission, PendingPaymentTransaction
from users.models import User


class JobModelTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="testpass123", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="testpass123", role="creator"
        )
        self.job = Job.objects.create(
            title="Test Job",
            description="A test job",
            target_language="nah",
            deliverable_types="text,audio",
            amount_per_person=Decimal("50.00"),
            budget=Decimal("100.00"),
            funder=self.funder,
            status="draft",
            max_responses=2,
            expired_date=timezone.now() + timedelta(days=30),
        )

    def test_str(self):
        self.assertEqual(str(self.job), "Test Job")

    def test_get_absolute_url(self):
        self.assertEqual(self.job.get_absolute_url(), f"/{self.job.pk}/")

    def test_get_deliverable_types_list(self):
        self.assertEqual(self.job.get_deliverable_types_list(), ["text", "audio"])

    def test_get_deliverable_types_display(self):
        display = self.job.get_deliverable_types_display()
        self.assertIn("Text", display)
        self.assertIn("Audio", display)

    def test_default_recruit_deadline_set_on_create(self):
        """New jobs should get a recruit_deadline 7 days from now."""
        job = Job.objects.create(
            title="New Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
        )
        self.assertIsNotNone(job.recruit_deadline)
        # Should be roughly 7 days from now
        expected = timezone.now() + timedelta(days=7)
        self.assertAlmostEqual(
            job.recruit_deadline.timestamp(), expected.timestamp(), delta=5
        )

    def test_has_reference_media_false(self):
        self.assertFalse(self.job.has_reference_media())

    def test_get_accepted_submissions_count(self):
        self.assertEqual(self.job.get_accepted_submissions_count(), 0)
        JobSubmission.objects.create(
            job=self.job, creator=self.creator, status="accepted", is_draft=False
        )
        self.assertEqual(self.job.get_accepted_submissions_count(), 1)

    def test_get_pending_submissions_count(self):
        JobSubmission.objects.create(
            job=self.job, creator=self.creator, status="pending", is_draft=False
        )
        self.assertEqual(self.job.get_pending_submissions_count(), 1)

    def test_draft_submissions_excluded_from_counts(self):
        JobSubmission.objects.create(
            job=self.job, creator=self.creator, status="pending", is_draft=True
        )
        self.assertEqual(self.job.get_pending_submissions_count(), 0)
        self.assertEqual(self.job.get_submissions_count(), 0)

    def test_has_reached_max_responses(self):
        self.assertFalse(self.job.has_reached_max_responses())
        for i in range(2):
            u = User.objects.create_user(username=f"c{i}", password="pass")
            JobSubmission.objects.create(
                job=self.job, creator=u, status="accepted", is_draft=False
            )
        self.assertTrue(self.job.has_reached_max_responses())

    def test_get_remaining_responses_needed(self):
        self.assertEqual(self.job.get_remaining_responses_needed(), 2)
        JobSubmission.objects.create(
            job=self.job, creator=self.creator, status="accepted", is_draft=False
        )
        self.assertEqual(self.job.get_remaining_responses_needed(), 1)

    def test_has_reached_recruit_limit(self):
        self.job.recruit_limit = 2
        self.job.save()
        self.assertFalse(self.job.has_reached_recruit_limit())
        for i in range(2):
            u = User.objects.create_user(username=f"app{i}", password="pass")
            JobApplication.objects.create(job=self.job, applicant=u)
        self.assertTrue(self.job.has_reached_recruit_limit())

    def test_has_passed_recruit_deadline(self):
        self.job.recruit_deadline = timezone.now() + timedelta(days=1)
        self.assertFalse(self.job.has_passed_recruit_deadline())
        self.job.recruit_deadline = timezone.now() - timedelta(hours=1)
        self.assertTrue(self.job.has_passed_recruit_deadline())

    def test_has_passed_recruit_deadline_none(self):
        self.job.recruit_deadline = None
        self.assertFalse(self.job.has_passed_recruit_deadline())

    def test_should_transition_to_selecting_wrong_status(self):
        self.job.status = "draft"
        self.assertFalse(self.job.should_transition_to_selecting())

    def test_should_transition_to_selecting_limit_reached(self):
        self.job.status = "recruiting"
        self.job.recruit_limit = 1
        self.job.save()
        JobApplication.objects.create(job=self.job, applicant=self.creator)
        self.assertTrue(self.job.should_transition_to_selecting())

    def test_has_reached_submit_limit(self):
        self.job.submit_limit = 1
        self.job.save()
        JobSubmission.objects.create(
            job=self.job, creator=self.creator, is_draft=False
        )
        self.assertTrue(self.job.has_reached_submit_limit())

    def test_has_passed_submit_deadline(self):
        self.job.submit_deadline = None
        self.assertFalse(self.job.has_passed_submit_deadline())
        self.job.submit_deadline = timezone.now() - timedelta(hours=1)
        self.assertTrue(self.job.has_passed_submit_deadline())

    def test_should_transition_to_reviewing_wrong_status(self):
        self.job.status = "recruiting"
        self.assertFalse(self.job.should_transition_to_reviewing())

    def test_should_expire_recruiting_no_applications(self):
        self.job.status = "recruiting"
        self.job.expired_date = timezone.now() - timedelta(hours=1)
        self.assertTrue(self.job.should_expire())

    def test_should_expire_recruiting_with_applications(self):
        self.job.status = "recruiting"
        self.job.expired_date = timezone.now() - timedelta(hours=1)
        JobApplication.objects.create(job=self.job, applicant=self.creator)
        self.assertFalse(self.job.should_expire())

    def test_should_expire_submitting_no_submissions(self):
        self.job.status = "submitting"
        self.job.expired_date = timezone.now() - timedelta(hours=1)
        self.assertTrue(self.job.should_expire())

    def test_should_not_expire_if_date_not_passed(self):
        self.job.status = "recruiting"
        self.job.expired_date = timezone.now() + timedelta(days=1)
        self.assertFalse(self.job.should_expire())

    def test_auto_transition_recruiting_to_selecting_on_save(self):
        """When recruit limit is reached, saving should auto-transition to selecting."""
        job = Job.objects.create(
            title="Auto Transition Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
            status="recruiting",
            recruit_limit=1,
            expired_date=timezone.now() + timedelta(days=30),
        )
        JobApplication.objects.create(job=job, applicant=self.creator)
        job.save()
        job.refresh_from_db()
        self.assertEqual(job.status, "selecting")

    def test_submit_deadline_set_on_transition_to_submitting(self):
        """Submit deadline should be auto-set when transitioning to submitting."""
        job = Job.objects.create(
            title="Submit Deadline Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
            status="selecting",
            submit_deadline_days=5,
            expired_date=timezone.now() + timedelta(days=30),
        )
        job.status = "submitting"
        job.save()
        job.refresh_from_db()
        self.assertIsNotNone(job.submit_deadline)
        expected = timezone.now() + timedelta(days=5)
        self.assertAlmostEqual(
            job.submit_deadline.timestamp(), expected.timestamp(), delta=5
        )

    def test_ordering(self):
        job2 = Job.objects.create(
            title="Newer Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
        )
        jobs = list(Job.objects.all())
        self.assertEqual(jobs[0], job2)


class JobApplicationModelTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Test Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
        )

    def test_str(self):
        app = JobApplication.objects.create(job=self.job, applicant=self.creator)
        self.assertEqual(str(app), f"{self.creator.get_display_name()} - Test Job")

    def test_unique_together(self):
        JobApplication.objects.create(job=self.job, applicant=self.creator)
        with self.assertRaises(Exception):
            JobApplication.objects.create(job=self.job, applicant=self.creator)

    def test_default_status(self):
        app = JobApplication.objects.create(job=self.job, applicant=self.creator)
        self.assertEqual(app.status, "pending")


class JobSubmissionModelTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator", password="pass", role="creator"
        )
        self.job = Job.objects.create(
            title="Test Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
        )

    def test_str(self):
        sub = JobSubmission.objects.create(job=self.job, creator=self.creator)
        self.assertEqual(str(sub), "creator - Test Job")

    def test_default_values(self):
        sub = JobSubmission.objects.create(job=self.job, creator=self.creator)
        self.assertEqual(sub.status, "pending")
        self.assertFalse(sub.is_draft)
        self.assertFalse(sub.is_complete)
        self.assertIsNone(sub.completed_at)


class PendingPaymentTransactionTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.job = Job.objects.create(
            title="Test Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=Decimal("10.00"),
            funder=self.funder,
        )

    def test_str(self):
        txn = PendingPaymentTransaction.objects.create(
            contract_id="TEST123",
            job=self.job,
            buyer_wallet_data={"id": "buyer"},
            seller_wallet_data={"id": "seller"},
        )
        self.assertEqual(str(txn), "PendingTransaction-TEST123")

    def test_one_to_one_relationship(self):
        txn = PendingPaymentTransaction.objects.create(
            contract_id="TEST456",
            job=self.job,
            buyer_wallet_data={},
            seller_wallet_data={},
        )
        self.assertEqual(self.job.pending_transaction, txn)
