import uuid
from decimal import Decimal

import factory
from faker import Faker

from api.merchants.tests.factories import MerchantFactory
from core.catalog.models import Policy, Price, Product, Quote
from core.providers.models import Provider as Partner
from core.user.models import Customer

fake = Faker()


def generate_decimal():
    value = Decimal(f"{fake.pydecimal(right_digits=2, positive=True)}")
    # limit to 2 decimal places
    return value.quantize(Decimal("0.01"))


class PartnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partner
        django_get_or_create = ("name",)

    name = fake.company()
    support_email = fake.company_email()
    support_phone = fake.phone_number()


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = fake.company()  # Use a company name for product name
    description = fake.paragraph()
    product_type = factory.Iterator(
        ["Life", "Health", "Auto", "Gadget", "Travel", "Home", "Cargo", "Other"]
    )
    provider = factory.SubFactory(PartnerFactory)


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    id = factory.LazyFunction(uuid.uuid4)
    first_name = factory.LazyAttribute(lambda _: fake.first_name()[:40])
    middle_name = factory.LazyAttribute(lambda _: fake.first_name()[:40])
    last_name = factory.LazyAttribute(lambda _: fake.last_name()[:40])
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com"
    )
    address = factory.LazyAttribute(lambda _: fake.address()[:200])
    kyc_verified = factory.Faker("boolean", chance_of_getting_true=50)
    dob = factory.Faker("date_of_birth", minimum_age=18, maximum_age=90)
    phone_number = factory.LazyAttribute(lambda _: fake.phone_number()[3:20])
    gender = factory.Iterator(["M", "F"])
    verification_type = factory.LazyAttribute(
        lambda _: fake.random.choice(["BVN", "NIN", "Passport"])[:20]
    )
    verification_id = factory.LazyAttribute(lambda _: str(uuid.uuid4())[0:20])
    merchant = factory.SubFactory(MerchantFactory)


class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    product = factory.SubFactory(ProductFactory)
    policy_holder = factory.SubFactory(CustomerFactory)
    effective_from = fake.date()
    effective_through = fake.date()
    premium = fake.random_number(digits=3)
    merchant_id = factory.SubFactory(MerchantFactory)
    provider_id = factory.SubFactory(PartnerFactory)


class PriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Price

    amount = factory.LazyFunction(generate_decimal)
    description = fake.sentence()
    commision = factory.LazyFunction(generate_decimal)
    discount_amount = factory.LazyFunction(generate_decimal)
    surcharges = factory.LazyFunction(generate_decimal)


class QuoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quote
        # handles the create or retrieve instance that causes dupicate key errors
        django_get_or_create = ("quote_code",)

    base_price = fake.random_number(digits=3)
    product = factory.SubFactory(ProductFactory)
    premium = factory.SubFactory(PriceFactory)
    expires_in = fake.date_time_this_year()
    status = factory.Iterator(["pending", "accepted", "declined"])
