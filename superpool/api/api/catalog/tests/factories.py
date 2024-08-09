import factory
from api.merchants.tests.factories import MerchantFactory
from core.catalog.models import Policy, Product
from core.merchants.models import Merchant
from core.providers.models import Provider as Partner
from core.user.models import Customer
from faker import Faker

fake = Faker()


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

    amount = fake.random_number(digits=3)
    description = fake.sentence()
    comssion = fake.random_number(digits=3)
    discount = fake.random_number(digits=3)
    surcharge = fake.random_number(digits=3)


class QuoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quote

    base_price = fake.random_number(digits=3)
    product = factory.SubFactory(ProductFactory)
    premium = fake.random_number(digits=3)
    expires_in = fake.date_time_this_year()
    status = factory.Iterator(["pending", "accepted", "declined"])
