from django.contrib.auth import get_user_model
import pytest
from rest_framework import status
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from django.core import mail

from core.merchants.models import Merchant

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(scope="function")
def setup_merchant_data(db):
    tenant = Merchant.objects.create(
        name="Test Merchant",
        business_email="sampleemail@enterprise.com",
        support_email="test@example.com",
    )
    user = User.objects.create_user(
        username="merchantuser",
        email="sampleemail@enterprise.com",
        password="password123",
    )

    if user:
        tenant.user = user
        tenant.save()
    return tenant, user


@pytest.mark.django_db
def test_password_reset_successful(api_client, setup_merchant_data):
    tenant, user = setup_merchant_data
    url = reverse("password-reset")

    response = api_client.post(
        url, data={"email": tenant.business_email}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data
    assert "message" in response.data
    assert response.data["message"] == "Password reset email sent successfully"


@pytest.mark.parametrize(
    "invalid_email",
    ["nonexistent@email.com", "invalidemail@wrongemail.com", "notanemail"],
)
@pytest.mark.django_db
def test_password_reset_invalid_email(api_client, invalid_email):
    url = reverse("password-reset")

    response = api_client.post(url, data={"email": invalid_email}, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "message" in response.data
    assert response.data["message"] == "Email not found!"
