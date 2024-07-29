"""
This module serves as a patch to resolve a bug in the faker library.
The bug is that the company provider does not have a method to generate a random company product.

Root Cause Analysis: the `random_company_product` method provided by the Provider class is not implemented in the company provider.
Nor does it provide a way to generate a random company product resulting in an Error from the `Generator`.

Solution: I have created a custom provider called `InsuranceProductProvider` that inherits from the `Provider` class. It
provides the concrete implementation of the `random_company_product` method to generate a random company product,
and more specifically, tailored to our company need, an insurance product.

Date created: 2024-07-29 16:00:00
"""

from faker import Faker
from faker.providers.company import Provider

fake = Faker()


class InsuranceProductProvider(Provider):
    def random_company_product(self):
        product_plans = (
            "Smart",
            "Mini",
            "Plus",
            "Premium",
            "Basic",
            "Standard",
        )
        product_types = (
            "Car",
            "Home",
            "Travel",
            "Health",
            "Gadget",
            "Life",
        )
        defacto = ("Insurance",)

        # generate product name
        product_name = (
            self.random_element(product_plans)
            + " "
            + self.generator.word().title()
            + " "
            + self.random_element(product_types)
            + " "
            + defacto[0]
        )
        print(product_name)
        return product_name


# register my custom insurance provider
fake.add_provider(InsuranceProductProvider)
