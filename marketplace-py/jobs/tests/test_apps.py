from unittest.mock import patch

from django.test import SimpleTestCase

from jobs import apps


class JobsAppTest(SimpleTestCase):
    @patch("django.core.management.call_command")
    def test_load_default_jobs_handler_calls_command(self, mock_call_command):
        apps.load_default_jobs_handler(sender=None)

        mock_call_command.assert_called_once_with("load_default_jobs", verbosity=0)

    @patch("django.core.management.call_command", side_effect=RuntimeError("boom"))
    def test_load_default_jobs_handler_swallows_command_errors(self, mock_call_command):
        apps.load_default_jobs_handler(sender=None)

        mock_call_command.assert_called_once_with("load_default_jobs", verbosity=0)
