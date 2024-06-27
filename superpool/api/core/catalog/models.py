import typing

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

if typing.TYPE_CHECKING:
    from core.models import Coverage  # noqa: F401
    from core.models import TimestampMixin, TrashableModelMixin  # noqa: F401
    from core.providers.models import Provider as Partner  # noqa: F401
    from django.db import models


class Product(TimestampMixin, TrashableModelMixin, models.Model):
    """
    Packages offered by an insurance partner

    E.g Life Insurance, MicroInsurance, General Insurance, etc
    """

    class ProductType(models.TextChoices):
        """
        Choices for the type of insurance package
        """

        LIFE = "Life", "Life Insurance"
        HEALTH = "Health", "Health Insurance"
        AUTO = "Auto", "Auto Insurance"
        GADGET = "Gadget", "Gadget Insurance"
        TRAVEL = "Travel", "Travel Insurance"

    policy_id: models.BigAutoField = models.BigAutoField(
        primary_key=True, help_text="Unique identifier for the package"
    )
    provider: models.ForeignKey = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        help_text="Insurance provider offering the package",
    )
    product_name: models.CharField = models.CharField(
        max_length=100,
        help_text="Name of the package offered by the insurance provider",
    )
    description: models.TextField = models.TextField(
        help_text="Description of the package"
    )
    product_type: models.CharField = models.CharField(
        max_length=15,
        choices=ProductType.choices,
        help_text="Type of insurance package",
    )
    coverage_details: models.TextField = models.TextField(
        help_text="Detailed breakdown of what's covered"
    )
    base_price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base price of the package prior to any modifications or adjustments",
    )  # TODO: We want to add a proper currency field here, we would probably need to create a custom field for this or use a  third-party package

    def __str__(self) -> str:
        return f"Product: {self.product_name}, Provider: {self.provider.name}"

    def delete(self, *args: dict, **kwargs: dict) -> None:
        """
        Override the delete method to trash the model instance
        """
        self.trash()
