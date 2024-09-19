from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from api.integrations.heirs.client import HeirsLifeAssuranceClient
from api.integrations.heirs.services import HeirsAssuranceService
from core.providers.integrations.heirs.registry import (
    DevicePolicy,
    DevicePolicyRequest,
    DeviceQuoteParams,
    MotorPolicy,
    MotorPolicyRequest,
    PersonalAccidentPolicy,
    PersonalAccidentPolicyRequest,
    TravelPolicyClass,
    TravelPolicyRequest,
)


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
    return HeirsAssuranceService()


@pytest.fixture
def customer_fixture():
    return {
        "John Doe": {
            "firstName": "John",
            "lastName": "Doe",
            "otherName": "Smith",
            "dateOfBirth": "1990-01-01",
            "startDate": "2024-07-15",
            "endDate": "2024-10-15",
            "categoryName": "Business",
            "country_id": "NG",
            "email": "john.doe@email.com",
            "address": "123 Street",
            "nextOfKinName": "Jane Doe",
            "relation": "Wife",
            "passportNo": "A1234567",
            "partnersEmail": "jane.doe@example.com",
            "gender": "male",
            "phone": "1234567890",
            "occupation": "Engineer",
        },
        "Jane Doe": {
            "firstName": "Jane",
            "lastName": "Doe",
            "otherName": "Smith",
            "dateOfBirth": "1990-01-01",
            "startDate": "2024-07-15",
            "endDate": "2024-07-15",
            "categoryName": "Personal",
            "country_id": "US",
            "email": "jane.doe@example.com",
            "address": "123 Street",
            "nextOfKinName": "John Doe",
            "relation": "Husband",
            "passportNo": "A1234568",
            "partnersEmail": "john.doe@example.com",
            "gender": "female",
            "phone": "1234567890",
            "occupation": "Doctor",
        },
    }


def test_register_policy_holder(service, data_fixture):
    with patch.object(HeirsLifeAssuranceClient, "post") as mock_post:
        policy_holder_endpoint = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/policy_holder"
        mock_post.return_value = {
            "status_code": 200,
            "json.return_value": {"message": "Policy holder registered successfully"},
        }

        response = service.register_policy_holder(data_fixture)

        assert response["message"] == "Policy holder registered successfully"

        assert mock_post.assert_called_once_with(policy_holder_endpoint, data_fixture)


def test_fetch_all_products(service):
    test_product_class = "Motor"
    with patch.object(HeirsLifeAssuranceClient, "get") as mock_get:
        company = "Heirs%20Insurance"
        products_by_class_resource_endpoint = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/{company}/class/{test_product_class}/product"
        mock_response = MagicMock(
            status_code=200, data=[{"id": 1, "name": "Test Product"}]
        )
        mock_get.return_value = mock_response

        response = service.product_queryset(test_product_class)
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert mock_get.assert_called_once_with(products_by_class_resource_endpoint)


def test_fetch_policy_information_with_policy_number_is_successful(service):
    company = "Heirs%20Insurance"

    with patch.object(HeirsLifeAssuranceClient, "get") as mock_get:
        policy_number = "POLICYX256"
        policy_info_endpoint = (
            f"{settings.HEIRS_ASSURANCE_STAGING_URL}/{company}/policy/{policy_number}"
        )

        response = service.get_policy_details(policy_number)
        assert response.status_code == 200
        assert response.data is not None
        assert mock_get.assert_called_once_with(policy_info_endpoint)


def test_fetch_policy_information_with_invalid_policy_number_is_unsuccessful(service):
    company = "Heirs%20Insurance"

    with patch.object(HeirsLifeAssuranceClient, "get") as mock_get:
        policy_number = ""
        policy_info_endpoint = (
            f"{settings.HEIRS_ASSURANCE_STAGING_URL}/{company}/policy/{policy_number}"
        )
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        response = service.get_policy_details(policy_number)
        assert response.status_code in (401, 403, 404)
        assert mock_get.assert_called_once_with(policy_info_endpoint)


def test_fetch_personal_accident_quotes(service, mocker):
    params = {}
    with mocker.patch.object(HeirsLifeAssuranceClient, "get") as mock_get:
        params["product_id"] = "1234Heirs"
        personal_accident_quotes_endpoint = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/personal-accident/quote/{params.get('product_id')}"

        mock_response = MagicMock(status_code=200, data={"premium": 22_000})
        mock_get.return_value = mock_response

        response = service.get_quote("personal_accident", params)
        assert response.status_code == 200
        mock_get.assert_called_once_with(personal_accident_quotes_endpoint)


def test_register_personal_accident_policy(service, customer_fixture, mocker):
    product_id = "2032"
    register_personal_accident_endpoint = (
        f"{settings.HEIRS_ASSURANCE_STAGING_URL}/personal-accident/{product_id}/policy"
    )
    mock_post = mocker.patch.object(HeirsLifeAssuranceClient, "post")
    mock_post.return_value = {
        "policy_id": "20425",
        "status": "success",
        "status_code": 201,
    }

    accident_policy_details = PersonalAccidentPolicyRequest(
        policyHolderId="holder_1",
        items=[customer_fixture["Jane Doe"]],
    )
    product = PersonalAccidentPolicy(policy_details=accident_policy_details)

    response = service.register_policy(1, product)

    # build the test payload
    test_payload = {
        "policyHolderId": "holder_1",
        "items": [customer_fixture["Jane Doe"]],
    }

    assert isinstance(response["policy_id"], str)
    assert response["status"] == "success"
    assert response.status_code == 201
    mock_post.assert_called_once_with(register_personal_accident_endpoint, test_payload)


def test_register_travel_policy(service, customer_fixture, mocker):
    product_id = "1212"
    register_travel_policy_endpoint = (
        f"{settings.HEIRS_ASSURANCE_STAGING_URL}/travel/{product_id}/policy"
    )
    mock_post = mocker.patch.object(HeirsLifeAssuranceClient, "post")
    mock_post.return_value = {
        "status_code": 201,
        "policy_id": "80801",
        "status": "success",
    }

    test_payload = {
        "policyHolderId": "holder_1",
        "items": [customer_fixture["John Doe"]],
    }

    travel_policy_details = TravelPolicyRequest(
        policyHolderId="holder_1", items=[customer_fixture["John Doe"]]
    )
    product = TravelPolicyClass(travel_policy_details)
    response = service.register_policy(2, product)

    assert response.status_code == 201
    assert response["policy_id"] == "80801"
    mock_post.assert_called_once_with(register_travel_policy_endpoint, test_payload)


def test_register_auto_policy(service, customer_fixture, mocker):
    product_id = "AU2345X"
    register_motor_policy_endpoint = (
        f"{settings.HEIRS_ASSURANCE_STAGING_URL}/motor/{product_id}/policy"
    )
    mock_post = mocker.patch.object(HeirsLifeAssuranceClient, "post")
    mock_post.return_value = {
        "status_code": 201,
        "policy_id": "MOTO22335",
        "status": "success",
    }

    test_payload = {
        "policyHolderId": "holder_1",
        "items": [customer_fixture["John Doe"]],
    }

    motor_policy_details = MotorPolicyRequest(
        policyHolderId="holder_1", items=[customer_fixture["John Doe"]]
    )
    product = MotorPolicy(motor_policy_details)
    response = service.register_policy(3, product)

    assert response.status_code == 201
    assert response["policy_id"] == "MOTO22335"
    mock_post.assert_called_once_with(register_motor_policy_endpoint, test_payload)


def test_register_device_insurance_policy_is_successful(service, mocker):
    policy_holder = "UserX2204"
    device_policy_endpoint = f"{settings.HEIRS_ASSURANCE_STAGING_URL}/device/policy"
    product_id = "DEV-POL2x23"
    device_info = {
        "value": 2,
        "make": "Apple",
        "model": "Iphone16ProMax",
        "serialNumber": "IProPro16",
        "imei": "AppleXx-2356799-100003",
        "deviceType": "Phone",
    }
    device_policy_details = DevicePolicyRequest(
        policyHolderId=policy_holder, items=[device_info]
    )
    product = DevicePolicy(device_policy_details)
    response = service.register_policy(product_id, product)

    mock_post = mocker.patch.object(HeirsLifeAssuranceClient, "post")
    mock_post.return_value = {
        "status_code": 201,
        "policy_id": "HEIRS-DEV-POL-2022",
        "policy_status": "pending",
        "premium": 2200,
        "policy_holder_id": "UserX2204",
    }
    assert response.status_code == 201
    assert "premium" in response.data
    assert "policy_status" in response.data
    assert "policy_id" in response.data
    assert response.data["policy_holder_id"] == policy_holder
    mock_post.assert_called_once_with(device_policy_endpoint, device_info)


def test_fetch_device_insurance_quote(service, mocker):
    item_value = 13_000
    product_id = "DEV-POL2x23"
    device_quote_endpoint = (
        f"{settings.HEIRS_ASSURANCE_STAGING_URL}/device/quote/{item_value}"
    )
    request_params = {"product_id": product_id, "item_value": item_value}
    device_params = DeviceQuoteParams(
        productId=request_params["product_id"], itemValue=request_params["item_value"]
    )
    response = service.get_quote("device", device_params)

    mock_get = mocker.patch.object(HeirsLifeAssuranceClient, "get")
    mock_get.return_value = {"status_code": 200, "data": {"premium": 40_000}}
    assert response.status_code == 200
    assert "premium" in response.data
    mock_get.assert_called_once_with(device_quote_endpoint, request_params)
