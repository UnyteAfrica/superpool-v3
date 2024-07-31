from rest_framework.test import APIClient
from rest_framework.status import status
import uuid
from core.catalog.models import Policy
from core.catalog.models import Product
from core.providers.models import Provider as Partner
from core.user.models import Customer
from datetime import datetime, timedelta
from django.urls import reverse
import pytest


@pytest.fixture
def client():
    return APIClient()


RENEWAL_URL = reverse("policy-renew")


@pytest.fixture
def data_fixture():
    test_insurer = Partner.objects.create(
        id=str(uuid.uuid4()),
        name="Test Insurer",
        support_email="support@testinsurer.com",
        support_phone="08012345678",
    )

    health_package = Product.objects.create(
        id=str(uuid.uuid4()),
        provider_id=test_insurer,
        name="Health Insurance",
        description="Health Insurance package",
        product_type=Product.ProductType.HEALTH,
        coverage_details="Covers medical expenses",
    )

    customer_ABC = Customer.objects.create(
        first_name="John",
        last_name="Doe",
        email="john.doey@email.com",
        phone_number="08012345678",
        address="123, Fake Street, Lagos",
        dob="1990-01-01",
        gender="M",
        verification_type="ID-Card",
        verification_id="1234567890",
    )

    policy_fixture = Policy.objects.create(
        policy_id=str(uuid.uuid4()),
        policy_number="POL-1234567890",  #  Optional
        policy_holder="John Doe",
        policy_type=health_package,
        effective_from=datetime.now().date() - timedelta(days=30),
        effective_to=datetime.now().date() + timedelta(days=60),  # about 3 months apart
    )

    return {
        "policy": policy_fixture,
        "customer": customer_ABC,
        "product": health_package,
        "insurance_provider": test_insurer,
    }


# POLICY RENEWAL SUCCESSFUL
@pytest.mark.django_db
def test_policy_renewal_is_successful(client, data_fixture):
    policy_id = data_fixture["policy"].policy_id
    # The payload should look like this
    # Although the policy_number  and the policy_id are optional, one of them must be provided
    # auto_renew is optional and defaults to False
    # {
    #   "policy_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", (optional)
    #   "policy_number": "string", (optional)
    #   "policy_end_date": "2024-07-31",
    #   "auto_renew": true
    # }
    policy_renewal_payload = {
        "policy_id": policy_id,
        "policy_end_date": "2025-01-01",
    }
    response = client.post(RENEWAL_URL, policy_renewal_payload)
    assert response.status_code == 200
    assert response.data == {"status": "success"}


# MISSING POLICY ID OR POLICY NUMBER
def test_policy_renewal_fails_missing_policy_id_or_policy_number(client, data_fixture):
    data = {
        "policy_end_date": (datetime.now().date() + timedelta(days=365)).isoformat(),
    }
    response = client.post(RENEWAL_URL, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["renewal_status"] == "failed"


# NON-EXISTENT POLICY
def test_policy_renewal_fails_policy_not_found(client, data_fixture):
    data = {
        "policy_id": "invalid-policy-id",
        "policy_end_date": (datetime.now().date() + timedelta(days=365)).isoformat(),
    }
    response = client.post(RENEWAL_URL, data, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["renewal_status"] == "failed"
    assert response.data["message"] == "Policy not found"


#  POLICY RENEWAL DATE IS IN THE PAST
def test_policy_renewal_fails_validation_renewal_date_in_past(client, data_fixture):
    data = {
        "policy_id": data_fixture["policy"].policy_id,
        "policy_end_date": (
            datetime.now().date() - timedelta(days=365)
        ).isoformat(),  #  1 year ago
    }

    response = client.post(RENEWAL_URL, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["renewal_status"] == "failed"
    assert response.data["errors"]["policy_end_date"] == [
        "Renewal date cannot be in the past"
    ]


# POLICY RENEWAL SERVER_ERROR
def test_policy_renewal_fails_server_error(client, data_fixture):
    """
    This test case simulates a server error when the policy renewal request is made.
    """

    new_policy = Policy.objects.create(
        policy_id=str(uuid.uuid4()),
        policy_number="POL-1234567890",
        policy_holder="John Doe",
        policy_type=Product.objects.first(),
        effective_from=datetime.now().date() - timedelta(days=30),
        effective_to=datetime.now().date() + timedelta(days=60),
    )
    pass
