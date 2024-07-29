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
