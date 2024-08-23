from typing import Any, ClassVar, NewType  # noqa

from django.db.models import Model
from rest_framework import serializers
from core.providers.models import Provider


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
