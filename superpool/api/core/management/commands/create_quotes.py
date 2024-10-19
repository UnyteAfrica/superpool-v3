import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.catalog.models import Price, Product, Quote
from core.providers.models import Provider as InsuranceProvider


class Command(BaseCommand):
    help = "Create sample quotes for products"

    def handle(self, *args, **kwargs):
        provider, _ = InsuranceProvider.objects.get_or_create(
            name="AIICO",
            support_email="support@aiioexample.com",
            support_phone="08012345678",
        )

        products_data = [
            {
                "name": "Health Insurance",
                "product_type": "Health",
                "description": "Health",
                "base_price": 1000.0,
                "premium_amount": 1000.0,
            },
            {
                "name": "Auto Insurance",
                "product_type": "Auto",
                "description": "Auto",
                "base_price": 2000.0,
                "premium_amount": 1500.0,
            },
            {
                "name": "Travel Insurance",
                "product_type": "Travel",
                "description": "Travel",
                "base_price": 3000.0,
                "premium_amount": 2000.0,
            },
            {
                "name": "Home Insurance",
                "product_type": "Home",
                "description": "Home",
                "base_price": 4000.0,
                "premium_amount": 2500.0,
            },
            {
                "name": "Gadget Insurance",
                "product_type": "Gadget",
                "description": "Gadget",
                "base_price": 5000.0,
                "premium_amount": 500.0,
            },
        ]

        for product_data in products_data:
            product, _ = Product.objects.get_or_create(
                name=product_data["name"],
                product_type=product_data["product_type"],
                description=product_data["description"],
                provider=provider,
            )

            price, _ = Price.objects.get_or_create(
                amount=product_data["premium_amount"],
                description=f"Standard {product_data['product_type'].lower()} insurance premium",
            )

            Quote.objects.get_or_create(
                product=product,
                # quote_code=f"Q{product_data['product_type'][0]}001",
                defaults={
                    "base_price": product_data["base_price"],
                    "premium": price,
                    "expires_in": timezone.now() + timedelta(days=30),
                    "status": random.choice(["pending", "accepted", "declined"]),
                },
            )

        print("Successfully created all quotes")
