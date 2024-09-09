from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.catalog.models import Policy
from core.claims.models import Claim
from core.user.models import Customer
from decimal import Decimal


class CustomerInformationSerializer(serializers.ModelSerializer):
    """
    Formats the full information displayed about a merchant's customer
    """

    customer_id = serializers.PrimaryKeyRelatedField(source="id", read_only=True)
    full_name = serializers.SerializerMethodField()
    customer_email = serializers.EmailField(source="email")
    customer_phone = serializers.CharField(source="phone_number")
    date_of_birth = serializers.DateField(format="%Y-%m-%D", source="dob")
    purchased_policies = serializers.SerializerMethodField()
    active_policies = serializers.SerializerMethodField()
    active_claims = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "customer_id",
            "full_name",
            "customer_email",
            "customer_phone",
            "date_of_birth",
            "address",
            "purchased_policies",
            "active_policies",
            "active_claims",
        ]
        read_only_fields = fields

    def get_full_name(self, obj) -> str:
        return obj.full_name

    def get_active_claims(self, obj) -> dict:
        claims = obj.claims.filter(status="active")
        return CustomerClaimSerializer(claims, many=True).data

    def get_active_policies(self, obj) -> dict:
        active_policies = obj.policies.filter(status="active")
        return CustomerPolicySerializer(active_policies, many=True).data

    def get_purchase_policies(self, obj) -> dict:
        policies = obj.policies.all()
        return CustomerPolicySerializer(policies, many=True).data


class CustomerPolicySerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(source="effective_from", format="%Y-%m-%d")
    end_date = serializers.DateField(source="effective_through", format="%Y-%m-%d")
    policy_type = serializers.CharField(source="product.product_type")
    premium_amount = serializers.DecimalField(
        source="premium", max_digits=10, decimal_places=2
    )

    class Meta:
        model = Policy
        fields = [
            "policy_id",
            "policy_type",
            "status",
            "start_date",
            "end_date",
            "premium_amount",
        ]


class CustomerClaimSerializer(serializers.ModelSerializer):
    claim_id = serializers.PrimaryKeyRelatedField(source="id", read_only=True)
    policy_id = serializers.UUIDField(source="policy.policy_id")
    claim_status = serializers.CharField(source="status")
    claim_amount = serializers.DecimalField(
        source="amount", max_digits=10, decimal_places=2, min_value=Decimal(0.00)
    )
    date_filed = serializers.DateField(format="%Y-%m-%d", source="claim_date")
    date_resolved = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = Claim
        fields = [
            "claim_id",
            "policy_id",
            "claim_status",
            "claim_amount",
            "date_filed",
            "date_resolved",
        ]
        read_only_fields = fields


class CustomerSummarySerializer(serializers.ModelSerializer):
    """
    Basic information serializer about a customer

    Effective use-case: Listing of customers
    """

    customer_id = serializers.PrimaryKeyRelatedField(read_only=True)
    full_name = serializers.CharField()
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(source="phone_number")

    class Meta:
        model = Customer
        fields = ["customer_id", "full_name", "customer_email", "customer_phone"]
        read_only_fields = fields
