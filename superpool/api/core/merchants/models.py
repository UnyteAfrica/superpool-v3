from django.db import models
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta


class Merchant(models.Model):
    """
    A merchant is a client or an entrity that embed our services into their platform.

    At this moment, we are only providing insurance services to businesses (organizations; banks, schools, online marts, etc)
    """

    business_name = models.CharField(
        max_length=255,
        verbose_name=_("Business Name"),
        help_text=_("The name of the business"),
    )
    internal_id = models.CharField(
        _("Internal ID"),
        max_length=40,
        help_text=_(
            "Unique short code indentifier used internally to identify a merchant or distributor"
            "e.g. UBA-X224, GTB-3X2, KON-001, SLOT-001, WEMA-2286, etc."
        ),
        unique=True,
    )
    support_email = models.EmailField(
        _("Business Email"), help_text=_("The contact email address of the business")
    )
    tax_identification_number = models.CharField(
        _("TIN"), unique=True, max_length=40, null=True, blank=True
    )
    registration_number = models.CharField(
        _("Registration Number"), max_length=40, null=True, blank=True, unique=True
    )

    class Meta(TypedModelMeta):
        verbose_name = _("Merchant")
        verbose_name_plural = _("Merchants")

    def __str__(self):
        return f"Merchant: {self.business_name}"
