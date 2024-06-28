from uuid import uuid4

from core.mixins import TimestampMixin, TrashableModelMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_stubs_ext.db.models import TypedModelMeta


class Merchant(TrashableModelMixin, TimestampMixin, models.Model):
    """
    A merchant is a client or an entrity that embed our services into their platform.

    At this moment, we are only providing insurance services to businesses (organizations; banks, schools, online marts, etc)
    """

    id = models.UUIDField(
        _("Merchant ID"), primary_key=True, unique=True, default=uuid4
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Business Name"),
        help_text=_("The name of the business"),
    )
    short_code = models.CharField(
        _("Merchant Short code"),
        max_length=10,
        help_text=_(
            "Unique short code indentifier used internally to identify a merchant or distributor"
            "e.g. UBA-X224, GTB-3X2, KON-001, SLOT-001, WEMA-2286, etc."
        ),
        unique=True,
        null=True,
    )
    business_email = models.EmailField(
        _("Business Email"),
        help_text=_("Company registration email address"),
        blank=True,
    )
    support_email = models.EmailField(
        _("Support Email"),
        null=True,
        blank=True,
        help_text=_("The contact email address of the business, for support if any"),
    )
    is_active = models.BooleanField(
        default=False, help_text="Designates if the merchant is active"
    )
    tax_identification_number = models.CharField(
        _("TIN"),
        unique=True,
        max_length=40,
        null=True,
        blank=True,
        help_text="Unique tax identification number issued by federal or inland revenue service",
    )
    registration_number = models.CharField(
        _("Registration Number"),
        max_length=40,
        null=True,
        blank=True,
        unique=True,
        help_text="Government-issued registration number with the CAC",
    )
    address = models.TextField(
        _("Business Address"),
        help_text=_("The physical address of the business"),
        null=True,
        blank=True,
    )
    api_key = models.CharField(
        _("API Key"),
        max_length=80,
        help_text="Unique key generated on the platform for use in subsequent request",
        null=True,
    )
    kyc_verified = models.BooleanField(
        _("KYC Verified"),
        default=False,
        help_text="Designates if the business has been verified by the platform",
        blank=True,
    )

    class Meta(TypedModelMeta):
        verbose_name = _("Merchant")
        verbose_name_plural = _("Merchants")

    def save(self, *args: dict, **kwargs: dict) -> None:
        if not self.short_code:
            self.short_code = self.generate_shortcode()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Merchant: {self.name}"

    def delete(self, *args, **kwargs) -> None:
        """
        Trash the merchant instance
        """
        super(TrashableModelMixin).delete()

    @property
    def has_completed_kyc(self) -> bool:
        """
        Check if the merchant has completed KYC
        """
        return self.kyc_verified

    def generate_shortcode(self) -> str:
        """
        Generate a unique short code for the merchant

        The short code is a combination of the first three characters of the merchant name and a random 4 character string

        e.g
            Merchant: UBA
            Short code: UBA-3X24

            Merchant: GTB
            Short code: GTB-2X3F
        """
        return f"{self.name[:3].upper()}-{uuid4().hex[:4].upper()}"
