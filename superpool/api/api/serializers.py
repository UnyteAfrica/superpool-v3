from typing import Any, ClassVar, NewType  # noqa

from django.db.models import Model
from rest_framework import serializers
from core.providers.models import Provider
from core.merchants.models import Merchant
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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


class CompleteRegistrationSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})

        return attrs

    def save(self):
        tenant_id = self.validated_data["tenant_id"]
        password = self.validated_data["password"]

        # Find the merchant and set the user password
        merchant = Merchant.objects.filter(tenant_id=tenant_id).first()
        user = User.objects.create(
            email=merchant.business_email, role=User.USER_TYPES.MERCHANT
        )
        user.set_password(password)
        user.save()

        return user
