import typing
import uuid
from datetime import datetime, timedelta

from core.merchants.models import Merchant
from core.mixins import TimestampMixin, TrashableModelMixin
from core.providers.models import Provider as Partner
from core.user.models import Customer
from core.utils import generate_id
from django.db import models
from django.utils.translation import gettext_lazy as _
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
        on_delete=models.CASCADE,
        help_text="Insurance provider offering the package",
    )
    name: models.CharField = models.CharField(
        max_length=255,
        help_text="Name of the package offered by the insurance provider",
    )
    description: models.TextField = models.TextField(
        help_text="Description of the package", null=True, blank=True
    )
    product_type: models.CharField = models.CharField(
        max_length=255,
        choices=ProductType.choices,
        help_text="Type of insurance package",
    )
    coverage_details: models.TextField = models.TextField(
        help_text="Detailed breakdown of what's covered", null=True, blank=True
    )
    is_live = models.BooleanField(
        default=True, help_text="Indicates if the package is live"
    )

    def __str__(self) -> str:
        return f"{self.product_type}: {self.name} - {self.provider.name}"

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

    POLICY_STATUS = (("accepted", _("Accepted")), ("cancelled", _("Cancelled")))
    """ Describes the current status of the policy """

    policy_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text="Unique identifier for the policy",
    )
    policy_number = models.CharField(
        null=True,
        blank=True,
        unique=True,
        help_text="Policy Refrence Number assigned by the insurer e.g GI86585700-1, AXA2024727-2, LEAD18002-42, etc",
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
    renewal_date = models.DateTimeField(
        help_text="Date when this insurance policy is due for renewal",
        null=True,
        blank=True,
    )
    inspection_required = models.BooleanField(
        default=False,
        help_text="Indicates if an inspection is required before the policy can be purchased",
    )
    cerfication_required = models.BooleanField(
        default=False,
        help_text="Indicates if any certifications are required before the policy can be purchased",
    )
    status = models.CharField(
        max_length=20,
        choices=POLICY_STATUS,
        default="active",
        help_text="Current status of the policy",
    )
    cancellation_initiator = models.CharField(
        max_length=50,
        help_text="Who requested for cancellation of this policy?",
        null=True,
        blank=True,
    )
    cancellation_reason = models.TextField(
        null=True, blank=True, help_text="Reason for policy cancellation"
    )
    cancellation_date = models.DateTimeField(
        null=True, blank=True, help_text="Date when the policy was cancelled"
    )

    def __str__(self) -> str:
        return f"{self.policy_id} bought by User: {self.policy_holder.username}"

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


class Price(models.Model):
    """
    Defines the pricing structure for an object e.g a product
    """

    value = models.DecimalField(max_digits=10, decimal_places=2)
    comission = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    surcharges = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )


class Quote(models.Model):
    """
    Represents an insurance quote for a policy
    """

    QUOTE_STATUS = (
        ("pending", "pending"),
        ("accepted", "accepted"),
        ("declined", "declined"),
    )

    # id = models.CharField(max_length=80, primary_key=True, unique=True, editable=False)
    quote_code = models.CharField(
        _("Quote Code"),
        primary_key=True,
        unique=True,
        editable=False,
        help_text="Assigned identifier for managing quote objects",
    )
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price of quote excluding  discount"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Insurance Product/Service covered by the quote",
    )
    premium = models.ForeignKey(
        Price,
        on_delete=models.CASCADE,
        help_text="The calculated premium for the quote",
    )
    expires_in = models.DateTimeField(
        auto_now_add=True,
        help_text="The expiry date of the quote.",
    )
    status = models.CharField(max_length=20, choices=QUOTE_STATUS, default="pending")

    class Meta:
        verbose_name = "quote"
        verbose_name_plural = "quotes"

    def save(self, *args, **kwargs):
        if not self.quote_code:
            quote_code = generate_id(self.__class__)
            self.quote_code = quote_code
        # Set quote expiry by default to 1 Month
        if not self.expires_in:
            self.expires_in = datetime.now() + timedelta(days=30)
        return super().save(*args, **kwargs)
