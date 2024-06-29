import factory
from core.merchants.models import Merchant
from faker import Faker

faker = Faker()


class MerchantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Merchant

    name = faker.company()
    short_code = faker.slug()
    business_email = faker.company_email()
    support_email = faker.company_email()
