from api.core.mixins import TimestampMixin
from api.core.models import Address
from django.db import models
from django.utils.translation import gettext_lazy as _


class Provider(TimestampMixin, models.Model):
    """
    A provider is a company that provides insurance services to our clients (merchants)
    """

    business_name = models.CharField(
        _("Business Name"),
        max_length=255,
        null=False,
        blank=False,
        help_text=_("The name of the insurance provider"),
    )
    business_email = models.EmailField(
        _("Business Email"), unique=True, null=False, blank=False
    )
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    tax_identification_number = models.CharField(
        _("TIN"), max_length=40, null=True, blank=True
    )
    registration_number = models.CharField(
        _("Registration Number"), max_length=40, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Insurance Provider")
        verbose_name_plural = _("Insurance Providers")

        indexes = [
            models.Index(fields=["business_name", "business_email"]),
        ]
