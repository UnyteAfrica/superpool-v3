import factory
from decimal import Decimal
from api.merchants.tests.factories import MerchantFactory
from core.catalog.models import Policy, Product, Quote, Price
from core.merchants.models import Merchant
from core.providers.models import Provider as Partner
from core.user.models import Customer
from faker import Faker

fake = Faker()


def generate_decimal():
    value = Decimal(f"{fake.pydecimal(right_digits=2, positive=True)}")
    # limit to 2 decimal places
    return value.quantize(Decimal("0.01"))


class PartnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partner

    name = fake.company()
    support_email = fake.company_email()
    support_phone = fake.phone_number()


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = fake.company()  # Use a company name for product name
    product_type = factory.Iterator(["Life", "Health", "Auto", "Gadget", "Travel"])
    coverage_details = fake.paragraph()  # Use a paragraph for coverage details
    base_price = fake.random_number(digits=5)  # Adjust as needed
    provider = factory.SubFactory(PartnerFactory)


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    first_name = fake.first_name()
    middle_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email()
    address = fake.address()
    kyc_verified = fake.boolean()
    dob = fake.date_of_birth()
    phone_number = fake.phone_number()
    gender = factory.Iterator(["M", "F"])
    verification_type = fake.word()
    verification_id = fake.uuid4()


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
