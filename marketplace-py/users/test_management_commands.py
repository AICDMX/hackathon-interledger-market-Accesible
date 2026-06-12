import json
import os
import tempfile
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from users.models import User


class ConfigureSellerCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller_user", password="pass")

    def test_configures_seller_from_direct_private_key(self):
        out = StringIO()

        call_command(
            "configure_seller",
            "seller_user",
            wallet_address="https://wallet.example/seller",
            key_id="key-1",
            private_key="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
            stdout=out,
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.seller_key_id, "key-1")
        self.assertEqual(
            self.user.seller_wallet_address,
            "https://wallet.example/seller",
        )
        self.assertIn("Successfully configured seller credentials", out.getvalue())

    def test_configures_seller_from_private_key_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as handle:
            handle.write("pem-data")
            key_file = handle.name

        try:
            call_command(
                "configure_seller",
                "seller_user",
                wallet_address="https://wallet.example/seller",
                key_id="key-2",
                private_key_file=key_file,
                stdout=StringIO(),
            )
        finally:
            os.unlink(key_file)

        self.user.refresh_from_db()
        self.assertEqual(self.user.seller_private_key, "pem-data")

    def test_requires_private_key_or_file(self):
        with self.assertRaises(CommandError):
            call_command(
                "configure_seller",
                "seller_user",
                wallet_address="https://wallet.example/seller",
                key_id="key-3",
                stdout=StringIO(),
            )

    def test_errors_for_missing_user(self):
        with self.assertRaises(CommandError):
            call_command(
                "configure_seller",
                "missing-user",
                wallet_address="https://wallet.example/seller",
                key_id="key-3",
                private_key="pem-data",
                stdout=StringIO(),
            )


class LoadDemoUsersInvalidJsonTest(TestCase):
    def test_invalid_json_file_reports_error(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            handle.write("{bad json")
            bad_json = handle.name

        try:
            out = StringIO()
            call_command("load_demo_users", json_file=bad_json, stdout=out)
        finally:
            os.unlink(bad_json)

        self.assertIn("Invalid JSON", out.getvalue())


class LoadDefaultJobsInvalidJsonTest(TestCase):
    def test_invalid_json_file_reports_error(self):
        User.objects.create_user(username="demo_funder", password="pass", role="funder")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            handle.write("{bad json")
            bad_json = handle.name

        try:
            out = StringIO()
            call_command("load_default_jobs", json_file=bad_json, stdout=out)
        finally:
            os.unlink(bad_json)

        self.assertIn("Invalid JSON", out.getvalue())
