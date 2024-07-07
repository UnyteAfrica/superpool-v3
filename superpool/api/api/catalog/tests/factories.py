import factory
from core.catalog.models import Policy, Product
from faker import Faker


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product


class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    name = factory.Faker("name")
    product = factory.SubFactory(ProductFactory)
    price = factory.Faker("random_price")
    description = factory.Faker("text")
