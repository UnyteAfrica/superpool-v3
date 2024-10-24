import uuid

import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from faker import Faker

from api.catalog.tests.factories import CustomerFactory
from api.catalog.tests.factories import PartnerFactory as ProviderFactory
from api.catalog.tests.factories import PolicyFactory, ProductFactory
from core.claims.models import Claim

fake = Faker()


class ClaimFactory(DjangoModelFactory):
    id = factory.LazyFunction(uuid.uuid4)
    claim_number = factory.LazyAttribute(
        lambda _: f"CLM{fake.random_number(digits=6, fix_len=True)}"
    )
    claim_date = factory.LazyFunction(fake.date_this_year)
    claim_type = factory.Faker(
        "word",
        ext_word_list=[
            "auto",
            "health",
            "life",
            "cargo",
            "gadget",
            "petcare",
            "others",
        ],
    )
    incident_date = factory.LazyFunction(fake.date_this_year)
    incident_description = factory.Faker("sentence", nb_words=255)
    # amount = factory.LazyFunction(
    #     lambda: Decimal(fake.pyfloat(left_digits=4, right_digits=2, positive=True))
    # )
    amount = factory.LazyFunction(
        lambda: fake.pydecimal(left_digits=4, right_digits=2, positive=True)
    )
    # estimated_loss = factory.LazyFunction(
    #     lambda: Decimal(fake.pyfloat(left_digits=4, right_digits=2, positive=True))
    # )
    # payout_amount = factory.LazyFunction(
    #     lambda: Decimal(fake.pyfloat(left_digits=4, right_digits=2, positive=True))
    # )
    estimated_loss = factory.LazyFunction(
        lambda: fake.pydecimal(left_digits=4, right_digits=2, positive=True)
    )
    payout_amount = factory.LazyFunction(
        lambda: fake.pydecimal(left_digits=4, right_digits=2, positive=True)
    )
    status = factory.Iterator([choice[0] for choice in Claim.CLAIM_STATUS])

    policy = factory.SubFactory(PolicyFactory)
    provider = factory.SubFactory(ProviderFactory)
    product = factory.SubFactory(ProductFactory)

    claimant_type = factory.Iterator(
        [choice[0] for choice in Claim.ClaimantType.choices]
    )

    # claimant_object_id = factory.LazyAttribute(lambda o: Customer.objects.first().id)
    claimant_object_id = factory.LazyAttribute(lambda o: CustomerFactory().id)

    notes = factory.Faker("paragraph", nb_sentences=5)

    @factory.lazy_attribute
    def claimant_content_type(self):
        return ContentType.objects.get_for_model(CustomerFactory._meta.model)

    @factory.post_generation
    def documents(self, create, extracted, **kwargs):
        if not create:
            # do nothing but build
            return

        if extracted:
            # means we pass in a list of documents to add to the claim, add them
            for document in extracted:
                self.documents.add(document)

    class Meta:
        model = Claim
        django_get_or_create = ["claim_number"]
