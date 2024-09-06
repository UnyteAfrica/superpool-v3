from typing import Union
from decimal import Decimal

from api.serializers import LimitedScopeSerializer
from core.claims.models import Claim
from core.catalog.models import Policy
from core.merchants.models import Merchant
from core.user.models import Customer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class MerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for Merchant model
    """

    class Meta:
        model = Merchant
        fields = "__all__"


class MerchantSerializerV2(serializers.ModelSerializer):
    """
    Serializer for Merchant model
    """

    class Meta:
        model = Merchant
        exclude = ("id",)


class MerchantLimitedSerializer(LimitedScopeSerializer):
    """
    Serializer to display Merchant model with limited fields
    """

    model_class = Merchant
    fields = [
        "id",
        "name",
        "short_code",
        "business_email",
        "is_active",  # noqa: E231
        "support_email",
        "created_at",
    ]


class CreateMerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Merchant
    """

    class Meta:
        model = Merchant
        fields = (
            "name",
            "business_email",
            "support_email",
        )
        extra_kwargs = {
            "name": {"required": True},
            "business_email": {"required": True},
            "support_email": {"required": False},
        }

    def get_short_code(self, obj):
        return self.Meta.model.generate_short_code()


class MerchantWriteSerializerV2(serializers.ModelSerializer):
    """
    Handles the creation of new Merchants
    """

    company_name = serializers.CharField(source="name")

    class Meta:
        model = Merchant
        fields = ("company_name", "business_email", "support_email", "short_code")
        extra_kwargs = {
            "company_name": {"required": True},
            "business_email": {"required": True},
            "support_email": {"required": False},
            "short_code": {"read_only": True},
        }

    def validate_business_email(self, value: str) -> Union[str, ValidationError]:
        """
        Check that the business email is unique
        """
        if Merchant.objects.filter(business_email=value).exists():
            raise ValidationError("A merchant with this business email already exists.")
        return value


class CustomerInformationSerializer(serializers.ModelSerializer):
    """
    Formats the full information displayed about a merchant's customer
    """

    customer_id = serializers.PrimaryKeyRelatedField()
    full_name = serializers.CharField(source="full_name")
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
    claim_id = serializers.PrimaryKeyRelatedField(source="id")
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
