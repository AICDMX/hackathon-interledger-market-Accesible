from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from jobs.payments_utils import create_incoming_payment


@override_settings(PAYMENTS_SERVICE_URL="http://payments.test")
class CreateIncomingPaymentTest(SimpleTestCase):
    @patch("jobs.payments_utils.requests.post")
    def test_success_uses_payment_id_alias(self, mock_post):
        response = Mock(status_code=200)
        response.json.return_value = {"success": True, "paymentId": "pay_123"}
        mock_post.return_value = response

        result = create_incoming_payment("10.50", "Test payment")

        self.assertEqual(
            result,
            {
                "success": True,
                "payment_id": "pay_123",
                "data": {"success": True, "paymentId": "pay_123"},
            },
        )
        mock_post.assert_called_once_with(
            "http://payments.test/api/payments/incoming",
            json={"amount": "10.50", "description": "Test payment"},
            timeout=30,
        )

    @patch("jobs.payments_utils.requests.post")
    def test_error_response_prefers_json_error_message(self, mock_post):
        response = Mock(status_code=500)
        response.json.return_value = {"error": "service down"}
        mock_post.return_value = response

        result = create_incoming_payment(12, "")

        self.assertEqual(result, {"success": False, "error": "service down"})

    @patch("jobs.payments_utils.requests.post")
    def test_request_exception_returns_connection_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("timed out")

        result = create_incoming_payment("5", "Delayed payment")

        self.assertEqual(
            result,
            {
                "success": False,
                "error": "Could not connect to payments service: timed out",
            },
        )
