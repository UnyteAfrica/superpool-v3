from unittest.mock import patch

import requests
from django.test import TestCase

from api.integrations.heirs.exceptions import HeirsAPIException
from api.integrations.heirs.services import HeirsAssuranceService


class HeirsAssuranceServiceTests(TestCase):
    def setUp(self):
        self.service = HeirsAssuranceService()
        self.product_id = 823

    @patch("api.integrations.heirs.client.HeirsLifeAssuranceClient.get")
    def test_get_quote_success(self, mock_get):
        """Test the successful retrieval of an auto insurance quote."""
        mock_response = {
            "quote_id": "12345",
            "product_id": self.product_id,
            "motor_value": 5000000,
            "premium": 150000,
        }
        mock_get.return_value = mock_response
        response = self.service.get_quote(
            category="auto",
            product_id=self.product_id,
            motor_value=5000000,
            motor_class="Private",
            motor_type="Saloon",
        )
        self.assertEqual(response["quote_id"], "12345")
        self.assertEqual(response["premium"], 150000)
        self.assertEqual(response["product_id"], "auto_01")
        mock_get.assert_called_once()

    @patch("api.integrations.heirs.client.HeirsLifeAssuranceClient.get")
    def test_get_quote_api_error(self, mock_get):
        """Test when the API returns an error response."""
        mock_error_response = {
            "type": "error",
            "title": "Invalid Product",
            "detail": "The product ID is invalid.",
            "status": "404",
        }
        mock_get.return_value = mock_error_response

        with self.assertRaises(HeirsAPIException):
            self.service.get_quote(
                category="auto",
                product_id="invalid_product_id",
                motor_value=5000000,
                motor_class="class_a",
                motor_type="sedan",
            )

        mock_get.assert_called_once()

    @patch("api.integrations.heirs.client.HeirsLifeAssuranceClient.get")
    def test_get_quote_http_error(self, mock_get):
        """Test when the client raises an HTTPError."""
        mock_get.side_effect = requests.HTTPError("Internal Server Error")

        response = self.service.get_quote(
            category="auto",
            product_id=self.product_id,
            motor_value=5000000,
            motor_class="Private",
            motor_type="Sedan",
        )

        self.assertEqual(response["error"]["type"], "http_error")
        self.assertEqual(
            response["error"]["title"], "HTTP Error when get_quote was called to Heirs"
        )
        mock_get.assert_called_once()

    @patch("api.integrations.heirs.client.HeirsLifeAssuranceClient.get")
    def test_get_quote_unexpected_error(self, mock_get):
        """Test when an unexpected error occurs."""
        mock_get.side_effect = Exception("Unexpected Error")

        response = self.service.get_quote(
            category="auto",
            product_id=self.product_id,
            motor_value=5000000,
            motor_class="Commercial",
            motor_type="Saloon",
        )

        self.assertEqual(response["error"]["type"], "unexpected_error")
        self.assertEqual(
            response["error"]["title"],
            "An unexpected error occurred when requesting quotes from Heirs",
        )
        mock_get.assert_called_once()
