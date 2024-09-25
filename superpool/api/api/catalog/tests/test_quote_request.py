import json

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
    provider_3 = InsuranceProvider.objects.create(name="Leadway Assurance")
    provider_4 = InsuranceProvider.objects.create(name="Reliance Insurance")

    # product_1 = Product.objects.create(
    #     provider=provider_1, name="Phone Insurance", product_type="Gadget"
    # )
    # product_2 = Product.objects.create(
    #     provider=provider_2, name="Laptop Insurance", product_type="Gadget"
    # )
    #
    # tier_1 = ProductTier.objects.create(
    #     product=product_1, tier_name="Basic", base_premium=500
    # )
    # tier_2 = ProductTier.objects.create(
    #     product=product_1, tier_name="Premium", base_premium=1000
    # )
    #
    # coverage_1 = Coverage.objects.create(
    #     coverage_name="Accidental Damage",
    #     coverage_limit=50000,
    #     coverage_type=Coverage.CoverageType.DAMAGES,
    # )
    # coverage_2 = Coverage.objects.create(
    #     coverage_name="Theft",
    #     coverage_limit=100000,
    #     coverage_type=Coverage.CoverageType.LIABILITY,
    # )

    # we would use this to access the products when we are
    # creating their associated tiers and coverages
    products_store = {}
    products = [
        # BEWARE SOME OF THESE PRODUCTS ARE INTENTIONALLY
        # REDUNDANT, IT IS MEANT TO TEST, DIFFERENT PROVIDERS
        # OFFERING THE SAME PRODUCT NAMES WITH SAME PRODUCT TYPES,
        # BUT DIFFERENT COVERAGE TYPES
        # provider 1
        ("Routine Medical Checkups", "Health", provider_1),
        ("Whole Life Insurance", "Life", provider_1),
        ("Homeowners Insurance", "Home", provider_1),
        ("Travel Medical Emergency Insurance", "Travel", provider_1),
        ("Smartphone Protection", "Gadget", provider_1),
        ("Accidental Injury Insurance", "Personal_Accident", provider_1),
        ("Comprehensive Auto Insurance", "Auto", provider_1),
        # provider 2
        ("Smartphone Protection", "Gadget", provider_2),
        ("Term Life Insurance", "Life", provider_2),
        ("Comprehensive Auto Insurance", "Auto", provider_2),
        ("Student Health Insurance", "Student_Protection", provider_2),
        ("Accidental Death Insurance", "Personal_Accident", provider_2),
        ("Travel Medical Emergency Insurance", "Travel", provider_2),
        ("Homeowners Insurance", "Home", provider_2),
        ("Routine Medical Checkups", "Health", provider_2),
        ("Trip Cancellation Insurance", "Travel", provider_2),
        # provider 3
        ("Accidental Death Insurance", "Personal_Accident", provider_3),
        ("Travel Medical Emergency Insurance", "Travel", provider_3),
        ("Homeowners Insurance", "Home", provider_3),
        ("Routine Medical Checkups", "Health", provider_3),
        # provider 4
        ("Term Life Insurance", "Life", provider_4),
        ("Smartphone Protection", "Gadget", provider_4),
        ("Comprehensive Auto Insurance", "Auto", provider_4),
        ("Student Health Insurance", "Student_Protection", provider_4),
        ("Homeowners Insurance", "Home", provider_4),
    ]

    for product_name, product_type, provider in products:
        product = Product.objects.create(
            provider=provider, name=product_name, product_type=product_type
        )
        products_store[product_name] = product

    valid_tiers = {
        "Basic": 5000,
        "Premium": 30000,
    }

    coverage_data = [
        {
            "coverage_name": "Accidental Damage",
            "coverage_limit": 50000,
            "coverage_type": Coverage.CoverageType.DAMAGES,
        },
        {
            "coverage_name": "Theft",
            "coverage_limit": 100000,
            "coverage_type": Coverage.CoverageType.LIABILITY,
        },
    ]

    # THEN WE SHOULD CREATE THE CORRESPONDING TIERS AND COVERAGES
    created_tiers = []
    created_coverages = []

    for coverage in coverage_data:
        coverage_instance = Coverage.objects.create(
            coverage_name=coverage["coverage_name"],
            coverage_limit=coverage["coverage_limit"],
            coverage_type=coverage["coverage_type"],
        )
        created_coverages.append(coverage_instance)

    for product in products_store.values():
        for coverage in created_coverages:
            # we wold get a value list from all the products in there
            for tier_name, base_premium in valid_tiers.items():
                tier = ProductTier.objects.create(
                    product=product, tier_name=tier_name, base_premium=base_premium
                )
                tier.coverages.add(coverage)
                created_tiers.append(tier)

    return {
        "provider_1": provider_1,
        "provider_2": provider_2,
        "provider_3": provider_3,
        "provider_4": provider_4,
        "products": products_store,
        "tiers": created_tiers,
        "coverages": created_coverages,
    }


@pytest.mark.django_db
class TestQuoteRequestView:
    def test_filter_products_by_type(self, setup_data):
        products = Product.objects.filter(
            provider__name__in=[setup_data["provider_1"].name], product_type="Gadget"
        )

        assert products.count() == 1
        assert products.first().name == "Smartphone Protection"

    def test_tier_and_coverage(self, setup_data):
        product_1 = setup_data["products"]["Routine Medical Checkups"]
        tiers = product_1.tiers.all()
        assert tiers.count() == 2

        basic_tier = tiers.get(tier_name="Basic")
        coverages = basic_tier.coverages.all()

        assert coverages.count() == 2
        assert any(
            coverage.coverage_name == "Accidental Damage" for coverage in coverages
        )
        assert any(coverage.coverage_name == "Theft" for coverage in coverages)

    def test_quote_creation(self, setup_data):
        with transaction.atomic():
            premium = Price.objects.create(
                amount=setup_data["tiers"][0].base_premium,
                description=f"{setup_data['products']['Routine Medical Checkups'].name} - {setup_data['tiers'][0].tier_name} Premium",
            )

            quote = Quote.objects.create(
                product=setup_data["products"]["Routine Medical Checkups"],
                premium=premium,
                base_price=setup_data["tiers"][0].base_premium,
                additional_metadata={
                    "tier_name": setup_data["tiers"][0].tier_name,
                    "coverage_details": [
                        {
                            "coverage_name": setup_data["coverages"][0].coverage_name,
                            "coverage_description": setup_data["coverages"][
                                0
                            ].description,
                            "coverage_type": setup_data["coverages"][0].coverage_type,
                            "coverage_limit": str(
                                setup_data["coverages"][0].coverage_limit
                            ),
                        }
                    ],
                    "exclusions": setup_data["tiers"][0].exclusions or "",
                    "benefits": setup_data["tiers"][0].benefits or "",
                    "product_type": setup_data["products"][
                        "Routine Medical Checkups"
                    ].product_type,
                    "available_tiers": [
                        setup_data["tiers"][0].tier_name,
                        setup_data["tiers"][1].tier_name,
                    ],  # All addons available for this product
                },
            )

            assert quote.base_price == 5000
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
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 200

        response_data = response.json()
        assert "data" in response_data
        assert len(response_data["data"]) > 0

    @pytest.mark.parametrize(
        "product_type,expected_product_names",
        [
            ("Gadget", ["Smartphone Protection"]),
            ("Home", ["Homeowners Insurance"]),
            (
                "Travel",
                ["Travel Medical Emergency Insurance", "Trip Cancellation Insurance"],
            ),
            (
                "Personal_Accident",
                ["Accidental Injury Insurance", "Accidental Death Insurance"],
            ),
            ("Student_Protection", ["Student Health Insurance"]),
            ("Auto", ["Comprehensive Auto Insurance"]),
            ("Life", ["Term Life Insurance"]),
        ],
    )
    def test_product_type_filtering(
        self, setup_data, product_type, expected_product_names
    ):
        products = Product.objects.filter(product_type=product_type).values_list(
            "name", flat=True
        )
        assert sorted(products) == sorted(
            expected_product_names
        ), f"Expected products for {product_type} did not match."
