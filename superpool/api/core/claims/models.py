import uuid

from core.catalog.models import Policy, Product
from core.providers.models import Provider
from core.user.models import Customer
from django.db import models
from django.utils.translation import gettext_lazy as _


class Claim(models.Model):
    """
    A request for compensation by a policyholder due to a covered loss.
    """

    CLAIM_STATUS = (
        (_("Accepted"), "accepted"),
        (_("Approved"), "approved"),
        (_("Pending"), "pending"),
        (_("Rejected"), "denied"),
        (_("Paid"), "paid"),
    )
    """ The current state of a claim (e.g., pending, accepted, approved, paid)."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_(
            "Unique ID used internally to reference and identify claim objects"
        ),
        serialize=False,
    )
    claim_number = models.CharField(
        _("Claim Number"),
        max_length=50,
        unique=True,
        help_text=_(
            "Claim Reference Number issued by insurer to identify and manage claim tracking process "
        ),
    )
    claim_date = models.DateField(
        auto_now=True,
        db_index=True,
        verbose_name=_("Date at which a claim is created"),
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=CLAIM_STATUS)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "claim"
        verbose_name_plural = "claims"
        indexes = [
            models.Index("created_at"),
            models.Index("claim_number"),
        ]

    @property
    def latest_status(self):
        """
        Provides latest information regarding a claim status
        """
        pass


class StatusTimeline(models.Model):
    """
    Represents a change in the status of a claim over time.

    Stores the new status and the timestamp when the change occurred.
    """

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=Claim.CLAIM_STATUS)
