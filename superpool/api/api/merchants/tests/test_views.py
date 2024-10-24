import uuid
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APIClient

from api.merchants.tests.factories import MerchantFactory
from core.merchants.models import Merchant

fake = Faker()
client = APIClient()

REGISTRATION_V1_URL = reverse("merchant-v2-list")
REGISTRATION_URL = reverse("merchant-v2-list")
# LOGIN_URL = reverse("merchant:login")


@pytest.mark.django_db
def merchant_registration_payload() -> dict:
    return {
        "company_name": fake.company(),
        "business_email": fake.email(),
        "support_email": fake.email(),
    }


@pytest.mark.django_db
def test_merchant_registration_successful(client, merchant_registration_payload):
    """
    Test that a merchant can successfully register
    """
    response = client.post(
        reverse("merchant-v2-list"), merchant_registration_payload, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant registered successfully."


@pytest.mark.django_db
def test_merchant_registration_duplicate_email_already_exist(
    client,
    merchant_registration_payload,
):
    """
    Test that a merchant cannot register with an existing email
    """
    # Register a new merchant
    response = client.post(
        reverse("merchant-v2-list"), merchant_registration_payload, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant registered successfully."

    # Attempts to signup a new merchant with the same email
    response = client.post(
        reverse("merchant-v2-list"), merchant_registration_payload, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["message"] == "Merchant with this email already exists."


@pytest.mark.django_db
def test_merchant_registration_missing_fields_required(
    client, merchant_registration_payload
):
    """
    Test that a merchant cannot register without missing [required] fields
    """
    required_fields = ["company_name", "business_email", "support_email"]
    for field in required_fields:
        payload = merchant_registration_payload.copy()
        payload.pop(field)
        response = client.post(reverse("merchant-v2-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["message"]
            == f"{field.replace('_', ' ').capitalize()} is required."
        )


@patch("core.utils.send_verification_email")
@patch("core.utils.generate_verification_token")
@pytest.mark.django_db
def test_create_merchant_email_sending_error(
    client, mock_generate_token, mock_send_email, merchant_registration_payload
):
    """
    Test that a merchant is unable to recieve verification email due to internal server error
    """

    payload = merchant_registration_payload()
    payload["company_name"] = "Test Merchant"

    mock_generate_token.return_value = str(uuid.uuid4())
    mock_send_email.side_effect = Exception(
        "Unable to send merchant verification email"
    )

    response = client.post(REGISTRATION_URL, payload, format="json")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert (
        Merchant.objects.count() > 0
    )  # we are not currently using atomic transactions, instead merchant is created even if email sending fails
    # assert Merchant.objects.get(name=payload["name"]).business_email is not None

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
@patch("core.utils.generate_verification_token")
@pytest.mark.django_db
def test_create_merchant_successful(client, mock_send_email, mock_generate_token):
    """
    Test merchant creation with V2 Registration URL is successful
    """

    mock_generate_token.return_value = str(uuid.uuid4())
    payload = MerchantFactory.build()

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
def test_retrieve_merchant_by_valid_short_code(client, merchant_registration_payload):
    payload = MerchantFactory()
    short_code = "TES-LE09"
    payload["short_code"] = short_code
    payload["company_name"] = "Test Merchant"

    # Create the merchant
    response = client.post(reverse("merchant-v2-list"), payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant created successfully."

    RETRIEVE_ENDPOINT = reverse(
        "merchant-v2-retrieve-by-short-code",
        kwargs={"merchant_id": short_code},
    )
    # Retrieve the merchant
    response = client.get(RETRIEVE_ENDPOINT)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["data"]["short_code"] == short_code


@override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
@pytest.mark.django_db
@patch("core.utils.send_verification_email")
def test_merchant_short_code_in_email(mock_send_email, merchant_registration_payload):
    REGISTRATION_ENDPOINT = reverse("merchant-v2-list")

    # payload = MerchantFactory.build(
    #     name="Test Merchant",
    #     short_code="TES-LE09",
    #     business_email="testemail@bytonf.com",
    #     support_email="testemail@bytonf.com",
    # )
    payload = merchant_registration_payload.copy()
    payload.update(
        {
            "company_name": "Test Merchant",
            "short_code": "TES-LE09",
            "business_email": "testemail@bytonf.com",
            "support_email": "testemail@bytonf.com",
        }
    )
    response = client.post(REGISTRATION_ENDPOINT, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Merchant created successfully."

    # Retrieve the merchant from the data
    response_data = response.data
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

    # check that the business email is the same as the one sent
    business_email = payload["business_email"]
    assert (
        business_email == kwargs["email"]
    ), f"Expected email {business_email} but got {kwargs['email']}"
