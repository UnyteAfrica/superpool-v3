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
from django.utils import timezone


class ProductTier(models.Model):
    """
    Represents the tier of a insurance product
    """

    class TierType(models.TextChoices):
        """
        Choices for the type of insurance package
        """

        BASIC = "Basic", "Basic Insurance"
        ADVANCED = "Advanced", "Advanced"
        STANDARD = "Standard", "Standard Insurance"
        PREMIUM = "Premium", "Premium"
        BRONZE = "Bronze", "Bronze"
        SILVER = "Silver", "Silver"
        OTHER = "Other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        help_text="Insurance package the tier belongs to",
        related_name="tiers",
        related_query_name="tier",
    )
    tier_name = models.CharField(
        max_length=255, help_text="Name of the product tier", choices=TierType.choices
    )
    description = models.TextField(
        help_text="Optional - description of the product tier", null=True, blank=True
    )
    base_preimum = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Base price for the product tier"
    )
    pricing = models.ForeignKey(
        "Price",
        on_delete=models.SET_NULL,
        help_text="Pricing for the product tier",
        null=True,
        blank=True,
    )
    coverages = models.ManyToManyField(
        "core.Coverage",
        blank=True,
        help_text="Detailed breakdown of what's covered",
    )

    benefits = models.TextField(
        _("Benefits"),
        help_text=_("Specific benefits included in the coverage"),
        blank=True,
        null=True,
    )
    exclusions = models.TextField(
        _("Exclusions"),
        help_text=_("Exclusions or limitations of the coverage"),
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return f"{self.product.name} - {self.tier_name}"

    class Meta:
        unique_together = ["product", "tier_name"]


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
        HOME = "Home", "Home Insurance"
        STUDENT_PROTECTION = "Student_Protection", "Student Protection"
        PERSONAL_ACCIDENT = "Personal_Accident", "Personal Accident Insurance"

    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        help_text="Unique identifier for the package",
        default=uuid.uuid4,
        editable=False,
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
    coverages = models.ManyToManyField(
        "core.Coverage",
        blank=True,
        help_text="Detailed breakdown of what's covered",
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


class Beneficiary(models.Model):
    """
    Represents a beneficiary of an insurance policy other than the policy holder
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40, blank=True, null=True)
    last_name = models.CharField(max_length=40)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=15)
    address = models.TextField(null=True)
    relationship = models.CharField(
        max_length=40, help_text="Relationship to the policy holder"
    )
    date_of_birth = models.DateField(
        help_text="Date of birth of the beneficiary",
        null=True,
    )


class Policy(TimestampMixin, TrashableModelMixin, models.Model):
    """
    Insurance policy purchased by a user
    """

    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    ACTIVE = "active"

    POLICY_STATUS = (
        (ACCEPTED, "Accepted"),
        (CANCELLED, "Cancelled"),
        (ACTIVE, "Active"),
    )
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
        related_name="policies",
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
        on_delete=models.SET_NULL,
        help_text="Coverage details for the policy",
        null=True,
    )
    merchant: models.ForeignKey = models.ForeignKey(
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
        default=ACTIVE,
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
    beneficiaries = models.ManyToManyField(
        Beneficiary,
        related_name="beneficiaries",
        verbose_name=_("Beneficiaries"),
        help_text=_("Beneficiaries of this policy"),
        blank=True,
    )

    def __str__(self) -> str:
        return f"#{self.policy_id} bought by User: {self.policy_holder.full_name}"

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

    class PriceFrequency(models.TextChoices):
        """
        Choices for the type of pricing model
        """

        MONTHLY = "Monthly", "Monthly"
        ANNUAL = "Annual", "Annual"
        QUARTERLY = "Quarterly", "Quarterly"

    class PriceType(models.TextChoices):
        """
        Choices for the type of pricing
        """

        FLAT = "Flat", "Flat Rate"
        FIXED = "Fixed", "Fixed Rate"
        VARIATE = "Dynamic", "Dynamic Rate"

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    commision = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    surcharges = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default="NGN", help_text="Currency code")
    pricing_model = models.CharField(
        max_length=20, choices=PriceType.choices, default=PriceType.FIXED
    )
    frequency = models.CharField(
        max_length=20, choices=PriceFrequency.choices, default=PriceFrequency.MONTHLY
    )

    def __str__(self):
        return (
            f"{self.amount} {self.currency} ({self.pricing_model} - {self.frequency})"
        )

    def compute_total_price(self):
        """
        Computes the total price for a product tier

        Takes into account the `base_preimum` of the product, and discount_amount
        """
        total_price = self.amount

        if self.discount_amount:
            total_price -= self.discount_amount
        return total_price


def default_expiry_date():
    return timezone.now() + timedelta(days=30)


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
        help_text="The expiry date of the quote.",
        default=default_expiry_date,
    )
    status = models.CharField(max_length=20, choices=QUOTE_STATUS, default="pending")
    additional_metadata = models.JSONField(
        null=True, blank=True, help_text="Additional information about the quote"
    )

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
