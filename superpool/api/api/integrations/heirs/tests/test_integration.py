from unittest.mock import patch

import pytest
from api.integrations.heirs.client import HeirsLifeAssuranceClient
from api.integrations.heirs.services import HeirsAssuranceService
from django.conf import settings


@pytest.fixture
def data_fixture():
    return {
        "firstName": "Johnthan",
        "lastName": "Joestar",
        "dateOfBirth": "1990-01-01",
        "gender": "male",
        "phone": "1234567890",
        "occupation": "Engineer",
        "email": "jojoestar@example.com",
        "idCardImgUrl": "http://example.com/id.jpg",
        "utilityImgUrl": "http://example.com/utility.jpg",
        "city": "City",
        "state": "State",
        "address": "123 Main St",
        "country": "Country",
        "street": "Main St",
        "streetNumber": "123",
        "postCode": "12345",
        "number": "ID123456",
        "expiry": "2025-01-01",
        "type": "driversLicense",
    }


@pytest.fixture
def service():
    service = HeirsAssuranceService()


def test_register_policy_holder(service, data_fixture):
    with patch.object(HeirsLifeAssuranceClient, "post") as mock_post:
        policy_holder_endpoint = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/policy_holder"
        mock_post.return_value = {
            "status_code": 200,
            "json.return_value": {"message": "Policy holder registered successfully"},
        }

        response = service.register_policy_holder(data_fixture)

        assert response["message"] == {
            "message": "Policy holder registered successfully"
        }
        assert mock_post.assert_called_once_with(policy_holder_endpoint, data_fixture)


def test_fetch_all_products(service):
    test_product_class = "Motor"
    with patch.object(HeirsLifeAssuranceClient, "get") as mock_get:
        company = "Heirs%20Insurance"
        products_by_class_resource_endpoint = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/{company}/class/{test_product_class}/product"

        response = service.product_queryset()
        assert response.status_code == 200
        assert len(response.data) >= 1
