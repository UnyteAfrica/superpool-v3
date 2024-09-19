"""
This is module is used to populate the database with the initial data.

With this, we can have some data to work with when we start the application.

Therefore, having actual testing experience
"""

from pprint import pprint

from django.core.management.base import BaseCommand
from faker import Faker

from core.catalog.models import Product
from core.management.fixtures.providers import InsuranceProductProvider
from core.providers.models import Provider as Partner


class Command(BaseCommand):
    help = "Populate the database with initial data"

    def handle(self, *args, **kwargs):
        fake = Faker()
        insurance_provider = InsuranceProductProvider
        fake.add_provider(insurance_provider)

        # Create 10 Merchants
        # for _ in range(10):
        # try:
        #     Merchant.objects.create(
        #         name=fake.company(),
        #         business_email=fake.company_email(),
        #         support_email=fake.email(),
        #         tax_identification_number=fake.random_int(max=15),
        #         registration_number=fake.random_int(max=15),
        #         address=fake.address(),
        #     )
        # except Exception as e:
        #     pprint(f"Error: {e}")
        #     pass

        # Create 10 Insurance Providers
        # for _ in range(10):
        #     Partner.objects.create(
        #         name=fake.company(),
        #         support_email=fake.company_email(),
        #         support_phone=fake.phone_number(),
        #     )

        # # Create 100 Customers
        # for _ in range(100):
        # try:
        #     Customer.objects.create(
        #         first_name=fake.first_name(),
        #         middle_name=fake.middle_name(),
        #         last_name=fake.last_name(),
        #         gender=fake.random_element(elements=("M", "F")),
        #         dob=fake.date_of_birth(),
        #         email=fake.email(),
        #         phone_number=fake.phone_number(),
        #         address=fake.address(),
        #         kyc_verified=fake.boolean(),
        #     )
        # except Exception as e:
        #     pprint(f"Error: {e}")
        #     pass

        # # Create 5 Products of 6 ditinct insurance types

        for _ in range(10):
            try:
                Product.objects.create(
                    name=fake.random_company_product(),
                    description=fake.sentence(),
                    product_type=fake.random_element(
                        elements=(
                            "Auto",
                            # "CreditLife",
                            "Life",
                            "Travel",
                            "Health",
                            "Gadget",
                        )
                    ),
                    provider=fake.random_element(Partner.objects.all()),
                )
            except Exception as e:
                pprint(f"Error: {e}")
                pass

        # # Create 20 Policies
        # for _ in range(20):
        #     try:
        #         Policy.objects.create(
        #             policy_id=uuid.uuid4(),
        #             policy_number=fake.bothify(text="POL######"),
        #             product=Product.objects.order_by("?").first(),
        #             product_type=fake.random_element(
        #                 elements=(
        #                     "Auto",
        #                     "CreditLife",
        #                     "Home",
        #                     "Travel",
        #                     "Health",
        #                     "Gadget",
        #                 )
        #             ),
        #             customer=Customer.objects.order_by("?").first(),
        #             merchant=Merchant.objects.order_by("?").first(),
        #             address=Address.objects.order_by("?").first(),
        #             start_date=fake.date_this_decade(),
        #             end_date=fake.date_this_decade(end_date="+1y"),
        #             premium=fake.random_number(digits=5),
        #             status=fake.random_element(
        #                 elements=("active", "cancelled", "expired")
        #             ),
        #         )
        #     except Exception as e:
        #         pprint(f"Error: {e}")
        #         pass
        #
        # # Create 20 Quotess
        # for _ in range(20):
        #     try:
        #         Quote.objects.create(
        #             quote_code=fake.uuid4(),
        #             product=Product.objects.order_by("?").first(),
        #             customer=Customer.objects.order_by("?").first(),
        #             merchant=Merchant.objects.order_by("?").first(),
        #             price=fake.random_number(digits=5),
        #             status=fake.random_element(
        #                 elements=("pending", "accepted", "rejected")
        #             ),
        #         )
        #     except Exception as e:
        #         pprint(f"Error: {e}")
        #         pass
        #
        # # Create 20 Addresses
        # for _ in range(20):
        #     try:
        #         Address.objects.create(
        #             street=fake.street_address(),
        #             city=fake.city(),
        #             state=fake.state(),
        #             country=fake.country(),
        #         )
        #     except Exception as e:
        #         pprint(f"Error: {e}")
        #         pass
        #
        # # Create 20 Coverages
        # for _ in range(20):
        #     try:
        #         Coverage.objects.create(
        #             coverage_name=fake.random_element(
        #                 elements=("Liability", "Comprehensive", "Collision")
        #             ),
        #             coverage_id=uuid.uuid4(),
        #             coverage_limit=fake.random_number(digits=5),
        #             description=fake.sentence(),
        #             product_id=Product.objects.order_by("?").first(),
        #         )
        #     except Exception as e:
        #         pprint(f"Error: {e}")
        #         pass

        pprint("Database populated successfully")
