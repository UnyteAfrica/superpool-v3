from unittest.mock import patch

import requests
from django.test import TestCase

from api.integrations.heirs.services import HeirsAssuranceService


class HeirsAssuranceServiceTest(TestCase):
    @patch("api.integrations.base.BaseClient.get")
    def test_get_quote_success(self, mock_get):
        # Setup mock response
        mock_response = {
            "quote_code": "HEIRS123",
            "premium": 300000.00,
            "additional_info": "Heirs premium quote",
        }
        mock_get.return_value = mock_response

        service = HeirsAssuranceService()

        category = "auto"
        params = {
            "product_id": "823",
            "motor_value": "2500000.00",
            "motor_class": "personal",
            "motor_type": "saloon",
        }

        with self.assertLogs("api_client", level="INFO") as log:
            response = service.get_quote(category=category, **params)
            self.assertEqual(response, mock_response)

            # Check logs
            self.assertIn(
                "GET Request URL: motor/quote/PID123/2500000.00/personal/saloon",
                log.output[0],
            )
            self.assertIn("GET Response Status: 200 | Response:", log.output[1])

    @patch("api.integrations.base.BaseClient.get")
    def test_get_quote_missing_parameter(self, mock_get):
        service = HeirsAssuranceService()
        category = "auto"
        params = {
            "product_id": "823",
            "motor_value": "2500000.00",
            # Missing 'motor_class' and 'motor_type'
        }

        with self.assertLogs("api_client", level="ERROR") as log:
            with self.assertRaises(ValueError) as context:
                service.get_quote(category=category, **params)

            self.assertIn(
                "Missing required parameter 'motor_class' for category 'auto'.",
                str(context.exception),
            )
            self.assertIn(
                "Missing required parameter 'motor_class' for category 'auto'.",
                log.output[-1],
            )

    @patch("api.integrations.base.BaseClient.get")
    def test_get_quote_api_failure(self, mock_get):
        mock_get.side_effect = requests.HTTPError("API Error")

        service = HeirsAssuranceService()
        category = "auto"
        params = {
            "product_id": "PID123",
            "motor_value": "2500000.00",
            "motor_class": "personal",
            "motor_type": "saloon",
        }

        with self.assertLogs("api_client", level="ERROR") as log:
            response = service.get_quote(category=category, **params)
            self.assertIn("error", response)
            self.assertEqual(response["error"], "API Error")
            self.assertIn("Failed to retrieve quote: API Error", log.output[-1])
