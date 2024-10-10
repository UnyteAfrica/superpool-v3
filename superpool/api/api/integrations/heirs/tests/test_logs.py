from unittest.mock import patch

import requests
from django.test import TestCase

from api.integrations.heirs.services import HeirsAssuranceService


class TestHeirsAssuranceServiceLogs(TestCase):
    """
    Ensures the returned logs of the `HeirsAssuranceService.get_quote` method
    matches the expected logs.
    """

    def setUp(self) -> None:
        self.motor_params = {
            "product_id": 823,
            "motor_value": 5000000,
            "motor_class": "Private",
            "motor_type": "SUV",
        }
        self.travel_params = {
            "product_id": 10811,
            "start_date": "2024-10-17",
            "end_date": "2024-10-24",
            "customer_age": 30,
            "product_name": "FAMILY (WORLD WIDE)",
        }
        # Device Insurance - Ultra-Sheild Device Plan
        # Let's say, the price of a samsung
        self.device_params = {
            "product_id": 1307,
            "device_value": 2_232_000,
        }
        # Home Insurance - Home Protect Plus Plan
        self.home_params = {
            "product_id": 1051,
            "property_value": 9_000_000,
            "stationary_value": 100_000,
            "mobile_items_value": 200_000,
        }
        # POS Insurance
        self.pos_device_params = {
            "product_id": 1286,
            "device_value": 70000,
        }

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
