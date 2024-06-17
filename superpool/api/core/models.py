from api.core.mixins import TimestampMixin
from core.user.models import User  # noqa: F401
from django.db import models


class Operation:
    """
    Class to represent an operation
    """

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"<Operation: {self.name}>"


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


class Policy(TimestampMixin, models.Model):
    """
    Represent an insurance policy

    """

    class Status(models.TextChoices):
        ACTIVE = "Active"
        CANCELLED = "Cancelled"
        EXPIRED = "Expired"

    policy_id: models.AutoField = models.AutoField(primary_key=True)
    policy_name: models.CharField = models.CharField(
        _("Policy Name"), max_length=100, help_text="Name of the insurance policy"
    )
    policy_number = models.CharField(max_length=100)
    premium: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final premimum amount after adjustments",
    )

    @property
    def is_claimable(self) -> bool:
        """
        Check if the policy is claimable
        """
        return False

    def __str__(self) -> str:
        return f"Policy: {self.policy_name}"

    @property
    def is_renewable(self) -> bool:
        return False

    class Meta:
        db_table = "policy"
        verbose_name = "Policy"
        verbose_name_plural = "Policies"
