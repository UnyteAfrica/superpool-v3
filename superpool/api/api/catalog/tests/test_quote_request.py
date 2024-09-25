import pytest
from django.db import transaction
from django.urls import reverse
from rest_framework.test import APIClient

from core.catalog.models import Price, Product, ProductTier, Quote
from core.models import Coverage
from core.providers.models import Provider as InsuranceProvider


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def setup_data():
    provider_1 = InsuranceProvider.objects.create(name="AXA")
    provider_2 = InsuranceProvider.objects.create(name="BedRock Global Partners")

    product_1 = Product.objects.create(
        provider=provider_1, name="Phone Insurance", product_type="Gadget"
    )
    product_2 = Product.objects.create(
        provider=provider_2, name="Laptop Insurance", product_type="Gadget"
    )

    tier_1 = ProductTier.objects.create(
        product=product_1, tier_name="Basic", base_premium=500
    )
    tier_2 = ProductTier.objects.create(
        product=product_1, tier_name="Premium", base_premium=1000
    )

    coverage_1 = Coverage.objects.create(
        coverage_name="Accidental Damage",
        coverage_limit=50000,
        coverage_type=Coverage.CoverageType.DAMAGES,
    )
    coverage_2 = Coverage.objects.create(
        coverage_name="Theft",
        coverage_limit=100000,
        coverage_type=Coverage.CoverageType.LIABILITY,
    )

    return {
        "provider_1": provider_1,
        "provider_2": provider_2,
        "product_1": product_1,
        "product_2": product_2,
        "tier_1": tier_1,
        "tier_2": tier_2,
        "coverage_1": coverage_1,
        "coverage_2": coverage_2,
    }


@pytest.mark.django_db
class TestQuoteRequestView:
    def test_filter_products_by_type(self, setup_data):
        products = Product.objects.filter(
            provider__name__in=[setup_data["provider_1"].name], product_type="Gadget"
        )

        assert products.count() == 1
        assert products.first().name == "Phone Insurance"

    def test_tier_and_coverage(self, setup_data):
        tiers = setup_data["product_1"].tiers.all()
        assert tiers.count() == 2

        basic_tier = tiers.first()
        coverages = basic_tier.coverages.all()

        assert coverages.count() == 1
        assert coverages.first().coverage_name == "Accidental Damage"

    def test_quote_creation(self, setup_data):
        with transaction.atomic():
            premium = Price.objects.create(
                amount=setup_data["tier_1"].base_premium,
                description=f"{setup_data['product_1'].name} - {setup_data['tier_1'].tier_name} Premium",
            )

            quote = Quote.objects.create(
                product=setup_data["product_1"],
                premium=premium,
                base_price=setup_data["tier_1"].base_premium,
                additional_metadata={
                    "tier_name": setup_data["tier_1"].tier_name,
                    "coverage_details": [
                        {
                            "coverage_name": setup_data["coverage_1"].coverage_name,
                            "coverage_description": setup_data[
                                "coverage_1"
                            ].description,
                            "coverage_type": setup_data["coverage_1"].coverage_name,
                            "coverage_limit": str(
                                setup_data["coverage_1"].coverage_limit
                            ),
                        }
                    ],
                    "exclusions": setup_data["tier_1"].exclusions or "",
                    "benefits": setup_data["tier_1"].benefits or "",
                    "product_type": setup_data["product_1"].product_type,
                    "available_tiers": [
                        setup_data["tier_1"].tier_name,
                        setup_data["tier_2"].tier_name,
                    ],  # All addons available for this product
                },
            )

        assert quote.base_price == 500
        assert quote.additional_metadata["tier_name"] == "Basic"

    def test_integration_quote_request(self, api_client, setup_data):
        request_data = {
            "insurance_details": {
                "product_type": "Gadget",
                "additional_information": {},
            },
            "coverage_preferences": {
                "coverage_type": [],
                "coverage_amount": "1000000",
                "additional_coverages": [],
            },
        }

        response = api_client.post(
            reverse("request-quote"),
            data=request_data,
            content_type="application/json",
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "data" in response_data
        assert len(response_data["data"]) > 0

    @pytest.mark.parametrize(
        "product_type,expected_product_name",
        [
            ("Gadget", "Phone Insurance"),
            ("Home", "Home Insurance"),
        ],
    )
    def test_product_type_filtering(
        self, setup_data, product_type, expected_product_name
    ):
        products = Product.objects.filter(product_type=product_type)

        if product_type == "Gadget":
            assert products.count() == 2
            assert products.first().name == expected_product_name
