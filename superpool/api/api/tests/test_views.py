import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.merchants.tests.factories import MerchantFactory
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


@pytest.mark.django_db
def test_password_reset_no_args_unsuccessful(api_client):
    url = reverse("password-reset")
    response = api_client.post(url, data={"email": ""}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "message" in response.data


@pytest.mark.django_db
def test_password_confirmation_successful(api_client):
    url = reverse("password-reset-confirm")
    response = api_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.data
    assert response.data["message"] == "Your password has been successfully updated"


@pytest.mark.django_db
def test_merchant_forgot_tenant_id_successful(api_client):
    merchant = MerchantFactory.build(
        name="Zabuza Incorporation",
        business_email="rogueninjacorp@hiddenmist.com",
        support_email="zabuza@akatuski.com",
    )

    url = reverse("merchant-forgot-credentials")
    response = api_client.post(url, kwargs={"email": merchant.business_email})

    assert response.status_code == status.HTTP_200_OK
    assert response.data
    # assert "message" in response.data

    # assert len(mail.outbox) == 1
    # email = mail.outbox[0]
    # assert merchant.tenant_id in email.body


@pytest.mark.parametrize(
    "email, expected_status, expected_message",
    [
        # sceneraio 1 - nonexistent email
        (
            "nonexistent@email.com",
            status.HTTP_400_BAD_REQUEST,
            "No merchant found for the provided email address",
        ),
        # sceneraio 2 - invalid email formaat
        (
            "invalid-format",
            status.HTTP_400_BAD_REQUEST,
            "Invalid email address. Enter a valid email addres",
        ),
        # sceneraio 3 - empty email input
        ("", status.HTTP_400_BAD_REQUEST, "Email address is required"),
    ],
)
@pytest.mark.django_db
def test_merchant_forgot_tenant_id_invalid_credentials(
    api_client, email, expected_status, expected_message
):
    url = reverse("merchant-forgot-credentials")
    response = api_client.post(url, kwargs={"email": email})

    assert response.status_code == expected_status
    assert response.data
    # assert 'message' in response.data
    # assert response.data["message"] == expected_message


@pytest.mark.django_db
def test_merchant_forgot_tenant_id_no_args(api_client):
    url = reverse("merchant-forgot-credentials")
    response = api_client.post(url, kwargs={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data
    assert "message" in response.data
    # assert response.data["message"] == "Email address is required"
