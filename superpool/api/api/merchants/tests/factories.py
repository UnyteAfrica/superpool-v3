import factory
from core.merchants.models import Merchant
from faker import Faker

fake = Faker()


class MerchantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Merchant

    name = fake.company()
    short_code = factory.Sequence(lambda n: f"MER-{n:03d}")
    business_email = fake.email()
    support_email = fake.email()
    is_active = True
    address = fake.address()
    api_key = fake.uuid4()
    kyc_verified = True
