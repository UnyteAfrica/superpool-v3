import uuid

from core.catalog.models import Policy, Product
from core.mixins import TimestampMixin, TrashableModelMixin
from core.providers.models import Provider
from core.user.models import Customer
from django.db import models
from django.utils.translation import gettext_lazy as _


class Claim(TimestampMixin, models.Model):
    """
    A request for compensation by a policyholder due to a covered loss.
    """

    CLAIM_STATUS = (
        ("accepted", _("Accepted")),
        ("approved", _("Approved")),
        ("pending", _("Pending")),
        ("denied", _("Rejected")),
        ("paid", _("Paid")),
        ("offer_sent", _("Offer sent")),
        ("offer_accepted", _("Offer accepted")),
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
    incident_date = models.DateField(verbose_name=_("Date of Incident"), null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    payout_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=CLAIM_STATUS, default="pending")
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    notes = models.TextField(null=True, blank=True)
    documents = models.ManyToManyField(
        "ClaimDocument",
        related_name="claims",
        verbose_name=_("Documents"),
        help_text=_("Documents uploaded by the policyholder as part of the claim"),
        blank=True,
    )

    class Meta:
        verbose_name = "claim"
        verbose_name_plural = "claims"
        ordering = ["-claim_date", "-created_at"]
        indexes = [
            # For performance reasons, we want to index the timestamps and claims number
            # as they would be used during audit processes
            models.Index(fields=["created_at"], name="created_at_idx"),
            models.Index(fields=["claim_number"], name="claim_number_idx"),
            models.Index(
                fields=["id"], name="claim_id_idx"
            ),  # pronounced claim id index
        ]

    def __str__(self) -> str:
        return f"Claim #{self.id} - {self.get_status_display()}"

    @property
    def latest_status(self):
        """
        Provides latest information regarding a claim status
        """
        # retrieves a set from the StatusTimeline class, ordering by latest timestamp
        return self.statustimeline_set.order_by("-timestamp").first()


class StatusTimeline(models.Model):
    """
    Represents a change in the status of a claim over time.

    Stores the new status and the timestamp when the change occurred.
    """

    claim = models.ForeignKey(
        Claim, on_delete=models.CASCADE, related_name="claim_status_timeline"
    )
    status = models.CharField(max_length=30, choices=Claim.CLAIM_STATUS)
    timestamp = models.DateTimeField(auto_now_add=True)


class ClaimDocument(models.Model):
    """
    Represents a document uploaded by a policyholder as part of a claim.
    """

    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    PICTURE = "picture"

    EVIDENCE_TYPE_CHOICES = [
        (VIDEO, _("Video")),
        (AUDIO, _("Audio")),
        (DOCUMENT, _("Document")),
        (PICTURE, _("Picture")),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    claim = models.ForeignKey(
        "Claim",
        related_name="claim_documents",
        on_delete=models.CASCADE,
        verbose_name=_("Related Claim"),
    )
    evidence_type = models.CharField(
        choices=EVIDENCE_TYPE_CHOICES,
        max_length=10,
        verbose_name=_("Evidence Type"),
        help_text=_("Type of evidence uploaded."),
    )
    document_name = models.CharField(
        max_length=255,
        verbose_name=_("Document Name"),
        help_text=_("Name of the document uploaded."),
    )
    document_url = models.URLField(
        max_length=1024,
        verbose_name=_("File Reference"),
        help_text=_(
            "Reference to the stored document (e.g., Google Cloud Storage blob name)."
        ),
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Claim Document")
        verbose_name_plural = _("Claim Documents")
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.document_name} for claim #{self.claim.claim_number} if {self.claim.claim_number} else {self.claim.id}"

    @property
    def download_url(self):
        """
        Returns a URL to download the document.
        """
        # TODO: Implement this!
        # should return the actual URL (public endpoint from gcp bucket to download the document)
        # e.g f"https://example.com/download/{self.blob}"
        pass

    @property
    def preview_url(self):
        """
        Returns a URL to preview the document.
        """
        # TODO: Implement this!
        # should be replaced with the actual URL
        # and be in the form of f"https://example.com/preview/{self.blob}"
        pass
