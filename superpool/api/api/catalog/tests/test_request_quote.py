from datetime import timedelta

import pytest
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.catalog.models import Price, Product, Quote
from core.providers.models import Provider as InsuranceProvider


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def provider_fixture():
    provider, created = InsuranceProvider.objects.get_or_create(
        name="AIICO",
        support_email="support@aiioexample.com",
        support_phone="08012345678",
    )
    return provider


@pytest.fixture
def data_fixture(provider_fixture):
    aiico_insurance = provider_fixture

    # Create or get products
    product_health, _ = Product.objects.get_or_create(
        name="Health Insurance",
        product_type="Health",
        description="Health",
        provider=aiico_insurance,
    )

    product_auto, _ = Product.objects.get_or_create(
        name="Auto Insurance",
        product_type="Auto",
        description="Auto",
        provider=aiico_insurance,
    )

    product_travel, _ = Product.objects.get_or_create(
        name="Travel Insurance",
        product_type="Travel",
        description="Travel",
        provider=aiico_insurance,
    )

    product_home, _ = Product.objects.get_or_create(
        name="Home Insurance",
        product_type="Home",
        description="Home",
        provider=aiico_insurance,
    )

    product_gadget, _ = Product.objects.get_or_create(
        name="Gadget Insurance",
        product_type="Gadget",
        description="Gadget",
        provider=aiico_insurance,
    )

    return product_health, product_auto, product_travel, product_home, product_gadget


@pytest.fixture
def quotes(data_fixture):
    product_health, product_auto, product_travel, product_home, product_gadget = (
        data_fixture
    )

    # Create or get prices (premiums)
    premium_health, _ = Price.objects.get_or_create(
        amount=1000.0, description="Standard health insurance premium"
    )

    premium_auto, _ = Price.objects.get_or_create(
        amount=1500.0, description="Comprehensive auto insurance premium"
    )

    premium_travel, _ = Price.objects.get_or_create(
        amount=2000.0, description="Standard travel insurance premium"
    )

    premium_home, _ = Price.objects.get_or_create(
        amount=2500.0, description="Standard home insurance premium"
    )

    premium_gadget, _ = Price.objects.get_or_create(
        amount=500.0, description="Standard gadget insurance premium"
    )

    # Create or get quotes
    quote_health, _ = Quote.objects.get_or_create(
        product=product_health,
        quote_code="QH001",
        defaults={
            "base_price": 1000,
            "premium": premium_health,
            "expires_in": timezone.now() + timedelta(days=30),
            "status": "pending",
        },
    )

    quote_auto, _ = Quote.objects.get_or_create(
        product=product_auto,
        quote_code="QA001",
        defaults={
            "base_price": 2000,
            "premium": premium_auto,
            "expires_in": timezone.now() + timedelta(days=30),
            "status": "pending",
        },
    )

    quote_travel, _ = Quote.objects.get_or_create(
        product=product_travel,
        quote_code="QT001",
        defaults={
            "base_price": 3000,
            "premium": premium_travel,
            "expires_in": timezone.now() + timedelta(days=30),
            "status": "pending",
        },
    )

    quote_home, _ = Quote.objects.get_or_create(
        product=product_home,
        quote_code="QH002",
        defaults={
            "base_price": 4000,
            "premium": premium_home,
            "expires_in": timezone.now() + timedelta(days=30),
            "status": "pending",
        },
    )

    quote_gadget, _ = Quote.objects.get_or_create(
        product=product_gadget,
        quote_code="QG001",
        defaults={
            "base_price": 5000,
            "premium": premium_gadget,
            "expires_in": timezone.now() + timedelta(days=30),
            "status": "pending",
        },
    )

    return quote_health, quote_auto, quote_travel, quote_home, quote_gadget


@pytest.mark.django_db
@override_settings(DATABASES={"default": {"ATOMIC_REQUESTS": True}})
def test_request_quotes_successful(api_client, quotes):
    quote_health, quote_auto, quote_travel, quote_home, quote_gadget = quotes

    test_data = [
        {
            "product_type": "health",
            "quote_code": quote_health.quote_code,
            "base_price": quote_health.base_price,
            "premium": quote_health.premium.id,
            "additional_metadata": {
                "coverage": "Standard",
                "age": "30",
                "health_condition": "good",
            },
        },
        {
            "product_type": "auto",
            "quote_code": quote_auto.quote_code,
            "base_price": quote_auto.base_price,
            "premium": quote_auto.premium.id,
            "additional_metadata": {
                "coverage": "Standard",
                "age": "30",
                "car_make": "Toyota",
            },
        },
        {
            "product_type": "travel",
            "quote_code": quote_travel.quote_code,
            "base_price": quote_travel.base_price,
            "premium": quote_travel.premium.id,
            "additional_metadata": {
                "coverage": "Standard",
                "age": "30",
                "destination": "USA",
            },
        },
        {
            "product_type": "home",
            "quote_code": quote_home.quote_code,
            "base_price": quote_home.base_price,
            "premium": quote_home.premium.id,
            "additional_metadata": {
                "coverage": "Standard",
                "property_value": "1000000",
                "home_type": "Duplex",
                "location": "Lagos",
            },
        },
        {
            "product_type": "gadget",
            "quote_code": quote_gadget.quote_code,
            "base_price": quote_gadget.base_price,
            "premium": quote_gadget.premium.id,
            "additional_metadata": {
                "coverage": "Standard",
                "gadget_type": "smartphone",
                "gadget_make": "Samsung",
            },
        },
    ]

    for quote_data in test_data:
        response = api_client.post(
            reverse("request-quote"), data=quote_data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data is not None
        assert response_data["quote_code"] == quote_data["quote_code"]


@pytest.mark.django_db
@override_settings(DATABASES={"default": {"ATOMIC_REQUESTS": True}})
def test_request_quote_with_invalid_data_unsuccessful(api_client):
    data = {
        "product_type": "unknown",
        "quote_code": "INVALID_CODE",
        "additional_metadata": {
            "coverage": "Standard",
            "age": "30",
        },
    }
    response = api_client.post(reverse("request-quote"), data=data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@override_settings(DATABASES={"default": {"ATOMIC_REQUESTS": True}})
def test_request_quote_with_missing_required_fields_unsuccessful(api_client, quotes):
    health_quote = quotes[0]
    data = {
        "product_type": health_quote.product.product_type.lower(),
        "quote_code": health_quote.quote_code,
        "additional_metadata": {
            "coverage": "Standard",
            "age": "30",
        },
    }
    response = api_client.post(reverse("request-quote"), data=data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
