import json
import tempfile
import os

from django.test import TestCase
from django.core.management import call_command
from io import StringIO

from users.models import User
from jobs.models import Job


class LoadDemoUsersCommandTest(TestCase):
    def test_load_from_custom_json(self):
        data = [
            {
                "username": "test_user_1",
                "email": "t1@test.com",
                "password": "testpass",
                "role": "creator",
                "preferred_language": "es",
                "native_languages": "nahuatl",
            }
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmpfile = f.name

        try:
            out = StringIO()
            call_command("load_demo_users", json_file=tmpfile, stdout=out)
            self.assertTrue(User.objects.filter(username="test_user_1").exists())
            user = User.objects.get(username="test_user_1")
            self.assertEqual(user.role, "creator")
        finally:
            os.unlink(tmpfile)

    def test_skip_existing_users(self):
        User.objects.create_user(username="existing", password="pass")
        data = [{"username": "existing", "email": "e@test.com"}]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmpfile = f.name

        try:
            out = StringIO()
            call_command("load_demo_users", json_file=tmpfile, stdout=out)
            output = out.getvalue()
            self.assertIn("Skipped", output)
        finally:
            os.unlink(tmpfile)

    def test_missing_json_file(self):
        out = StringIO()
        call_command("load_demo_users", json_file="/nonexistent.json", stdout=out)
        self.assertIn("not found", out.getvalue())

    def test_sets_seller_credentials(self):
        data = [
            {
                "username": "seller_test",
                "email": "s@test.com",
                "seller_key_id": "key-123",
                "seller_private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
                "seller_wallet_address": "https://wallet.example.com/seller",
            }
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmpfile = f.name

        try:
            call_command("load_demo_users", json_file=tmpfile, stdout=StringIO())
            user = User.objects.get(username="seller_test")
            self.assertEqual(user.seller_key_id, "key-123")
            self.assertEqual(
                user.seller_wallet_address, "https://wallet.example.com/seller"
            )
        finally:
            os.unlink(tmpfile)


class LoadDefaultJobsCommandTest(TestCase):
    def test_requires_demo_funder(self):
        out = StringIO()
        call_command("load_default_jobs", stdout=out)
        self.assertIn("demo_funder user not found", out.getvalue())

    def test_load_from_custom_json(self):
        User.objects.create_user(username="demo_funder", password="pass", role="funder")
        data = [
            {
                "title": "Test Job From JSON",
                "description": "A test job",
                "target_language_code": "nah",
                "deliverable_types": "text,audio",
                "amount_per_person": 100,
                "max_responses": 2,
                "status": "recruiting",
            }
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmpfile = f.name

        try:
            out = StringIO()
            call_command("load_default_jobs", json_file=tmpfile, stdout=out)
            self.assertTrue(Job.objects.filter(title="Test Job From JSON").exists())
            job = Job.objects.get(title="Test Job From JSON")
            self.assertEqual(job.budget, 200)
            self.assertEqual(job.status, "recruiting")
        finally:
            os.unlink(tmpfile)

    def test_skip_existing_jobs(self):
        funder = User.objects.create_user(
            username="demo_funder", password="pass", role="funder"
        )
        Job.objects.create(
            title="Existing Job",
            description="desc",
            target_language="en",
            deliverable_types="text",
            budget=50,
            funder=funder,
        )
        data = [
            {
                "title": "Existing Job",
                "description": "desc",
                "target_language_code": "en",
                "deliverable_types": "text",
                "amount_per_person": 50,
            }
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(data, f)
            tmpfile = f.name

        try:
            out = StringIO()
            call_command("load_default_jobs", json_file=tmpfile, stdout=out)
            self.assertIn("Skipped", out.getvalue())
        finally:
            os.unlink(tmpfile)
