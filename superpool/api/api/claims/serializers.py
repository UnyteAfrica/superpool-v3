from core.catalog.models import Product
from core.claims.models import Claim, StatusTimeline
from core.providers.models import Provider
from core.user.models import Customer
from rest_framework import serializers


class ProviderSerializer(serializers.ModelSerializer):
    """Helps us to serialize the Insurer name from the Provider object"""

    class Meta:
        model = Provider
        fields = ["name"]


class ClaimOwnerSerializer(serializers.ModelSerializer):
    """Serializes the metadata about at claim owner"""

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "dob", "email", "phone_number"]


class ClaimProductSerializer(serializers.ModelSerializer):
    """Serilizes the metadata about the product category a claim belongs to"""

    class Meta:
        model = Product
        fields = [
            "name",
            "product_type",
        ]


class ClaimProviderSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer()

    class Meta:
        # We are using product here, so we can use the product to reference the insurer who offered this package
        model = Product
        fields = ["provider"]


class StatusTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusTimeline
        fields = ["status", "timestamp"]

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr["name"] = repr.pop("status")
        repr["time_stamp"] = repr.pop("timestamp").strftime(
            # This allows us to be able to convert the timestamp to: Month Day, Year Hour:Minute AM/PM
            "%b %d, %Y %I:%M %p"
        )
        return repr


class ClaimSerializer(serializers.ModelSerializer):
    """
    Serializer for Claim instances.

    This serializer includes fields that are intended to be visible when
    retrieving or listing Claim objects. It provides a human-readable
    representation of the Claim, including status descriptions.
    """

    product = ClaimProductSerializer()
    customer = ClaimOwnerSerializer()
    insurer = ClaimProviderSerializer()
    claim_amount = serializers.DecimalField(
        source="amount", max_digits=10, decimal_places=2
    )
    claim_reference_number = serializers.CharField(source="claim_number")
    claim_status = serializers.CharField(source="status")
    claim_status_timeline = StatusTimelineSerializer(many=True, read_only=True)

    class Meta:
        model = Claim
        fields = [
            "claim_reference_number",
            "claim_status",
            "claim_date",
            "customer",
            "claim_amount",
            "insurer",
            "product",
            "policy",
            "claim_status_timeline",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "claim_reference_number": {"required": False},
        }


class ClaimWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Claim objects.

    This serializer is used for creating and updating claim objects.
    It provides fields needed only for write-operations and excludes
    all forms of computed fields

    NOTE: It shuld be used in write-only operations
    """

    claim_reference_number = serializers.CharField(source="claim_number")
    customer = ClaimOwnerSerializer()
    claim_id = serializers.UUIDField(source="id")

    class Meta:
        model = Claim
        fields = [
            "claim_id",
            "claim_reference_number",
            "claim_status",
            "customer",
            # TODO: documents and other stuff should be used in this serializer and not in the read serializer
        ]
        extra_kwargs = {
            "claim_reference_number": {"read_only": True},
            "claim_id": {"read_only": True},
        }