from factory.django import DjangoModelFactory
from faker import Faker

from core.claims.models import Claim

fake = Faker()


class ClaimFactory(DjangoModelFactory):
    class Meta:
        model = Claim
