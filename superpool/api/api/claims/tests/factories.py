from factory.django import DjangoModelFactory
from core.claims.models import Claim
from faker import Faker

fake = Faker()


class ClaimFactory(DjangoModelFactory):
    class Meta:
        model = Claim
