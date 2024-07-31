from rest_framework.test import APIClient
import pytest


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def policy():
    import uuid
    from core.catalog.models import Policy
    from core.catalog.models import Product
    from core.providers.models import Provider as Partner

    test_insurer = Partner.objects.create(
        name="Test Insurer",
        support_email="support@testinsurer.com",
        support_phone="08012345678",
    )

    health_package = Product.objects.create(
        product_id=uuid.uuid4(),
        provider_id=test_insurer,
        name="Health Insurance",
        description="Health Insurance package",
        product_type=Product.ProductType.HEALTH,
        coverage_details="Covers medical expenses",
    )

    return Policy.objects.create(
        policy_id=uuid.uuid4(),
        policy_holder="John Doe",
        policy_type=health_package,
        effective_from="2021-01-01",
        effective_to="2022-01-01",
    )


@pytest.mark.django_db
def test_policy_renewal_is_successful(client, policy):
    policy_id = policy.policy_id
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
    response = client.post("/policies/renew/", policy_renewal_payload)
    assert response.status_code == 200
    assert response.data == {"status": "success"}
