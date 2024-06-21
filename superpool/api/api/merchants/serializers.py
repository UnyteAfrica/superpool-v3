from api.serializers import LimitedScopeSerializer
from core.merchants.models import Merchant
from rest_framework import serializers
from rest_framework.serializers import Serializer


class MerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for Merchant model
    """

    class Meta:
        model = Merchant
        fields = "__all__"


class MerchantLimitedSerializer(LimitedScopeSerializer):
    """
    Serializer to display Merchant model with limited fields
    """

    model_class = Merchant
    fields = [
        "name",
        "short_code",
        "support_email",
    ]


class CreateMerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a Merchant
    """

    class Meta:
        model = Merchant
        fields = (
            "merchant_name",
            "short_code",
            "test_mode",
        )
