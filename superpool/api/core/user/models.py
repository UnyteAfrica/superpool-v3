import uuid

from core.mixins import TimestampMixin
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(PermissionsMixin, TimestampMixin, AbstractBaseUser):
    """
    Represent a given user model
    """

    class USER_TYPES(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        ADMIN = "admin", _("Admin")
        SUPPORT = "support", _("Support")

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
    username = models.CharField(
        unique=True,
        blank=True,
        null=False,
        help_text="Designates the username of a given user",
    )
    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=USER_TYPES.choices,
        default=USER_TYPES.CUSTOMER,
        help_text="Designates the role of a given user on the platform",
    )

    email = models.EmailField(unique=True, blank=False, null=False)

    date_joined = models.DateTimeField(auto_now_add=True, help_text="Date user joined")
    last_active = models.DateTimeField(
        auto_now=True, help_text="Last time user was active"
    )
    is_active = models.BooleanField(
        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts"
        "This will prevent the user from logging in "
        "Also, a user is only active when he or he has completed verification",
        default=False,
    )
    is_staff = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["first_name", "last_name", "email"]
    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        ordering = ["first_name", "last_name", "date_joined"]
        indexes = [
            models.Index(fields=["first_name", "last_name", "date_joined"]),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    def has_completed_verification(self) -> bool:
        """
        Validates if the user has completed KYC verification
        """
        return False

    def has_read_terms(self) -> bool:
        """
        Check if user has read terms and conditions
        """
        return False


class UserProfile(models.Model):
    """
    Model to represent user profile
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["user", "date_of_birth"]
        indexes = [
            models.Index(fields=["user", "date_of_birth"]),
        ]
        constraints = [
            UniqueConstraint(fields=["user", "date_of_birth"], name="unique_user_dob"),
        ]
