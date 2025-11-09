from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from users.models import User
from jobs.models import Job, JobSubmission


class PaymentsUITest(TestCase):
    def setUp(self):
        # Creator account to test "My Money" page
        self.creator = User.objects.create_user(
            username="creator1",
            password="pass1234",
            role="creator",
            wallet_endpoint="https://wallet.test/.well-known/pay"
        )
        # Funder account to own jobs and trigger approve_quote
        self.funder = User.objects.create_user(
            username="funder1",
            password="pass1234",
            role="funder",
            wallet_endpoint="https://wallet.test/funder/.well-known/pay"
        )

    def test_my_money_renders_wallet_and_totals(self):
        # Given an accepted submission for the creator worth 100
        job = Job.objects.create(
            title="Sample Job",
            description="Desc",
            target_language="es",
            target_dialect="",
            deliverable_types="text",
            amount_per_person=Decimal("100.00"),
            budget=Decimal("100.00"),
            funder=self.funder,
            status="reviewing",
        )
        JobSubmission.objects.create(
            job=job,
            creator=self.creator,
            status="accepted",
            is_draft=False,
        )

        # When the creator visits My Money
        self.client.login(username="creator1", password="pass1234")
        url = reverse("jobs:my_money")
        response = self.client.get(url)

        # Then the page renders and shows wallet + totals
        self.assertEqual(response.status_code, 200)
        # Check context values
        self.assertIn("total_earned", response.context)
        self.assertIn("total_spent", response.context)
        self.assertIn("balance", response.context)
        self.assertEqual(response.context["total_earned"], Decimal("100.00"))
        self.assertEqual(response.context["total_spent"], Decimal("0"))
        self.assertEqual(response.context["balance"], Decimal("100.00"))
        # Check simple UI text presence
        self.assertContains(response, "My Money")
        self.assertContains(response, "Wallet Endpoint")
        self.assertContains(response, "100.00")

    def test_approve_quote_requires_wallet_endpoint(self):
        # Funder without wallet should be redirected back with error
        funder_no_wallet = User.objects.create_user(
            username="funder2",
            password="pass1234",
            role="funder",
            wallet_endpoint=""
        )
        job = Job.objects.create(
            title="Needs Wallet",
            description="Desc",
            target_language="es",
            target_dialect="",
            deliverable_types="text",
            amount_per_person=Decimal("50.00"),
            budget=Decimal("50.00"),
            funder=funder_no_wallet,
            status="recruiting",
        )
        self.client.login(username="funder2", password="pass1234")
        url = reverse("jobs:approve_quote", kwargs={"pk": job.pk})
        response = self.client.get(url, follow=True)
        # Should end up back on job detail
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.view_name, "jobs:detail")
        # Error message about missing wallet should be present
        self.assertContains(response, "Please add your wallet address in your profile first.")

    @patch("jobs.views.start_quote")
    def test_approve_quote_redirects_to_wallet_on_success(self, mock_start_quote):
        # Mock payments service returning a redirect URL
        mock_start_quote.return_value = {
            "success": True,
            "redirect_url": "https://wallet.example/redirect"
        }
        job = Job.objects.create(
            title="Pay This",
            description="Desc",
            target_language="es",
            target_dialect="",
            deliverable_types="text",
            amount_per_person=Decimal("75.00"),
            budget=Decimal("75.00"),
            funder=self.funder,
            status="reviewing",
        )
        self.client.login(username="funder1", password="pass1234")
        url = reverse("jobs:approve_quote", kwargs={"pk": job.pk})
        response = self.client.get(url)
        # Should redirect to mocked wallet URL
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "https://wallet.example/redirect", fetch_redirect_response=False)

