# Utility models that does not fit into domain-specific parts of the application

import hashlib
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from core.catalog.models import Product  # noqa: F401
from core.merchants.models import Merchant  # noqa: F401
from core.providers.models import Provider as Partner  # noqa: F401
from core.user.models import User  # noqa: F401


class Operation:
    """
    Class to represent an operation
    """

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"<Operation: {self.name}>"


class Coverage(models.Model):
    """
    Represents a structure to help track complex coverage information
    """

    class CoverageType(models.TextChoices):
        """
        Choices for different types of coverage
        """

        MEDICAL = "Medical", "Medical Coverage"
        COLLISION = "Collision", "Collision Coverage"
        LIABILITY = "Liability", "Liability Coverage"
        PROPERTY = "Property", "Property Coverage"
        TRAVEL = "Travel", "Travel Coverage"
        ACCIDENTAL = "Accidental", "Accidental Coverage"
        DAMAGES = "Damages", "Damages"
        OTHER = "Other", "Other Coverage"

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coverage_name: models.CharField = models.CharField(
        _("Coverage Name"),
        max_length=100,
        help_text=_("Name of the coverage e.g collision, hospitalization, etc."),
    )
    coverage_type = models.CharField(
        help_text=_("Internal recognized of coverages"),
        choices=CoverageType.choices,
        null=True,
        blank=True,
    )
    coverage_id: models.CharField = models.CharField(
        _("Coverage ID"),
        max_length=100,
        help_text=_("unique identifier to track coverage details"),
        primary_key=True,
    )
    coverage_limit: models.DecimalField = models.DecimalField(
        _("Coverage Limit"),
        max_digits=10,
        decimal_places=2,
        help_text=_(
            "This is the maximum amount that the insurance company will pay for a claim"
        ),
        null=True,
        blank=True,
    )
    currency = models.CharField(
        _("Currency"),
        max_length=10,
        default="NGN",
        help_text=_("Currency of the coverage limit, e.g., USD, EUR"),
    )
    description: models.TextField = models.TextField(
        _("Description"), help_text=_("Description of the coverage")
    )

    coverage_period_end = models.DateField(
        _("Coverage End Date"),
        help_text=_("End date of the coverage period"),
        null=True,
        blank=True,
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

    def __str__(self):
        return f"{self.coverage_name} - {self.coverage_id}"

    class Meta:
        verbose_name = _("Coverage")
        verbose_name_plural = _("Coverages")

    def generate_coverage_id(self):
        prefix = "COV_"
        return prefix + get_random_string(length=12)

    def save(self, *args, **kwargs):
        if not self.coverage_id:
            self.coverage_id = self.generate_coverage_id()
        super().save(*args, **kwargs)


class Address(models.Model):
    """
    Class to represent an address
    """

    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"<Address: {self.street}, {self.city}, {self.state}, {self.country}>"


class APIKey(models.Model):
    """
    API Key
    """

    id = models.UUIDField(
        unique=True, editable=False, primary_key=True, default=uuid.uuid4
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="api_keys",
        null=True,
    )
    key = models.CharField(
        max_length=150,
        unique=True,
        help_text=(
            "Unique key generated on the platform for use in subsequent request"
        ),
        blank=True,
    )
    key_hash = models.CharField(
        max_length=150,
        unique=True,
        help_text="Hashed value of the key shared with the merchant. Always use this and never use the actual `key` in requests.",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.display_key()} for {self.merchant.name}"

    def hash_key(self, value: str) -> str:
        """
        Hashes a given value using SHA-256.
        """
        return hashlib.sha256(value.encode()).hexdigest()

    def generate_key(self) -> str:
        """
        Generate a random key
        """
        return str(uuid.uuid4()).replace("-", "")

    def save(self, *args, **kwargs):
        # only generate the key and the hash key if it is a new object
        if not self.key:
            self.key = self.generate_key()
            self.key_hash = self.hash_key(self.key)

        # if the key is present but the hash key is not, hash the key
        elif self.key and not self.key_hash:
            self.key_hash = self.hash_key(self.key)

        super().save(*args, **kwargs)

    def display_key(self) -> str:
        if self.key:
            return self.key[:5] + "..." + self.key[-5:]
        return "No key"

    def display_key_hash(self) -> str:
        return str(self.key_hash)


class Application(models.Model):
    """
    An application is a sandbox environment or a production environment for interacting with Unyte's APIs
    """

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    application_id = models.CharField(
        max_length=100,
        primary_key=True,
        unique=True,
        default=str(uuid.uuid4()),
    )
    api_key = models.OneToOneField(
        APIKey,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="applications",
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    test_mode = models.BooleanField(
        help_text="True if the application is in test mode (sandbox), otherwise false for production.",
        default=True,
    )

    def __str__(self) -> str:
        return f"{self.name} ({'Sandbox' if self.test_mode else 'Production'}) - {self.merchant.name}"

    # def save(self, *args, **kwargs):
    #     # # Validate API keys
    #     if not self.pk:  # Only check for new instances
    #         existing_keys = APIKey.objects.filter(merchant=self.merchant).count()
    #         if existing_keys >= 2:
    #             raise ValidationError(
    #                 "A merchant can only have a maximum of 2 API keys."
    #             )
    #     # no api key, no probs -  generate new one
    #     if not self.api_key:
    #         self.api_key = APIKey.objects.create(merchant=self.merchant)
    #     super().save(*args, **kwargs)

    def generate_api_key(self):
        """
        Generates and assign new API key to the application
        """
        if not self.api_key:
            self.api_key = APIKey.objects.create(merchant=self.merchant)
            self.save(update_fields=["api_key"])

    @property
    def api_key_hash(self):
        return self.api_key.key_hash if self.api_key else None


class Environment(models.Model):
    """
    Represents a test or production environment for interacting with the APIs.

    This model is primarily used by merchants for managing different environments.

    This is an improved version of the `Application` model and as such,
    the `Application` model would be deprecated at some point.
    """

    client_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for the merchant client.",
        db_index=True,
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="environments",
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        help_text="A descriptive name for the environment.",
    )
    is_test_mode = models.BooleanField(
        default=True,
        help_text="Indicates if the environment is in test mode (sandbox) or production.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({'Test' if self.is_test_mode else 'Production'}) - {self.client_id}"


class APIKeyV2(models.Model):
    """
    API Key - Version 2

    - Stores hashed versions of API keys.
    - Supports revocation and rolling updates using flags.
    - Associates with a specific environment or client.
    """

    API_KEY_TYPES = (
        ("merchant", "Merchant"),
        ("internal", "Internal Backend"),
    )

    id = models.UUIDField(
        unique=True, editable=False, primary_key=True, default=uuid.uuid4, db_index=True
    )
    client_id = models.CharField(
        max_length=100,
        help_text="Unique identifier for the client or environment (merchant ID or internal client ID).",
        db_index=True,
        blank=True,
    )
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text="The environment associated with this API key.",
        null=True,
        blank=True,
    )
    key_hash = models.CharField(
        max_length=200,
        unique=True,
        help_text="SHA-256 hashed value of the API key. The raw key is never stored due to compliance and security reasons.",
    )
    api_key_type = models.CharField(
        max_length=20,
        choices=API_KEY_TYPES,
        help_text="Type of API key: 'merchant' for merchant integrations or 'internal' for backend use.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the key is active. Utilized for revoking access.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"APIKey for {self.environment.client_id} ({'Test' if self.environment.is_test_mode else 'Production'})"

    def compute_hash(self, value: str) -> str:
        """
        Hashes a given value using SHA-256.
        """
        return hashlib.sha256(value.encode()).hexdigest()

    def verify_key(self, hashed_key: str) -> bool:
        """
        Verifies that a provided API key matches the stored hash.
        """
        return self.key_hash == self.compute_hash(hashed_key)

    def generate_key(self, client_id: str, test_mode: bool) -> str:
        """
        Generates a API key based on client ID and environment type
        """
        prefix = "unytk"  # consider it a vanila flavor- hehehe! :) crack the gist, and win 10k
        env_label = "uk_test" if test_mode is True else "uk_live"

        client_id = client_id.replace("-", "_")
        base_key = f"{env_label}_{client_id}"
        keyhash = self.compute_hash(base_key)
        check_sum = hashlib.md5(keyhash.encode()).hexdigest()[:8]
        return f"{prefix}_{env_label}_{keyhash}_{check_sum}"

    def clean(self):
        if not self.client_id and not self.environment:
            raise ValidationError(
                "Either 'client_id' or 'environment' must be provided."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
