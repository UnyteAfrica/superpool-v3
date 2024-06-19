from core.mixins import TimestampMixin
from core.models import Address
from django.db import models
from django.utils.translation import gettext_lazy as _


class Merchant(TimestampMixin, models.Model):
    """
    A merchant is a client that uses our services

    At this moment, we are only providing insurance services to businesses (organizations; banks, schools, online marts, etc)
    """

    name = models.CharField(
        _("Name"),
        max_length=255,
        null=False,
        blank=False,
        help_text=_("The name of the merchant"),
    )
    business_email = models.EmailField(_("Email"), unique=True, null=False, blank=False)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    tax_identification_number = models.CharField(
        _("TIN"), max_length=40, null=True, blank=True
    )
    registration_number = models.CharField(
        _("Registration Number"), max_length=40, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Merchant")
        verbose_name_plural = _("Merchants")

        indexes = [
            models.Index(fields=["name", "business_email"]),
        ]

    def __str__(self):
        return self.name
