"""
This is module is used to populate the database with the initial data.

With this, we can have some data to work with when we start the application.

Therefore, having actual testing experience
"""

import uuid
from pprint import pprint

from core.catalog.models import Policy, Product, Quote
from core.merchants.models import Merchant
from core.models import Address, Coverage
from core.providers.models import Provider as Partner
from core.user.models import Customer, User
from django.core.management.base import BaseCommand
from faker import Faker


class Command(BaseCommand):
    help = "Populate the database with initial data"

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create 10 Merchants
        for _ in range(10):
            Merchant.objects.create(
                name=fake.company(),
                business_email=fake.company_email(),
                support_email=fake.email(),
                tax_identification_number=fake.random_int(),
                registration_number=fake.random_int(),
                address=fake.address(),
                api_key=fake.uuid4(),
            )

        # Create 10 Insurance Providers
        for _ in range(10):
            Partner.objects.create(
                name=fake.company(),
                short_code=fake.random_company_acronym(),
                tax_identification_number=fake.random_int(),
                support_email=fake.company_email(),
                support_phone=fake.phone_number(),
            )

        # Create 100 Customers
        for _ in range(100):
            Customer.objects.create(
                first_name=fake.first_name(),
                middle_name=fake.middle_name(),
                last_name=fake.last_name(),
                gender=fake.random_element(elements=("M", "F")),
                dob=fake.date_of_birth(),
                email=fake.email(),
                phone_number=fake.phone_number(),
                address=fake.address(),
                kyc_verified=fake.boolean(),
            )

        # Create 5 Products of 6 ditinct insurance types
        for _ in range(5):
            Product.objects.create(
                name=fake.random_company_product(),
                description=fake.sentence(),
                product_type=fake.random_element(
                    elements=(
                        "Auto",
                        "CreditLife",
                        "Home",
                        "Travel",
                        "Health",
                        "Gadget",
                    )
                ),
                provider=fake.random_element(Partner.objects.all()),
            )

        # Create 20 Policies
        for _ in range(20):
            Policy.objects.create(
                policy_id=uuid.uuid4(),
                policy_number=fake.bothify(text="POL######"),
                product=Product.objects.order_by("?").first(),
                product_type=fake.random_element(
                    elements=(
                        "Auto",
                        "CreditLife",
                        "Home",
                        "Travel",
                        "Health",
                        "Gadget",
                    )
                ),
                customer=Customer.objects.order_by("?").first(),
                merchant=Merchant.objects.order_by("?").first(),
                address=Address.objects.order_by("?").first(),
                start_date=fake.date_this_decade(),
                end_date=fake.date_this_decade(end_date="+1y"),
                premium=fake.random_number(digits=5),
                status=fake.random_element(elements=("active", "cancelled", "expired")),
            )

        # Create 20 Quotess
        for _ in range(20):
            Quote.objects.create(
                quote_code=fake.uuid4(),
                product=Product.objects.order_by("?").first(),
                customer=Customer.objects.order_by("?").first(),
                merchant=Merchant.objects.order_by("?").first(),
                price=fake.random_number(digits=5),
                status=fake.random_element(
                    elements=("pending", "accepted", "rejected")
                ),
            )

        # Create 20 Addresses
        for _ in range(20):
            Address.objects.create(
                street=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                country=fake.country(),
            )

        # Create 20 Coverages
        for _ in range(20):
            Coverage.objects.create(
                coverage_name=fake.random_element(
                    elements=("Liability", "Comprehensive", "Collision")
                ),
                coverage_id=uuid.uuid4(),
                coverage_limit=fake.random_number(digits=5),
                description=fake.sentence(),
                product_id=Product.objects.order_by("?").first(),
            )

        pprint("Database populated successfully")
