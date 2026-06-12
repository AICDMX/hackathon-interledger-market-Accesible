from django.test import TestCase

from jobs.forms import JobApplicationForm
from jobs.models import Job, JobApplication
from users.models import User


class JobApplicationFormTest(TestCase):
    def setUp(self):
        self.funder = User.objects.create_user(
            username="funder", password="pass", role="funder"
        )
        self.creator = User.objects.create_user(
            username="creator",
            password="pass",
            role="creator",
            profile_note="I can deliver this quickly.",
        )
        self.job = Job.objects.create(
            title="Test Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget="10.00",
            funder=self.funder,
        )

    def test_prefills_profile_note_from_user_on_new_form(self):
        form = JobApplicationForm(user=self.creator)

        self.assertEqual(
            form.fields["profile_note"].initial, "I can deliver this quickly."
        )

    def test_does_not_override_existing_application_data(self):
        application = JobApplication.objects.create(
            job=self.job,
            applicant=self.creator,
            profile_note="Existing application note",
        )

        form = JobApplicationForm(instance=application, user=self.creator)

        self.assertNotEqual(
            form.fields["profile_note"].initial, "I can deliver this quickly."
        )
