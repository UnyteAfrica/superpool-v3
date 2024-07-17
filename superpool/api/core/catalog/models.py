import typing
import uuid

from core.merchants.models import Merchant
from core.mixins import TimestampMixin, TrashableModelMixin
from core.providers.models import Provider as Partner
from core.user.models import Customer
from django.db import models
from django_stubs_ext.db.models import TypedModelMeta


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

    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        help_text="Unique identifier for the package",
        default=uuid.uuid4,
    )
    provider: models.ForeignKey = models.ForeignKey(
        Partner,
        on_delete=models.PROTECT,
        help_text="Insurance provider offering the package",
    )
    name: models.CharField = models.CharField(
        max_length=100,
        help_text="Name of the package offered by the insurance provider",
    )
    description: models.TextField = models.TextField(
        help_text="Description of the package", null=True, blank=True
    )
    product_type: models.CharField = models.CharField(
        max_length=15,
        choices=ProductType.choices,
        help_text="Type of insurance package",
    )
    coverage_details: models.TextField = models.TextField(
        help_text="Detailed breakdown of what's covered", null=True, blank=True
    )
    base_price: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base price of the package prior to any modifications or adjustments",
    )  # TODO: We want to add a proper currency field here, we would probably need to create a custom field for this or use a  third-party package
    is_live = models.BooleanField(
        default=True, help_text="Indicates if the package is live"
    )

    def __str__(self) -> str:
        return f"Product: {self.name}, Provider: {self.provider.name}"

    def delete(self, *args: dict, **kwargs: dict) -> None:
        """
        Override the delete method to trash the model instance
        """
        self.trash()

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["product_type"]),
        ]


class Policy(TimestampMixin, TrashableModelMixin, models.Model):
    """
    Insurance policy purchased by a user
    """

    policy_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text="Unique identifier for the policy",
    )
    product: models.ForeignKey = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Insurance package purchased by the user",
    )
    policy_holder: models.ForeignKey = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        help_text="User who purchased the policy",
    )
    effective_from: models.DateField = models.DateField(
        help_text="Date the policy was purchased"
    )
    effective_through: models.DateField = models.DateField(
        help_text="Date the policy expires"
    )
    premium: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount paid for the policy",
    )
    coverage: models.ForeignKey = models.ForeignKey(
        "core.Coverage",
        on_delete=models.CASCADE,
        help_text="Coverage details for the policy",
    )
    merchant_id: models.ForeignKey = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        help_text="Merchant who sold the policy",
    )
    provider_id: models.ForeignKey = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        help_text="Insurance provider for the policy",
    )
    renewable = models.BooleanField(
        default=False, help_text="Indicates if the policy is renewable"
    )
    inspection_required = models.BooleanField(
        default=False,
        help_text="Indicates if an inspection is required before the policy can be purchased",
    )
    cerfication_required = models.BooleanField(
        default=False,
        help_text="Indicates if any certifications are required before the policy can be purchased",
    )

    def __str__(self) -> str:
        return f"Policy: {self.policy_id} bought by User: {self.policy_holder.username}"

    def delete(self, *args: dict, **kwargs: dict) -> None:
        """
        Override the delete method to trash the model instance
        """
        self.trash()

    class Meta:
        indexes = [
            models.Index(
                fields=["effective_from", "effective_through", "policy_id", "premium"]
            ),
            models.Index(fields=["policy_holder"]),
            models.Index(fields=["provider_id"]),
        ]


class Quote(models.Model):
    id = models.CharField(max_length=80, primary_key=True, unique=True, editable=False)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "quote"
        verbose_name_plural = "quotes"
