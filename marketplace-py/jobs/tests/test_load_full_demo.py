from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from jobs.management.commands.load_full_demo import Command


class LoadFullDemoCommandTest(SimpleTestCase):
    def test_handle_runs_load_steps_in_order_without_reset(self):
        command = Command()
        call_order = []

        command._load_users = MagicMock(side_effect=lambda: call_order.append("users"))
        command._load_jobs = MagicMock(side_effect=lambda: call_order.append("jobs"))
        command._create_applications = MagicMock(
            side_effect=lambda: call_order.append("applications")
        )
        command._create_submissions = MagicMock(
            side_effect=lambda: call_order.append("submissions")
        )
        command._wire_audio = MagicMock(side_effect=lambda: call_order.append("audio"))
        command._print_summary = MagicMock(side_effect=lambda: call_order.append("summary"))
        command.stdout = MagicMock()
        command.style.SUCCESS = lambda message: message
        command.style.WARNING = lambda message: message

        command.handle(reset=False)

        self.assertEqual(
            call_order,
            ["users", "jobs", "applications", "submissions", "audio", "summary"],
        )

    @patch("jobs.management.commands.load_full_demo.PendingPaymentTransaction")
    @patch("jobs.management.commands.load_full_demo.JobSubmission")
    @patch("jobs.management.commands.load_full_demo.JobApplication")
    @patch("jobs.management.commands.load_full_demo.Job")
    @patch("jobs.management.commands.load_full_demo.AudioSnippet")
    @patch("jobs.management.commands.load_full_demo.StaticUIElement")
    @patch("jobs.management.commands.load_full_demo.User")
    def test_handle_reset_clears_demo_models_before_loading(
        self,
        mock_user,
        mock_static_ui,
        mock_audio_snippet,
        mock_job,
        mock_job_application,
        mock_job_submission,
        mock_pending_payment,
    ):
        command = Command()
        command._load_users = MagicMock()
        command._load_jobs = MagicMock()
        command._create_applications = MagicMock()
        command._create_submissions = MagicMock()
        command._wire_audio = MagicMock()
        command._print_summary = MagicMock()
        command.stdout = MagicMock()
        command.style.SUCCESS = lambda message: message
        command.style.WARNING = lambda message: message

        command.handle(reset=True)

        mock_pending_payment.objects.all.return_value.delete.assert_called_once()
        mock_job_submission.objects.all.return_value.delete.assert_called_once()
        mock_job_application.objects.all.return_value.delete.assert_called_once()
        mock_job.objects.all.return_value.delete.assert_called_once()
        mock_audio_snippet.objects.all.return_value.delete.assert_called_once()
        mock_static_ui.objects.all.return_value.delete.assert_called_once()
        mock_user.objects.exclude.assert_called_once_with(username="admin")
        mock_user.objects.exclude.return_value.delete.assert_called_once()
