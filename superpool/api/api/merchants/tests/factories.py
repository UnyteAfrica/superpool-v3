from uuid import uuid4

import factory
from faker import Faker

from core.merchants.models import Merchant
from core.user.models import Customer

fake = Faker()


class MerchantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Merchant

    name = fake.company()
    # short_code = factory.Sequence(lambda n: f"MER-{n:03d}")
    business_email = fake.email()
    support_email = fake.email()
    is_active = True
    address = fake.address()
    # api_key = fake.uuid4()
    kyc_verified = True
    tenant_id = uuid4()


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    id = fake.uuid4()
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email()
    address = fake.address()
    merchant = factory.SubFactory(MerchantFactory)
