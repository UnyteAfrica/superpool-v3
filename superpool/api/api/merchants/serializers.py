from api.serializers import LimitedScopeSerializer
from core.merchants.models import Merchant
from rest_framework import serializers


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
