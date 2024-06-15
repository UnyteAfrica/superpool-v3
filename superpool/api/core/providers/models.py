import uuid

from django.db import models  # type: ignore
from django.utils.translation import gettext_lazy as _  # type: ignore
from django_stubs_ext.db.models import TypedModelMeta


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
    short_code: models.CharField = models.CharField(
        max_length=10,
        unique=True,
        help_text="This is used in the system to identify the provider. It should be unique, example includes: AXA-XXXX, "
        "HEIR-XXXX, UNYT-XXXX, LEAD-XXXX, etc.",
    )

    support_email: models.EmailField
    support_phone: models.CharField

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta(TypedModelMeta):
        verbose_name_plural = _("Providers")
