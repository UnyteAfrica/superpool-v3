import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.merchants.models import Merchant
from core.mixins import TimestampMixin, TrashableModelMixin
from core.providers.models import Provider as Partner
from core.user.models import Customer
from core.utils import generate_id


class ProductTier(models.Model):
    """
    Represents the tier of a insurance product

    A product tier defines different levels of insurance products (e.g., Basic, Premium)
    and can offer varying coverages, pricing, exclusions, and benefits.
    """

    class TierType(models.TextChoices):
        """
        Types of insurance tiers for a product.

        These represent the different levels of the insurance package, e.g.,
        Basic, Premium, Silver, Bronze, etc.
        """

        BASIC = "Basic", "Basic Insurance"
        ADVANCED = "Advanced", "Advanced"
        STANDARD = "Standard", "Standard Insurance"
        PREMIUM = "Premium", "Premium"
        BRONZE = "Bronze", "Bronze"
        SILVER = "Silver", "Silver"
        COMPREHENSIVE = "Comprehensive", "Comprehensive"
        THIRDPARTY = "ThirdParty", "ThirdParty"
        OTHER = "Other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        help_text="Insurance package the tier belongs to",
        related_name="tiers",
        related_query_name="tier",
        db_index=True,
    )
    tier_name = models.CharField(
        max_length=255,
        help_text="Name of the product tier",
    )
    tier_type = models.CharField(
        max_length=255,
        choices=TierType.choices,
        blank=True,
        null=True,
        help_text="Type of tier. Choose from predefined options such as Basic, Premium, Silver, Corporate, Comprehensive, etc. An optional classification that further categorizes the tier",
    )
    description = models.TextField(
        help_text="Optional description of what the tier offers, such as specific benefits or target audience",
        null=True,
        blank=True,
    )
    base_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The base premium price for this tier before any adjustments or discounts",
    )
    pricing = models.ForeignKey(
        "Price",
        on_delete=models.SET_NULL,
        help_text="Pricing details for this tier, including surcharges or discounts",
        null=True,
        blank=True,
    )
    coverages = models.ManyToManyField(
        "core.Coverage",
        blank=True,
        help_text="Detailed breakdown of coverages provided in this tier. Example: Health, Accident, etc.",
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
        unique_together = ("product", "tier_name")


class Product(TimestampMixin, TrashableModelMixin, models.Model):
    """
    Packages offered by an insurance partner

    E.g Life Insurance, MicroInsurance, General Insurance, etc

    Can exist with or without associated tiers
    """

    class ProductType(models.TextChoices):
        """
        Choices for the type of insurance package
        """

        LIFE = "Life", "Life Insurance"
        HEALTH = "Health", "Health Insurance"
        AUTO = "Auto", "Auto Insurance"
        CARGO = "Cargo", "Cargo (Shipment) Insurance"
        GADGET = "Gadget", "Gadget Insurance"
        TRAVEL = "Travel", "Travel Insurance"
        HOME = "Home", "Home Insurance"
        STUDENT_PROTECTION = "Student_Protection", "Student Protection"
        ACCIDENT = "Accident", "Accident Insurance"
        PERSONAL_ACCIDENT = "Personal_Accident", "Personal Accident Insurance"
        CREDIT_LIFE = "CreditLife", "Credit Life Insurance"
        PET_INSURANCE = "PetCare", "PetCare Insurance"
        GENERAL = "General", "General Insurance"
        OTHER = "Other", "Other"

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
        db_index=True,
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
    base_premium = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base premium price if no tiers are defined",
        default=Decimal("0.00"),
    )
    is_live = models.BooleanField(
        default=True, help_text="Indicates if the package is live"
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.provider.name}"

    def delete(self, *args: dict, **kwargs: dict) -> None:
        """
        Override the delete method to trash the model instance
        """
        self.trash()

    def full_delete(self) -> None:
        return super().full_delete()

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

    class Meta:
        unique_together = ("amount", "description")

    def __str__(self):
        return (
            f"{self.amount} {self.currency} - {self.description} - {self.pricing_model}"
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

    class QuoteStatus(models.TextChoices):
        """
        Choices for the status of a quote
        """

        PENDING = "pending", "Pending"
        ACCEPTED = (
            "accepted",
            "Accepted",
        )  # could also mean, "Paid or user has used the quote"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    # id = models.CharField(max_length=80, primary_key=True, unique=True, editable=False)
    origin = models.CharField(
        max_length=255,
        help_text="The origin of the quote, e.g., Internal, or External provider",
        choices=[("Internal", "Internal"), ("External", "External")],
        default="Internal",
    )
    provider = models.CharField(
        max_length=255,
        help_text="The provider of the quote, e.g., AXA, Leadway, etc",
        null=True,
        blank=True,
    )
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
    status = models.CharField(
        max_length=20, choices=QuoteStatus.choices, default=QuoteStatus.PENDING
    )
    additional_metadata = models.JSONField(
        null=True, blank=True, help_text="Additional information about the quote"
    )
    purchase_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Unique identifier provided to payment processors to identify a quote purchase",
    )
    purchase_id_created_at = models.DateTimeField(null=True, blank=True)
    policy_terms = models.JSONField(
        help_text="Terms and conditions of the insurance policy, stored as a JSON object.",
        default=dict,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.quote_code} - {self.origin} - ({self.provider})"

    class Meta:
        verbose_name = "quote"
        verbose_name_plural = "quotes"

    def truncate_quote_code(self) -> str:
        """
        Truncate the quote code by removing underscores
        and cutting off the first three characters.

        Technically, 'Quo'_this_that_me_you

        into, 'thisthatmeyou'
        """
        return self.quote_code[3:].replace("_", "")

    def generate_purchase_id(self) -> str:
        """
        Generate a unique time-based purchase ID for this quote
        This ID is valid for 45 minutes from the time it's generated.
        """
        now = timezone.now()
        truncated_quote_code = self.truncate_quote_code()
        purchase_id = f"purchase_{truncated_quote_code}_{now.strftime('%Y%m%d%H%M%S')}"

        # store our new purchase quote that would be provided to external payment processors
        self.purchase_id = purchase_id
        self.purchase_id_created_at = now
        self.save()
        return purchase_id

    def purchase_id_isvalid(self) -> bool:
        """
        Check if the purchase ID is still valid (i.e., not older than 45 minutes).
        """
        if self.purchase_id_created_at:
            return timezone.now() <= self.purchase_id_created_at + timedelta(minutes=45)
        # if we don't have a creation time, the ID is therefore invalid
        return False

    def regenerate_purchase_id(self):
        """
        Regenerate the purchase ID if it's no longer valid.
        """
        if not self.purchase_id_isvalid():
            return self.generate_purchase_id()
        return self.purchase_id

    def save(self, *args, **kwargs):
        if not self.quote_code:
            quote_code = generate_id(self.__class__)
            self.quote_code = quote_code
        # Set quote expiry by default to 1 Month
        if not self.expires_in:
            self.expires_in = datetime.now() + timedelta(days=30)
        return super().save(*args, **kwargs)
