import uuid
from typing import NewType
from unittest.mock import patch

import pytest
from api.merchants.tests.factories import MerchantFactory
from core.merchants.models import Merchant
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from django.test import TestCase, override_settings

fake = Faker()
client = APIClient()

REGISTRATION_V1_URL = reverse("merchant-list")
REGISTRATION_URL = reverse("merchant-v2-list")
RETRIEVE_ENDPOINT = reverse("merchant-v2-detail")
# LOGIN_URL = reverse("merchant:login")


@pytest.mark.django_db
def merchant_registration_payload() -> dict:
    return {
        "name": fake.name(),
        "registration_number": fake.random_number(),
        "business_email": fake.email(),
        "password": fake.password(),
    }


@pytest.mark.django_db
def test_merchant_registration_successful(merchant_registration_payload):
    """
    Test that a merchant can successfully register
    """
    response = client.post(REGISTRATION_V1_URL, merchant_registration_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant registered successfully."


@pytest.mark.django_db
def test_merchant_registration_duplicate_email_already_exist(
    merchant_registration_payload,
):
    """
    Test that a merchant cannot register with an existing email
    """
    response = client.post(REGISTRATION_V1_URL, merchant_registration_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant registered successfully."

    # Attempts to signup a new merchant with the same email
    response = client.post(REGISTRATION_V1_URL, merchant_registration_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Merchant with this email already exists."


@pytest.mark.django_db
def test_merchant_registration_missing_fields_required(merchant_registration_payload):
    """
    Test that a merchant cannot register without missing [required] fields
    """
    for field in merchant_registration_payload:
        payload = merchant_registration_payload.copy()
        payload.pop(field)
        response = client.post(REGISTRATION_V1_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["message"] == f"{field.capitalize()} is required."


@patch("core.utils.send_verification_email")
@patch("core.utils.generate_verfication_token")
@pytest.mark.django_db
def test_create_merchant_email_sending_error(
    mock_generate_token, mock_send_email, merchant_registration_payload
):
    """
    Test that a merchant is unable to recieve verification email due to internal server error
    """

    payload = merchant_registration_payload()

    mock_generate_token.return_value = str(uuid.uuid4())
    mock_send_email.side_effect = Exception(
        "Unable to send merchant verification email"
    )

    response = client.post(REGISTRATION_URL, payload, format="json")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert Merchant.objects.count() != 1
    assert Merchant.objects.get(name=payload["name"]).business_email is not None

    mock_generate_token.assert_called_once()
    mock_send_email.assert_called_with(
        payload["business_email"], mock_generate_token.return_value
    )


@pytest.mark.django_db
def test_create_merchant_duplicate_email_returns_api_error():
    """
    Test that merchant is only allowed one and ONLY one business email per account
    """

    from .factories import MerchantFactory

    payload = MerchantFactory()
    response = client.post(REGISTRATION_URL, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "business_email" in response.data
    assert Merchant.objects.count() == 1
    assert (
        response.data["business_email"][0]
        == "A merchant with this business email already exists."
    )


@patch("core.utils.send_verification_email")
@patch("core.utils.generate_verfication_token")
@pytest.mark.django_db
def test_create_merchant_successful(mock_send_email, mock_generate_token):
    """
    Test merchant creation with V2 Registration URL is successful
    """

    mock_generate_token.return_value = str(uuid.uuid4())
    payload = MerchantFactory()

    # Ensure we have a unique email address
    payload["business_email"] = "uniquetestmail@example.com"
    response = client.post(REGISTRATION_URL, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant created successfully."
    assert Merchant.objects.count() != 1

    # assert the method is called at least once
    assert (
        Merchant.objects.get(name=payload["name"]).business_email
        == "uniquetestmail@example.com"
    )
    mock_generate_token.assert_called_once()
    mock_send_email.assert_called_with(
        payload["business_email"], mock_generate_token.return_value
    )


@pytest.mark.django_db
def test_retrieve_merchant_by_valid_short_code():
    payload = MerchantFactory()
    payload["short_code"] = "TES-LE09"

    # Create the merchant
    response = client.post(REGISTRATION_URL, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant created successfully."

    # Retrieve the merchant
    response = client.get(RETRIEVE_ENDPOINT, data=payload)

    assert response.status_code == status.HTTP_200_OK
    # Do some checking of the short code here


@override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
@pytest.mark.django_db
@patch("core.utils.send_verification_email")
def test_merchant_short_code_in_email(mock_send_email):
    REGISTRATION_ENDPOINT = reverse("merchant-v2-list")

    payload = MerchantFactory.build(
        name="Test Merchant",
        short_code="TES-LE09",
        business_email="testemail@bytonf.com",
        support_email="testemail@bytonf.com",
    )
    response = client.post(REGISTRATION_ENDPOINT, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant created successfully."

    # Retrieve the merchant from the data
    response_data = response.json()

    response_short_code = response_data["data"]["short_code"]

    # Check that the send_verification_email function was called with the correct arguments
    assert mock_send_email.call_count == 1
    args, kwargs = mock_send_email.call_args

    print(f"args: {args}")
    print(f"kwargs: {kwargs}")

    try:
        verification_token, email_short_code = args[1:3]
    except IndexError:
        pytest.fail(
            "send_verification_email was not called with the expected arguments"
        )

    # check that the short code is the same as the one sent
    assert (
        response_short_code == email_short_code
    ), f"Expected short code {response_short_code} but got {email_short_code}"
