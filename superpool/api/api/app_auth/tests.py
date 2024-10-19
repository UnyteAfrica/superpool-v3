from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.merchants.models import Merchant
from core.models import APIKey as APIKeyModel

User = get_user_model()


class APIKeyAuthenticationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="password", role="merchant"
        )
        self.merchant = Merchant.objects.create(user=self.user)
        self.api_key_model = APIKeyModel.objects.create(merchant=self.merchant)
        self.api_key = self.api_key_model.key

        self.client = APIClient()

    def test_valid_api_key_authentication(self):
        """
        Test that a valid API key authenticates successfully.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"SUPERPOOL {self.api_key}")

        response = self.client.post("/api/v1/environments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_invalid_api_key_authentication(self):
        """
        Test that an invalid API key results in an authentication failure.
        """
        self.client.credentials(HTTP_AUTHORIZATION="SUPERPOOL invalid_key")
        response = self.client.get("/api/v1/environments/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid API key", response.data.get("detail", ""))

    def test_missing_api_key_authentication(self):
        """
        Test that a missing API key results in an authentication failure.
        """
        response = self.client.get("/api/v1/environments/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            "Authentication credentials were not provided.",
            response.data.get("detail", ""),
        )

    def test_incorrect_prefix_api_key_authentication(self):
        """
        Test that an API key with the incorrect prefix fails authentication.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"WRONGPREFIX {self.api_key}")
        response = self.client.get("/api/v1/environments/")

        # Assert that the request fails with 401 Unauthorized due to incorrect prefix
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            "Invalid API key header. No credentials provided.",
            response.data.get("detail", ""),
        )
