import uuid

from core.mixins import TimestampMixin
from django.db import models  # type: ignore
from django.utils.translation import gettext_lazy as _  # type: ignore
from django_stubs_ext.db.models import TypedModelMeta
from django.apps import apps


class Provider(models.Model):
    """
    Business or company that provide insurance coverage for our clients

    """

    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the provider",
    )
    name: models.CharField = models.CharField(
        max_length=80,
        unique=True,
        help_text="Name of the Insurance Provider. This could be a short form of the company name",
    )

    support_email: models.EmailField = models.EmailField(
        _("Business email"),
        help_text="Email address is used to track their support team during integrations",
        blank=True,
        null=True,
    )
    support_phone: models.CharField = models.CharField(
        help_text="Phone number of the insurance provider's support team",
        max_length=20,
        blank=True,
        null=True,
    )

    products = models.ManyToManyField(
        "catalog.Product",  # noqa: F405
        related_name="providers",
        blank=True,
        help_text="Products offered by the provider",
    )

    def __str__(self) -> str:
        return f"{self.name}"

    def get_products(self):
        """
        Method to get related products using apps.get_model.
        """
        Product = apps.get_model("catalog", "Product")
        return self.products.all()

    class Meta(TypedModelMeta):
        verbose_name = _("Insurer")
        verbose_name_plural = _("Insurers")
