from typing import Union

from api.serializers import LimitedScopeSerializer
from core.merchants.models import Merchant
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
