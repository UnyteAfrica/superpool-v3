from core.catalog.models import Product
from core.claims.models import Claim, StatusTimeline
from core.providers.models import Provider
from core.user.models import Customer
from rest_framework import serializers


class ClaimOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "dob", "email", "phone_number"]


class ClaimProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "name",
            "product_type",
        ]


class ClaimProviderSerializer(serializers.ModelSerializer):
    class Meta:
        # We are using product here, so we can use the product to reference the insurer who offered this package
        model = Product
        fields = ["provider__name"]


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
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }
