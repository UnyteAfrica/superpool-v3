import pytest
from rest_framework.test import APIClient
from core.catalog.models import Product, Quote
from core.catalog.models import Price
from core.providers.models import Provider as InsuranceProvider
from django.urls import reverse


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def provider_fixture():
    provider, created = InsuranceProvider.objects.get_or_create(
        name="AIICO",
        id="1",
        support_email="support@aiioexample.com",
        support_phone="08012345678",
    )
    return provider


@pytest.fixture
def data_fixture(provider_fixture):
    # create the insurer
    aiico_insurance = provider_fixture

    product_health, created = Product.objects.get_or_create(
        name="Health Insurance",
        product_type="Health",
        product_description="Health",
        provider=aiico_insurance,
        # product_price=1000,
    )

    product_auto, created = Product.objects.get_or_create(
        name="Auto Insurance",
        product_type="Auto",
        product_description="Auto",
        provider=aiico_insurance,
        # product_price=2000,
    )

    product_travel, created = Product.objects.get_or_create(
        name="Travel Insurance",
        product_type="Travel",
        product_description="Travel",
        provider=aiico_insurance,
        # product_price=3000,
    )
    print(f"Created product for health insurance: {product_health}")
    print(f"Created product for auto insurance: {product_auto}")
    print(f"Created product for travel insurance: {product_travel}")

    return product_health, product_auto, product_travel


@pytest.fixture
def quotes(data_fixture, provider_fixture):
    product_health, product_auto, product_travel = data_fixture

    # Create or get the Prices instance (The Premiums)
    premium_health, created = Price.objects.get_or_create(
        amount=1000.0, description="Standard health insurance premium"
    )

    premium_auto, created = Price.objects.get_or_create(
        amount=1500.0, description="Comprehensive auto insurance premium"
    )

    premium_travel, created = Price.objects.get_or_create(
        amount=2000.0, description="Standard travel insurance premium"
    )

    # create quote instances
    quote_health = Quote.objects.create(
        product=product_health,
        quote_code="QH001",
        base_price=1000,
        premium=premium_health,
        additional_metadata={
            "coverage": "Standard",
            "age": "30",
            "health_condition": "good",
        },
    )

    quote_auto = Quote.objects.create(
        product=product_auto,
        quote_code="QA001",
        base_price=2000,
        premium=premium_auto,
        additional_metadata={
            "coverage": "Standard",
            "age": "30",
            "car_make": "Toyota",
        },
    )

    quote_travel = Quote.objects.create(
        product=product_travel,
        quote_code="QT001",
        base_price=3000,
        premium=premium_travel,
        additional_info={
            "coverage": "Standard",
            "age": "30",
            "destination": "USA",
        },
    )

    print(f"Created quote for health insurance: {quote_health}")
    print(f"Created quote for auto insurance: {quote_auto}")
    print(f"Created quote for travel insurance: {quote_travel}")
    return quote_health, quote_auto, quote_travel


def test_request_quotes_successful(api_client, quotes):
    data = {
        "product": quotes[0].product.id,
        "quote_code": "QH001",
        "base_price": 1000,
        "premium": quotes[0].premium.id,
        "additional_metadata": {
            "coverage": "Standard",
            "age": "30",
            "health_condition": "good",
        },
    }
    response = api_client.post(reverse("request-quote"), data=data, format="json")
    assert response.status_code == 200
    assert response.json() is not None
    assert response.json() == data
