# Utility models that does not fit into domain-specific parts of the application

from decimal import Decimal
import hashlib
import uuid

from django.apps import apps
from core.catalog.models import Product  # noqa: F401
from core.merchants.models import Merchant  # noqa: F401
from core.mixins import TimestampMixin, TrashableModelMixin
from core.providers.models import Provider as Partner  # noqa: F401
from core.user.models import User  # noqa: F401
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta
from django.core.exceptions import ValidationError


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

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coverage_name: models.CharField = models.CharField(
        _("Coverage Name"),
        max_length=100,
        help_text=_("Name of the coverage e.g collision, hospitalization, etc."),
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
    )  # TODO: Add currency field here
    description: models.TextField = models.TextField(
        _("Description"), help_text=_("Description of the coverage")
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="coverages",
        help_text=_("Product to which the coverage belongs"),
    )

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
        return f"#{self.display_key} for {self.merchant.name}"

    def __hash__(self, value):
        return hashlib.sha256(value.encode()).hexdigest()

    def generate_key(self) -> str:
        """
        Generate a random key
        """
        return str(uuid.uuid4()).replace("-", "")

    def save(self, *args, **kwargs):
        # only generate the key and the hash key if it is a new object
        if not self.pk:
            self.key = self.generate_key()
            self.__hash__(self.key)

        # if the key is present but the hash key is not, hash the key
        elif self.key and not self.key_hash:
            self.__hash__(self.key)
        super().save(*args, **kwargs)

    def display_key(self) -> str:
        return self.key[:5] + "..." + self.key[-5:]

    def display_key_hash(self) -> str:
        return str(self.key_hash)


class Application(models.Model):
    """
    An application is a sandbox environment needed for interacting with Unyte's APIs
    """

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
    )
    application_id = models.CharField(
        max_length=100,
        primary_key=True,
        unique=True,
    )
    api_key = models.OneToOneField(
        APIKey,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="applications",
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    test_mode = models.BooleanField(help_text="Whether the application is in test mode")

    def __str__(self) -> str:
        return f"Environment: {self.name} by {self.merchant.name}"

    def save(self, *args, **kwargs):
        # Validate API keys
        if not self.pk:  # Only check for new instances
            existing_keys = APIKey.objects.filter(merchant=self.merchant).count()
            if existing_keys >= 2:
                raise ValidationError(
                    "A merchant can only have a maximum of 2 API keys."
                )
            # no api key, no probs -  generate new one
            if not self.api_key:
                self.api_key = APIKey.objects.create(merchant=self.merchant)
        super().save(*args, **kwargs)

    @property
    def api_key_hash(self):
        return self.api_key.key_hash if self.api_key else None
