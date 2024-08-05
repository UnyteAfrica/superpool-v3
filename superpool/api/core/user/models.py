import uuid

from core.mixins import TimestampMixin
from django.contrib.auth.models import AbstractBaseUser, AbstractUser, PermissionsMixin
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _
from typing_extensions import deprecated

from .managers import UserManager


class User(AbstractUser, TimestampMixin):
    """
    Represent a given user model
    """

    class USER_TYPES(models.TextChoices):
        # TODO: Remove the customer model in the next release
        # CUSTOMER = "customer", _("Customer")
        ADMIN = "admin", _("Admin")
        MERCHANT = "merchant", _("Merchant")
        SUPPORT = "support", _("Customer Support")

    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        help_text="ID of the user",
    )
    first_name = models.CharField(
        _("First Name"),
        help_text="Given name as it appears on ID",
        max_length=40,
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        _("Last Name"),
        help_text="Family name as it appears on ID",
        max_length=40,
        null=True,
        blank=True,
    )
    username = models.CharField(
        unique=True,
        blank=True,
        null=True,
        help_text="Designates the username of a given user",
    )
    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=USER_TYPES.choices,
        default=USER_TYPES.ADMIN,
        help_text="Designates the role of a given user on the platform",
    )
    # merchant = models.ForeignKey(
    #     "Merchant", null=True, blank=True, on_delete=models.SET_NULL
    # )

    email = models.EmailField(unique=True)
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["first_name", "last_name", "last_login", "date_joined"]
        indexes = [
            models.Index(fields=["first_name", "last_name"]),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Customer(TimestampMixin, models.Model):
    """
    V2: Customer

    Model to represent a customer
    """

    from core.merchants.models import Merchant

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(
        _("First Name"),
        help_text="Given name as it appears on ID",
        max_length=40,
    )
    middle_name = models.CharField(
        _("middle name"),
        max_length=40,
        blank=True,
        null=True,
        help_text="Middle name as it appears on User's ID ",
    )
    last_name = models.CharField(
        _("Last Name"),
        help_text="Family name as it appears on ID",
        max_length=40,
    )
    email = models.EmailField(unique=True, blank=False, null=False, help_text="Email")
    address = models.TextField(
        _("Address"), help_text="Physical address of the customer"
    )
    kyc_verified = models.BooleanField(
        default=False, help_text="Designates if the customer has completed KYC"
    )
    dob = models.DateField(
        _("Date of Birth"), help_text="Date of birth of the customer", null=True
    )
    phone_number = models.CharField(
        _("Phone Number"), help_text="Phone number of the customer", max_length=20
    )
    gender = models.CharField(
        _("Gender"),
        help_text="Gender of the customer, identified as: M for Male, F for Female",
        max_length=1,
        null=True,
    )
    verification_type = models.CharField(
        _("Verification Type"),
        help_text="Type of verification document",
        max_length=20,
        null=True,
    )
    verification_id = models.CharField(
        _("Verification ID"),
        help_text="ID of the verification document",
        max_length=20,
        null=True,
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="customers",
        null=True,
        blank=True,
        help_text="Merchant that created the customer",
    )

    def has_completed_verification(self) -> bool:
        """
        Validates if the user has completed KYC verification
        """
        return self.kyc_verified

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name", "last_name"]
        indexes = [
            models.Index(fields=["first_name", "last_name", "email"]),
        ]
