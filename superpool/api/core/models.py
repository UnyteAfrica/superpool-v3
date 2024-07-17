# Utility models that does not fit into domain-specific parts of the application

from core.catalog.models import Product  # noqa: F401
from core.merchants.models import Merchant  # noqa: F401
from core.mixins import TimestampMixin, TrashableModelMixin
from core.providers.models import Provider as Partner  # noqa: F401
from core.user.models import User  # noqa: F401
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta


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

    coverage_name: models.CharField = models.CharField(
        _("Coverage Name"),
        max_length=100,
        help_text=_("Name of the coverage e.g collision, hospitalization, etc."),
    )
    coverage_id: models.CharField = models.CharField(
        _("Coverage ID"),
        max_length=100,
        help_text=_("unique identifier to track coverage details"),
    )
    coverage_limit: models.DecimalField = models.DecimalField(
        _("Coverage Limit"),
        max_digits=10,
        decimal_places=2,
        help_text=_(
            "This is the maximum amount that the insurance company will pay for a claim"
        ),
    )  # TODO: Add currency field here
    description: models.TextField = models.TextField(
        _("Description"), help_text=_("Description of the coverage")
    )
    product_id: models.ForeignKey = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="coverages",
        help_text=_("Product to which the coverage belongs"),
    )


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


class Application(models.Model):
    """
    An application is a sandbox environment needed for interacting with Unyte's APIs

    Merchants can only have ONE application instance
    """

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
    )
    # We are storing the application_id as a string because it is a UUID
    #
    # By storing it as string here, we move an expensive operation such as generating UUIDs
    # from the database to the application layer, which is more efficient
    application_id = models.CharField(max_length=100, primary_key=True, unique=True)
    api_key = models.OneToOneField(
        "core.APIKey", on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    test_mode = models.BooleanField(help_text="Whether the application is in test mode")

    def __str__(self) -> str:
        return f"{self.name} - {self.application_id}"

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = APIKey.objects.create(
                key=get_random_string(32), merchant=self.merchant
            )
        super().save(*args, **kwargs)


class APIKey(models.Model):
    """
    API Key
    """

    id = models.CharField(primary_key=True, unique=True, editable=False)
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    key = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"API Key for {self.merchant.name}"

    def _generate_id(self):
        from uuid import uuid

        prefix = "SUPERPOOL_"
        suffix = str(uuid.uuid4())
        return "".join(prefix, suffix)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self._generate_id()
        return super().save(*args, **kwargs)
