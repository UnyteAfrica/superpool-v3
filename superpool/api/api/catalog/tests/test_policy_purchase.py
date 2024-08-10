import random
import pytest
from django.urls import reverse
from api.catalog.services import PolicyService
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from api.merchants.tests.factories import MerchantFactory
from .factories import (
    CustomerFactory,
    PartnerFactory,
    ProductFactory,
    QuoteFactory,
)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture(scope="session")
def purchase_policy_data():
    customer = CustomerFactory()
    partner = PartnerFactory()
    merchant = MerchantFactory()
    product = ProductFactory(provider=partner)
    quote = QuoteFactory(product=product)

    return {
        "quote": quote.quote_code,
        "customer_metadata": {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "customer_email": customer.email,
            "customer_phone": customer.phone_number,
            "customer_address": customer.address,
            "customer_date_of_birth": customer.dob,
            "customer_gender": customer.gender,
        },
        "product_metadata": {
            "product_name": product.name,
            "product_type": product.product_type,
        },
        "payment_metadata": {
            "payment_method": random.choice(
                ["credit_card", "debit_card", "cash", "bank_transfer"]
            ),
            "premium_amount": quote.premium.amount,
        },
        "activation_metadata": {
            "policy_expiry_date": "",
            "renew": random.choice([True, False]),
        },
        "merchant_code": merchant.short_code,
    }


# UNIT TESTS
# Unit tests test the service classes independently of the Django framework.
#
# Test Case 1: Test the purchase policy  with valid data
@pytest.mark.django_db
def test_purchase_policy_valid_data_is_successful(purchase_policy_data):
    purchase_policy_data = purchase_policy_data
    policy_service = PolicyService()
    policy = policy_service.purchase_policy(purchase_policy_data)

    assert policy is not None


# Test Case 2: Test the purchase policy  with invalid data
@pytest.mark.django_db
def test_purchase_policy_invalid_data_fails(purchase_policy_data):
    purchase_policy_data = purchase_policy_data
    purchase_policy_data["quote"] = "INVALID_QUOTE_CODE"

    policy_service = PolicyService()

    with pytest.raises(Exception):
        policy_service.purchase_policy(purchase_policy_data)


# Test Case 3: Test the purchase policy with missing data
def test_purchase_policy_missing_data_fails():
    purchase_policy_data = {}

    policy_service = PolicyService()

    with pytest.raises(Exception):
        policy_service.purchase_policy(purchase_policy_data)


# INTEGRATION TESTS
# Integration tests test the service classes with the Django framework (through the APIs).
#
# Test Case 4: Test the purchase policy API with valid data
def test_purchase_policy_api_valid_data_is_successful(client, purchase_policy_data):
    response = client.post(
        reverse("purchase-policy"),
        purchase_policy_data,
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data
