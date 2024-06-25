from typing import Any, ClassVar, NewType  # noqa

from rest_framework import serializers

_Model = NewType("_Model", type)


class LimitedScopeSerializer(serializers.ModelSerializer):
    """
    Generic [Read-only] Serializer that only includes the specified fields

    Attributes:
        model_class: ClassVar[type[_Model]] | None
        fields: ClassVar[list[str]]
    """

    model_class: ClassVar[type[_Model]] | None = None
    fields: ClassVar[list[str]] = []

    def __init_subclass__(cls, **kwargs):
        if not cls.model_class:
            raise ValueError("model_class is required")
        if not cls.fields:
            raise ValueError("fields is required")

    def __new__(cls, *args: Any, **kwargs: Any) -> "LimitedScopeSerializer":
        kwargs["Meta"].fields = cls.fields
        return super().__new__(cls, *args, **kwargs)

    class Meta:
        model = cls.model_class
        fields = None
        read_only_fields = cls.fields
