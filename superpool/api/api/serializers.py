from typing import Any, ClassVar, NewType  # noqa

from django.db.models import Model
from rest_framework import serializers
from core.providers.models import Provider
from core.merchants.models import Merchant
from django.contrib.auth import get_user_model

User = get_user_model()


class LimitedScopeSerializer(serializers.ModelSerializer):
    """
    Generic [Read-only] Serializer that only includes the specified fields

    Attributes:
        model_class: Model
        fields: list[str]
    """

    model_class: Model = None
    fields: list[str] = []

    def __init_subclass__(cls, **kwargs):
        if not cls.model_class:
            raise ValueError("model_class is required")
        if not cls.fields:
            raise ValueError("fields is required")

    def __new__(cls, *args: Any, **kwargs: Any) -> "LimitedScopeSerializer":
        # We also want to validate if the field specified actually exists in the model
        for field in cls.fields:
            if not hasattr(cls.model_class, field):
                raise ValueError(f"Field Error: Invalid Field, {field}")

        # Set the models and read_only_fields of the subclasses to the fields list
        kwargs["Meta"] = {
            "model": cls.model_class,
            "fields": cls.fields,
            "read_only_fields": cls.fields,
        }
        return super().__new__(cls, *args, **kwargs)


class ProviderSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(source="id")
    provider_name = serializers.CharField(source="name")

    class Meta:
        model = Provider
        fields = [
            "provider_id",
            "provider_name",
            "support_email",
        ]
        read_only_fields = fields


class SetPasswordSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    new_password = serializers.CharField()

    def validate(self, attrs):
        tenant_id = attrs.get("tenant_id")
        new_password = attrs.get("new_password")

        try:
            # retreive the merchant information from the User table
            merchant = Merchant.objects.get(tenant_id=tenant_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid user.")

        user = merchant.user

        # check if the user is a merchant
        if user.role != User.USER_TYPES.MERCHANT:
            raise serializers.ValidationError(
                "Only merchants can complete registration via this endpoint."
            )

        # security gurard against password
        if len(new_password) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )

        return attrs
