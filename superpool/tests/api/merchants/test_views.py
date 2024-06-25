from typing import NewType

import pytest
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

fake = Faker()
client = APIClient()

URL = NewType("URL", str)

REGISTRATION_URL: URL = reverse("merchant:register")
LOGIN_URL: URL = reverse("merchant:login")


@pytest.mark.django_db
def merchant_registration_payload() -> dict:
    return {
        "name": fake.name(),
        "registration_number": fake.random_number(),
        "business_email": fake.email(),
        "password": fake.password(),
    }


def test_merchant_registration_successful(merchant_registration_payload):
    """
    Test that a merchant can successfully register
    """
    response = client.post(REGISTRATION_URL, merchant_registration_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant registered successfully."


def test_merchant_registration_duplicate_email_already_exist(
    merchant_registration_payload,
):
    """
    Test that a merchant cannot register with an existing email
    """
    response = client.post(REGISTRATION_URL, merchant_registration_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant registered successfully."

    # Attempts to signup a new merchant with the same email
    response = client.post(REGISTRATION_URL, merchant_registration_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Merchant with this email already exists."


def test_merchant_registration_missing_fields_required(merchant_registration_payload):
    """
    Test that a merchant cannot register without missing [required] fields
    """
    for field in merchant_registration_payload:
        payload = merchant_registration_payload.copy()
        payload.pop(field)
        response = client.post(REGISTRATION_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == f"{field.capitalize()} is required."
